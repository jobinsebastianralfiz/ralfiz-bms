"""Read a YouTube playlist and match its videos to a course's lessons.

Uses the YouTube Data API with a read-only key (settings.YOUTUBE_API_KEY), so
it needs no Google sign-in. An unlisted playlist works as long as the key's
project can reach it by ID.
"""
import re
from urllib.parse import parse_qs, urlparse

from django.conf import settings

API = 'https://www.googleapis.com/youtube/v3/playlistItems'
_LIST_ID = re.compile(r'^[A-Za-z0-9_-]{10,}$')


class YouTubeError(Exception):
    pass


def playlist_id(text):
    """The playlist ID from a playlist, watch or Studio link, or a bare ID. None if there is none."""
    text = (text or '').strip()
    if _LIST_ID.match(text):
        return text
    u = urlparse(text)
    pid = parse_qs(u.query).get('list', [''])[0]
    parts = [p for p in u.path.split('/') if p]
    if not pid and (u.hostname or '').lower() == 'studio.youtube.com' and len(parts) > 1 and parts[0] == 'playlist':
        pid = parts[1]  # studio.youtube.com/playlist/<id>/edit
    return pid if _LIST_ID.match(pid) else None


def playlist_videos(pid):
    """[{'id', 'title', 'private'}] for every video in the playlist, in playlist order."""
    import requests

    key = settings.YOUTUBE_API_KEY
    if not key:
        raise YouTubeError('YOUTUBE_API_KEY is not set on the server.')
    videos, page = [], None
    while True:
        params = {'part': 'snippet,status', 'playlistId': pid, 'maxResults': 50, 'key': key}
        if page:
            params['pageToken'] = page
        try:
            r = requests.get(API, params=params, timeout=15)
        except requests.RequestException:
            raise YouTubeError('Could not reach YouTube. Try again in a minute.')
        if r.status_code == 404:
            raise YouTubeError('YouTube cannot find that playlist. Check the link, and that the '
                               'playlist is Unlisted or Public, not Private.')
        if r.status_code != 200:
            reason = (r.json().get('error', {}).get('message', '') if r.headers.get(
                'content-type', '').startswith('application/json') else '')
            raise YouTubeError(f'YouTube refused the request ({r.status_code}). {reason}'.strip())
        data = r.json()
        for item in data.get('items', []):
            vid = item.get('snippet', {}).get('resourceId', {}).get('videoId')
            if not vid:
                continue
            videos.append({
                'id': vid,
                'title': item['snippet'].get('title', ''),
                # A private (or deleted) video cannot play inside the Academy.
                'private': item.get('status', {}).get('privacyStatus') not in ('public', 'unlisted'),
            })
        page = data.get('nextPageToken')
        if not page:
            return videos


def lesson_num(title, track_code):
    """'2.10' or 'A.3' from titles like 'PL-900 2.10 · ALM …', YouTube's 'PL 900 2 10 ALM …'
    or 'AB 410 A 3 Solutions …'.

    The course code must lead the title, so a PL-300 video never lands in PL-900.
    """
    letters, _, digits = track_code.partition('-')
    code = rf'{re.escape(letters)}[\s._-]*{re.escape(digits)}' if digits else re.escape(letters)
    m = re.match(rf'\s*{code}[\s._·:-]+(\d+|[A-Za-z])[\s._-]+(\d+)\b', title, re.IGNORECASE)
    if not m:
        return None
    part = m[1].upper() if m[1].isalpha() else str(int(m[1]))
    return f'{part}.{int(m[2])}'


def match(videos, lessons, track_code):
    """Pair playlist videos with lessons by the lesson number in the title.

    Returns (links, unmatched, private): {lesson_id: youtu.be link}, titles no
    lesson matched, and titles skipped because they are private.
    """
    by_num = {l.num: l for l in lessons}
    links, unmatched, private = {}, [], []
    for v in videos:
        lesson = by_num.get(lesson_num(v['title'], track_code) or '')
        if v['private']:
            private.append(v['title'])
        elif lesson is None:
            unmatched.append(v['title'])
        elif lesson.id not in links:  # the first copy in the playlist wins
            links[lesson.id] = f"https://youtu.be/{v['id']}"
    return links, unmatched, private
