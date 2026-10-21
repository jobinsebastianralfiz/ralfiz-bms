"""A platform that does nothing, for tests and for trying the hub locally.

With SOCIAL_FAKE_ADAPTERS = True (the default when DEBUG is on and no
platform app is configured), every platform uses this adapter: connecting
creates a demo account, publishing returns a made-up id, and the inbox and
insights return sample data, so the whole flow runs with no API keys.
"""
import random
import uuid
from datetime import timedelta

from django.utils import timezone

from .base import AccountCandidate, Adapter, AdapterError, Capabilities, FetchedItem, FetchedPost, PublishResult


class FakeAdapter(Adapter):
    connect_mode = 'fake'

    def __init__(self, real):
        self.real = real
        self.platform = real.platform
        self.label = real.label
        self.caps = real.caps
        self.published = []
        self.fail_next = None

    def is_configured(self):
        return True

    def demo_candidate(self, workspace_name):
        slug = workspace_name.lower().replace(' ', '')[:20]
        return AccountCandidate(
            external_id=f'demo-{self.platform}-{uuid.uuid4().hex[:8]}',
            name=f'{workspace_name} ({self.label} demo)',
            handle=f'@{slug}' if self.platform in ('instagram', 'x') else '',
            token='demo-token',
            expires_at=timezone.now() + timedelta(days=60),
        )

    def validate(self, text, media, **kwargs):
        return self.real.validate(text, media, **kwargs)

    def publish(self, account, text, media, *, title='', link='', first_comment='', options=None):
        if self.fail_next:
            err, self.fail_next = self.fail_next, None
            raise err
        external_id = f'{self.platform}_{uuid.uuid4().hex[:12]}'
        self.published.append({'account': account.pk, 'text': text, 'media': len(media)})
        return PublishResult(external_id, f'https://example.com/{self.platform}/{external_id}')

    def delete(self, account, external_id):
        return True

    def fetch_inbox(self, account, since=None):
        if self.platform not in ('facebook', 'instagram', 'whatsapp', 'google_business',
                                 'youtube', 'linkedin'):
            return []
        kind = {'whatsapp': 'dm', 'google_business': 'review'}.get(self.platform, 'comment')
        now = timezone.now()
        samples = [
            ('Anjali R.', 'Do you have parking near the shop?'),
            ('Rahul M.', 'Great service, thank you!'),
            ('Sneha K.', 'What are your timings on Sunday?'),
        ]
        return [
            FetchedItem(kind=kind, external_id=f'demo-{account.pk}-{i}', text=text, author_name=who,
                        rating=5 if kind == 'review' else None,
                        received_at=now - timedelta(minutes=15 * (i + 1)))
            for i, (who, text) in enumerate(samples)
        ]

    def reply(self, account, item, text):
        if self.fail_next:
            err, self.fail_next = self.fail_next, None
            raise err
        return f'reply_{uuid.uuid4().hex[:10]}'

    def private_reply(self, account, comment_id, text, buttons=None):
        if self.fail_next:
            err, self.fail_next = self.fail_next, None
            raise err
        return f'dm_{uuid.uuid4().hex[:10]}'

    def send_dm(self, account, user_id, text, buttons=None):
        return self.private_reply(account, user_id, text, buttons)

    def user_profile(self, account, user_id):
        return {'name': 'Demo follower', 'username': 'demo', 'is_follower': True}

    def fetch_insights(self, account, start, end):
        rnd = random.Random(str(account.pk))
        out, day = {}, start
        base = rnd.randint(200, 2000)
        while day <= end:
            out[day] = {
                'reach': base + rnd.randint(-150, 400),
                'impressions': int(base * 1.6) + rnd.randint(0, 600),
                'engagement': rnd.randint(20, 220),
                'followers': 1000 + (day - start).days * rnd.randint(0, 6),
            }
            day += timedelta(days=1)
        return out

    def fetch_post_metrics(self, account, external_id):
        rnd = random.Random(external_id)
        return {'reach': rnd.randint(200, 5000), 'engagement': rnd.randint(10, 400)}

    def fetch_posts(self, account, since=None, limit=50):
        rnd = random.Random(f'{account.pk}-posts')
        now = timezone.now()
        kinds = {'instagram': ['reel', 'post', 'carousel', 'post'], 'youtube': ['video'],
                 'facebook': ['post', 'video', 'post']}.get(self.platform, ['post'])
        out = []
        for i in range(8):
            when = now - timedelta(days=3 * i + 1, hours=rnd.randint(0, 10))
            if since and when <= since:
                break
            likes, comments = rnd.randint(20, 900), rnd.randint(0, 80)
            out.append(FetchedPost(
                external_id=f'demo-post-{account.pk}-{i}', text=f'Sample {self.label} post #{i + 1}',
                published_at=when, url=f'https://example.com/{self.platform}/p{i}', kind=kinds[i % len(kinds)],
                metrics={'likes': likes, 'comments': comments, 'engagement': likes + comments,
                         'views': rnd.randint(500, 20000)}))
        return out

    def quota_status(self, account, published_last_24h):
        return self.real.quota_status(account, published_last_24h)


class FailingError(AdapterError):
    pass
