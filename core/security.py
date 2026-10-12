"""Login protection shared by every way into the system.

All logins (BMS /login/, Django /admin/, the staff portal, the Academy, the
client portal and the mobile app's JWT login) go through authenticate(), so
the lockout lives in an authentication backend: one place covers them all.

* A username is locked for LOCK_SECONDS after MAX_PER_USER failures inside
  WINDOW; an address after MAX_PER_IP failures (catches password spraying
  across many usernames). A correct password does not get through while
  locked, so a bot cannot tell when it has guessed right.
* Counters live in the shared database cache, so every server process and
  every deploy sees the same numbers.
"""
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.signals import user_logged_in, user_login_failed
from django.core.cache import cache
from django.dispatch import receiver
from django.utils.http import url_has_allowed_host_and_scheme

WINDOW = 15 * 60
LOCK_SECONDS = 15 * 60
MAX_PER_USER = 8
MAX_PER_IP = 40


def client_ip(request):
    """The address Railway's proxy saw (the last X-Forwarded-For entry; earlier ones are client-supplied)."""
    if request is None:
        return ''
    fwd = [p.strip() for p in request.META.get('HTTP_X_FORWARDED_FOR', '').split(',') if p.strip()]
    return fwd[-1] if fwd else request.META.get('REMOTE_ADDR', '')


def _keys(username, request):
    user = f'login-fail:user:{(username or "").strip().lower()}'
    ip = f'login-fail:ip:{client_ip(request)}'
    return user, ip


def is_locked(username, request=None):
    user_key, ip_key = _keys(username, request)
    return (cache.get(user_key, 0) >= MAX_PER_USER or
            (bool(client_ip(request)) and cache.get(ip_key, 0) >= MAX_PER_IP))


class LockoutModelBackend(ModelBackend):
    """ModelBackend that refuses while a username or address is locked out."""

    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None:
            username = kwargs.get(self._username_field())
        if is_locked(username, request):
            return None
        return super().authenticate(request, username=username, password=password, **kwargs)

    @staticmethod
    def _username_field():
        from django.contrib.auth import get_user_model
        return get_user_model().USERNAME_FIELD


def _bump(key, limit):
    count = cache.get(key, 0) + 1
    # Reaching the limit starts the lock; until then the window is WINDOW.
    cache.set(key, count, LOCK_SECONDS if count >= limit else WINDOW)


@receiver(user_login_failed)
def _record_failure(sender, credentials, request=None, **kwargs):
    from django.contrib.auth import get_user_model
    username = credentials.get('username') or credentials.get(get_user_model().USERNAME_FIELD)
    user_key, ip_key = _keys(username, request)
    _bump(user_key, MAX_PER_USER)
    if client_ip(request):
        _bump(ip_key, MAX_PER_IP)


@receiver(user_logged_in)
def _clear_on_success(sender, request, user, **kwargs):
    cache.delete(_keys(user.get_username(), request)[0])


def safe_next(request, url, default):
    """``url`` if it stays on this site, else ``default`` (blocks ?next=https://evil.example)."""
    if url and url_has_allowed_host_and_scheme(url, allowed_hosts={request.get_host()},
                                               require_https=request.is_secure()):
        return url
    return default
