"""An email inbox (Gmail) in the hub, through IMAP and SMTP with an app password.

Google's Gmail API scopes are "restricted" (a paid security assessment before
other people can use them), so the mailbox signs in the classic way: the
address plus a 16-letter app password (Google Account → Security → 2-Step
Verification → App passwords). Reading never marks mail as read; replies go
out through Gmail's SMTP, so they also land in the mailbox's Sent folder.

Only Gmail's Primary tab is pulled in, so promotions and social mail stay out.
"""
import email
import email.policy
import html
import imaplib
import re
import smtplib
import ssl
from email.message import EmailMessage
from email.utils import formatdate, make_msgid, parseaddr, parsedate_to_datetime

from .base import AccountCandidate, Adapter, AdapterError, AuthError, Capabilities, FetchedItem, NotSupported

IMAP_HOST, IMAP_PORT = 'imap.gmail.com', 993
SMTP_HOST, SMTP_PORT = 'smtp.gmail.com', 465
FIRST_SYNC_DAYS = 7       # how far back the first sync looks
MAX_PER_SYNC = 50
MAX_BODY = 20000
TIMEOUT = 30

# Senders nobody can reply to (security alerts, receipts, bounces).
AUTOMATED_SENDER = re.compile(r'^(no-?reply|do-?not-?reply|donotreply|mailer-daemon|postmaster|bounces?)([+._-].*)?@')

SIGN_IN_HELP = ('Gmail refused the sign-in. Use the full address and an app password (16 letters from '
                'Google Account → Security → 2-Step Verification → App passwords), not the normal password.')


def _one_line(value):
    return re.sub(r'[\r\n]+', ' ', str(value or '')).strip()


def _body(msg):
    """Plain text of a message: the text part, else the HTML part with tags removed."""
    part = msg.get_body(preferencelist=('plain', 'html'))
    if part is None:
        return ''
    try:
        text = part.get_content()
    except (LookupError, ValueError):
        text = (part.get_payload(decode=True) or b'').decode('utf-8', 'replace')
    if part.get_content_type() == 'text/html':
        text = re.sub(r'(?is)<(script|style).*?</\1>', ' ', text)
        text = re.sub(r'(?i)<br\s*/?>|</p>|</div>', '\n', text)
        text = html.unescape(re.sub(r'<[^>]+>', ' ', text))
    text = re.sub(r'[ \t]+', ' ', text)
    return re.sub(r'\n\s*\n\s*\n+', '\n\n', text).strip()[:MAX_BODY]


def is_automated(address, msg=None):
    """Machine-sent mail: a no-reply sender, or an Auto-Submitted header (RFC 3834)."""
    if AUTOMATED_SENDER.match(address or ''):
        return True
    auto = str((msg or {}).get('Auto-Submitted', '') or '').strip().lower()
    return bool(auto) and auto != 'no'


class GmailAdapter(Adapter):
    platform = 'email'
    label = 'Email'
    caps = Capabilities(max_chars=MAX_BODY, images=False, video=False, max_media=0, link=False,
                        inbox=('email',), insights=False)
    connect_mode = 'manual'
    required_settings = ()
    manual_fields = [
        ('address', 'Gmail address', 'For example ralfiztechnologies@gmail.com.'),
        ('app_password', 'App password',
         'Not the normal password: a 16-letter app password from Google Account → Security → '
         '2-Step Verification → App passwords. 2-Step Verification must be on.'),
    ]

    # ------------------------------------------------------------ connection

    def _imap(self, address, password):
        try:
            box = imaplib.IMAP4_SSL(IMAP_HOST, IMAP_PORT, ssl_context=ssl.create_default_context(),
                                    timeout=TIMEOUT)
        except OSError as exc:
            raise AdapterError(f'Could not reach Gmail: {exc}', retryable=True)
        try:
            box.login(address, password)
        except imaplib.IMAP4.error:
            raise AuthError(SIGN_IN_HELP)
        return box

    def manual_connect(self, data):
        address = (data.get('address') or '').strip().lower()
        password = re.sub(r'\s+', '', data.get('app_password') or '')   # Google shows it in groups of 4
        if '@' not in address or not password:
            raise AdapterError('Fill in the Gmail address and the app password.')
        box = self._imap(address, password)
        try:
            box.logout()
        except (imaplib.IMAP4.error, OSError):
            pass
        return [AccountCandidate(external_id=address, name=address, handle=address, token=password)]

    # ------------------------------------------------------------ inbox

    def fetch_inbox(self, account, since=None):
        box = self._imap(account.external_id, account.token)
        try:
            typ, _ = box.select('INBOX', readonly=True)    # read-only: nothing gets marked as read
            if typ != 'OK':
                raise AdapterError('Could not open the Gmail inbox.')
            validity = (box.response('UIDVALIDITY')[1] or [b''])[0]
            validity = validity.decode() if isinstance(validity, bytes) else str(validity or '')
            last = int(account.extra.get('last_uid') or 0) if account.extra.get('uidvalidity') == validity else 0
            query = 'category:primary' if last else f'category:primary newer_than:{FIRST_SYNC_DAYS}d'
            args = ('X-GM-RAW', f'"{query}"') + (('UID', f'{last + 1}:*') if last else ())
            typ, data = box.uid('SEARCH', *args)
            uids = sorted(int(u) for u in (data[0] or b'').split() if int(u) > last)[-MAX_PER_SYNC:]
            items = []
            for uid in uids:
                typ, parts = box.uid('FETCH', str(uid), '(BODY.PEEK[])')
                raw = next((p[1] for p in parts or [] if isinstance(p, tuple)), None)
                if raw:
                    item = self._item(account, uid, email.message_from_bytes(raw, policy=email.policy.default))
                    if item:
                        items.append(item)
            if uids or account.extra.get('uidvalidity') != validity:
                account.extra = {**account.extra, 'last_uid': max(uids + [last]), 'uidvalidity': validity}
                account.save(update_fields=['extra'])
            return items
        except imaplib.IMAP4.error as exc:
            raise AdapterError(f'Gmail error: {exc}', retryable=True)
        finally:
            try:
                box.logout()
            except (imaplib.IMAP4.error, OSError):
                pass

    def _item(self, account, uid, msg):
        name, address = parseaddr(str(msg.get('From', '')))
        address = address.strip().lower()
        if not address or address == account.external_id:     # skip mail we sent ourselves
            return None
        if is_automated(address, msg):
            return None
        subject = _one_line(msg.get('Subject', '')) or '(no subject)'
        message_id = _one_line(msg.get('Message-ID', ''))
        references = _one_line(msg.get('References', ''))
        try:
            received = parsedate_to_datetime(str(msg.get('Date', ''))) if msg.get('Date') else None
        except (TypeError, ValueError):
            received = None
        return FetchedItem(
            kind='email', external_id=message_id or f'uid:{uid}', text=f'{subject}\n\n{_body(msg)}'.strip(),
            author_name=_one_line(name) or address, author_id=address,
            thread_id=(references.split() or [message_id])[0], received_at=received,
            raw={'subject': subject, 'message_id': message_id, 'references': references, 'uid': uid})

    def reply(self, account, item, text):
        to = (item.author_id or '').strip()
        if '@' not in to or re.search(r'\s', to):
            raise AdapterError('This email has no address to reply to.')
        raw = item.raw or {}
        subject = _one_line(raw.get('subject')) or 'your message'
        msg = EmailMessage()
        msg['From'] = account.external_id
        msg['To'] = to
        msg['Subject'] = subject if subject.lower().startswith('re:') else f'Re: {subject}'
        if raw.get('message_id'):
            msg['In-Reply-To'] = raw['message_id']
            msg['References'] = f"{raw.get('references', '')} {raw['message_id']}".strip()
        msg['Message-ID'] = make_msgid(domain=account.external_id.split('@')[-1])
        msg['Date'] = formatdate(localtime=True)
        msg.set_content(text)
        try:
            with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, context=ssl.create_default_context(),
                                  timeout=TIMEOUT) as smtp:
                smtp.login(account.external_id, account.token)
                smtp.send_message(msg)
        except smtplib.SMTPAuthenticationError:
            raise AuthError(SIGN_IN_HELP)
        except (smtplib.SMTPException, OSError) as exc:
            raise AdapterError(f'Gmail could not send the reply: {exc}', retryable=True)
        return msg['Message-ID']

    # ------------------------------------------------------------ no feed

    def validate(self, text, media, title='', first_comment=''):
        return ['Email is an inbox only; there is nothing to post to.']

    def publish(self, account, text, media, *, title='', link='', first_comment='', options=None):
        raise NotSupported('Email is an inbox only; there is nothing to post to.')
