"""Turn a lesson's video link into something a page can play."""
import re
from urllib.parse import parse_qs, urlparse

_YT_ID = re.compile(r'^[A-Za-z0-9_-]{11}$')


def youtube_id(url):
    u = urlparse(url)
    host = (u.hostname or '').lower().removeprefix('www.').removeprefix('m.')
    if host == 'youtu.be':
        vid = u.path.strip('/').split('/')[0]
    elif host in ('youtube.com', 'youtube-nocookie.com'):
        if u.path == '/watch':
            vid = parse_qs(u.query).get('v', [''])[0]
        else:
            parts = [p for p in u.path.split('/') if p]
            vid = parts[1] if len(parts) > 1 and parts[0] in ('embed', 'shorts', 'live') else ''
    else:
        return None
    return vid if _YT_ID.match(vid or '') else None


def embed(url):
    """{'kind': 'iframe'|'file', 'src': ...} or None for no/unknown video."""
    if not url:
        return None
    vid = youtube_id(url)
    if vid:
        # Privacy-enhanced mode: no YouTube cookies until the viewer presses play.
        return {'kind': 'iframe', 'src': f'https://www.youtube-nocookie.com/embed/{vid}?rel=0&modestbranding=1'}
    u = urlparse(url)
    host = (u.hostname or '').lower().removeprefix('www.')
    if host == 'vimeo.com':
        vid = u.path.strip('/').split('/')[0]
        if vid.isdigit():
            return {'kind': 'iframe', 'src': f'https://player.vimeo.com/video/{vid}'}
    if host == 'player.vimeo.com':
        return {'kind': 'iframe', 'src': url}
    if u.scheme == 'https' and u.path.lower().endswith(('.mp4', '.webm', '.m3u8')):
        return {'kind': 'file', 'src': url}
    return None


def is_supported(url):
    return embed(url) is not None
