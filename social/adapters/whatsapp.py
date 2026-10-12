"""WhatsApp Business through the Cloud API.

There is no OAuth here: the business creates a System User in Business
Manager, gives it a permanent token for the WhatsApp Business Account, and
pastes that token with the phone number id and WABA id into a form.

WhatsApp has no feed, so nothing is published; incoming messages arrive only
by webhook (social/webhooks.py). Free-form replies are allowed for 24 hours
after the customer's last message; outside that window only approved
templates can be sent (``send_template``).
"""
from .base import AccountCandidate, Adapter, AdapterError, Capabilities, NotSupported
from .meta import graph


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
        phone = graph('GET', values['phone_number_id'], values['access_token'], platform=self.label,
                      params={'fields': 'verified_name,display_phone_number'})
        number = phone.get('display_phone_number', '')
        return [AccountCandidate(
            external_id=values['phone_number_id'], name=phone.get('verified_name') or number,
            handle=number, token=values['access_token'], extra={'waba_id': values['waba_id']})]

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
