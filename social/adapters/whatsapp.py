"""WhatsApp Business through the Cloud API.

There is no OAuth here: the business creates a System User in Business
Manager, gives it a permanent token for the WhatsApp Business Account, and
pastes that token with the phone number id and WABA id into a form.

WhatsApp has no feed, so nothing is published; incoming messages arrive only
by webhook (social/webhooks.py). Free-form replies are allowed for 24 hours
after the customer's last message; outside that window only approved
templates can be sent (``send_template``).
"""
import logging
import secrets

from django.conf import settings

from .base import AccountCandidate, Adapter, AdapterError, Capabilities, NotSupported
from .meta import graph

log = logging.getLogger(__name__)


def wa_app():
    """(app id, app secret) of the Meta app that runs WhatsApp: its own, or the main one."""
    if getattr(settings, 'META_WHATSAPP_APP_ID', '') and getattr(settings, 'META_WHATSAPP_APP_SECRET', ''):
        return settings.META_WHATSAPP_APP_ID, settings.META_WHATSAPP_APP_SECRET
    return settings.META_APP_ID, settings.META_APP_SECRET


def _ok(data, what):
    """Graph returns most failures as a 400 with an ``error`` body; turn that into a message."""
    if isinstance(data, dict) and data.get('error'):
        err = data['error']
        raise AdapterError(f"{what}: {err.get('error_user_msg') or err.get('message') or err}")
    return data


class WhatsAppAdapter(Adapter):
    platform = 'whatsapp'
    label = 'WhatsApp'
    caps = Capabilities(max_chars=4096, text_only=True, images=False, video=False, max_media=0,
                        link=False, inbox=('dm',), insights=False)
    connect_mode = 'manual'
    required_settings = ()
    manual_fields = [
        ('phone_number_id', 'Phone number ID',
         'WhatsApp Manager → API setup: the id of the business phone number (not the number itself).'),
        ('waba_id', 'WhatsApp Business Account ID', 'Shown next to the phone number id in API setup.'),
        ('access_token', 'Access token',
         'A permanent System User token with whatsapp_business_messaging and '
         'whatsapp_business_management. Temporary 24-hour test tokens stop working the next day.'),
    ]

    def manual_connect(self, data):
        values = {name: (data.get(name) or '').strip() for name, _, _ in self.manual_fields}
        missing = [label for name, label, _ in self.manual_fields if not values[name]]
        if missing:
            raise AdapterError(f'Fill in: {", ".join(missing)}.')
        phone = _ok(graph('GET', values['phone_number_id'], values['access_token'], platform=self.label,
                          params={'fields': 'verified_name,display_phone_number'}), 'Could not read the number')
        try:   # so incoming messages reach the hub's webhook (already subscribed is fine)
            _ok(graph('POST', f"{values['waba_id']}/subscribed_apps", values['access_token'], platform=self.label),
                'Could not subscribe to WhatsApp messages')
        except AdapterError:
            log.warning('WhatsApp manual connect: subscribing the app to the WABA failed', exc_info=True)
        number = phone.get('display_phone_number', '')
        return [AccountCandidate(
            external_id=values['phone_number_id'], name=phone.get('verified_name') or number,
            handle=number, token=values['access_token'], extra={'waba_id': values['waba_id']},
            expires_at=self._token_expiry(values['access_token']))]

    # ------------------------------------------------------------ Embedded Signup
    # Meta's "Connect WhatsApp" popup. With coexistence the business keeps using the
    # WhatsApp Business app on its phone; the same number also works here.

    def embedded_ready(self):
        app_id, secret = wa_app()
        return bool(app_id and secret and getattr(settings, 'META_WHATSAPP_CONFIG_ID', ''))

    def embedded_connect(self, code, phone_number_id, waba_id, *, coexistence=True):
        """Finish Embedded Signup: swap the popup's code for a business token, read the
        number, and subscribe this app to the WhatsApp account's webhooks."""
        if not (code and phone_number_id and waba_id):
            raise AdapterError('Meta did not send the WhatsApp details back. Try connecting again.')
        token = _ok(graph('GET', 'oauth/access_token', platform=self.label, params={
            'client_id': wa_app()[0], 'client_secret': wa_app()[1], 'code': code,
        }), 'Could not finish the WhatsApp sign-in').get('access_token')
        if not token:
            raise AdapterError('Meta did not return an access token. Try connecting again.')
        phone = _ok(graph('GET', phone_number_id, token, platform=self.label,
                          params={'fields': 'verified_name,display_phone_number'}),
                    'Could not read the WhatsApp number')
        _ok(graph('POST', f'{waba_id}/subscribed_apps', token, platform=self.label),
            'Could not subscribe to WhatsApp messages')
        extra = {'waba_id': waba_id, 'coexistence': coexistence, 'via': 'embedded_signup'}
        if not coexistence:
            # A number that lives only on the API has to be registered, with a two-step PIN.
            pin = f'{secrets.randbelow(10 ** 6):06d}'
            _ok(graph('POST', f'{phone_number_id}/register', token, platform=self.label,
                      json={'messaging_product': 'whatsapp', 'pin': pin}),
                'Could not register the WhatsApp number')
            from social.crypto import encrypt
            extra['pin_encrypted'] = encrypt(pin)   # Meta asks for it again if the number is re-registered
        number = phone.get('display_phone_number', '')
        return [AccountCandidate(external_id=str(phone_number_id), name=phone.get('verified_name') or number,
                                 handle=number, token=token, extra=extra, expires_at=self._token_expiry(token))]

    def _token_expiry(self, token):
        """When the signup token runs out (the 60-day template), so the hub warns a week ahead.
        None means it never expires, or Meta would not say."""
        app_id, secret = wa_app()
        try:
            info = graph('GET', 'debug_token', platform=self.label,
                         params={'input_token': token, 'access_token': f'{app_id}|{secret}'}).get('data') or {}
        except AdapterError:
            log.warning('Could not read the WhatsApp token expiry', exc_info=True)
            return None
        when = int(info.get('expires_at') or 0)
        if not when:
            return None
        from datetime import datetime, timezone as dt_timezone
        return datetime.fromtimestamp(when, tz=dt_timezone.utc)

    def validate(self, text, media, title='', first_comment=''):
        return ['WhatsApp posts are not supported: WhatsApp has no feed. '
                'Broadcasts go out as approved message templates.']

    def publish(self, account, text, media, *, title='', link='', first_comment='', options=None):
        raise NotSupported('WhatsApp has no feed to post to; send an approved template instead.')

    def fetch_inbox(self, account, since=None):
        return []       # the Cloud API cannot be polled; messages arrive by webhook

    def _send(self, account, payload):
        data = graph('POST', f'{account.external_id}/messages', account.token, platform=self.label,
                     json={'messaging_product': 'whatsapp', 'recipient_type': 'individual', **payload})
        return ((data.get('messages') or [{}])[0]).get('id', '')

    def reply(self, account, item, text):
        """Free-form text to the customer (item.author_id is their wa_id)."""
        return self._send(account, {'to': item.author_id, 'type': 'text',
                                    'text': {'preview_url': False, 'body': text}})

    def send_template(self, account, to, template_name, language='en', components=None):
        """An approved template: the only message allowed outside the 24-hour window."""
        template = {'name': template_name, 'language': {'code': language}}
        if components:
            template['components'] = components
        return self._send(account, {'to': to, 'type': 'template', 'template': template})
