"""Website numbers (ralfiz.com) for the hub: Google Analytics 4 and Search Console.

Read-only, through a Google Cloud *service account* that has Viewer access on
the GA4 property and the Search Console site. A service account needs no
OAuth consent screen or Google app review. Its key goes in the
GOOGLE_SERVICE_ACCOUNT_JSON setting (the JSON file's contents, or base64 of it).

The access token is signed here with PyJWT (already installed for app logins),
so no Google client library is needed. Results are cached for an hour.
"""
import base64
import json
import logging
import time
from datetime import timedelta
from urllib.parse import quote

import jwt
import requests
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone

log = logging.getLogger(__name__)

TOKEN_URL = 'https://oauth2.googleapis.com/token'
GA4_URL = 'https://analyticsdata.googleapis.com/v1beta/properties/{pid}:batchRunReports'
GSC_URL = 'https://www.googleapis.com/webmasters/v3/sites/{site}/searchAnalytics/query'
SCOPES = ('https://www.googleapis.com/auth/analytics.readonly',
          'https://www.googleapis.com/auth/webmasters.readonly')
CACHE_SECONDS = 3600
#: Bump when the report's shape changes, so a deploy never reads an old cached report.
REPORT_VERSION = 2
TIMEOUT = 30


class WebsiteError(Exception):
    pass


def service_account():
    raw = (getattr(settings, 'GOOGLE_SERVICE_ACCOUNT_JSON', '') or '').strip()
    if not raw:
        return None
    try:
        if not raw.startswith('{'):
            raw = base64.b64decode(raw).decode()
        info = json.loads(raw)
    except (ValueError, UnicodeDecodeError):
        raise WebsiteError('GOOGLE_SERVICE_ACCOUNT_JSON is not a valid service account key.')
    if not info.get('client_email') or not info.get('private_key'):
        raise WebsiteError('The service account key is missing client_email or private_key.')
    return info


def is_configured():
    return bool(getattr(settings, 'GOOGLE_SERVICE_ACCOUNT_JSON', '') and
                (getattr(settings, 'WEBSITE_GA4_PROPERTY_ID', '') or getattr(settings, 'WEBSITE_SEARCH_CONSOLE_SITE', '')))


def _token():
    info = service_account()
    key = f"social:gsa-token:{info['client_email']}"
    token = cache.get(key)
    if token:
        return token
    now = int(time.time())
    assertion = jwt.encode({'iss': info['client_email'], 'scope': ' '.join(SCOPES), 'aud': TOKEN_URL,
                            'iat': now, 'exp': now + 3600}, info['private_key'], algorithm='RS256')
    try:
        r = requests.post(TOKEN_URL, data={'grant_type': 'urn:ietf:params:oauth:grant-type:jwt-bearer',
                                           'assertion': assertion}, timeout=TIMEOUT)
    except requests.RequestException as exc:
        raise WebsiteError(f'Could not reach Google: {exc}')
    if r.status_code != 200:
        raise WebsiteError(f'Google refused the service account key ({r.status_code}).')
    token = r.json()['access_token']
    cache.set(key, token, 3300)
    return token


def _post(url, body):
    try:
        r = requests.post(url, json=body, headers={'Authorization': f'Bearer {_token()}'}, timeout=TIMEOUT)
    except requests.RequestException as exc:
        raise WebsiteError(f'Could not reach Google: {exc}')
    if r.status_code == 403:
        email = service_account()['client_email']
        raise WebsiteError(f'Google says no access. Add {email} as a Viewer (Analytics) / user (Search Console).')
    if r.status_code != 200:
        try:
            msg = r.json().get('error', {}).get('message', '')
        except ValueError:
            msg = ''
        raise WebsiteError(f'Google error {r.status_code}: {msg[:200]}')
    return r.json()


def _rows(report):
    out = []
    for row in report.get('rows') or []:
        dims = [d.get('value', '') for d in row.get('dimensionValues') or []]
        vals = [float(m.get('value') or 0) for m in row.get('metricValues') or []]
        out.append((dims, vals))
    return out


def analytics(days):
    """GA4: totals, a daily series, top pages, traffic channels and contact-form leads."""
    pid = getattr(settings, 'WEBSITE_GA4_PROPERTY_ID', '')
    if not pid:
        return None
    rng = [{'startDate': f'{days}daysAgo', 'endDate': 'today'},
           {'startDate': f'{days * 2}daysAgo', 'endDate': f'{days + 1}daysAgo'}]
    reqs = [
        {'dateRanges': rng, 'metrics': [{'name': n} for n in ('activeUsers', 'sessions', 'screenPageViews',
                                                               'averageSessionDuration')]},
        {'dateRanges': rng[:1], 'dimensions': [{'name': 'date'}],
         'metrics': [{'name': 'activeUsers'}, {'name': 'screenPageViews'}],
         'orderBys': [{'dimension': {'dimensionName': 'date'}}]},
        {'dateRanges': rng[:1], 'dimensions': [{'name': 'pagePath'}], 'metrics': [{'name': 'screenPageViews'}],
         'orderBys': [{'metric': {'metricName': 'screenPageViews'}, 'desc': True}], 'limit': 8},
        {'dateRanges': rng[:1], 'dimensions': [{'name': 'sessionDefaultChannelGroup'}],
         'metrics': [{'name': 'sessions'}], 'orderBys': [{'metric': {'metricName': 'sessions'}, 'desc': True}]},
        {'dateRanges': rng, 'dimensions': [{'name': 'eventName'}], 'metrics': [{'name': 'eventCount'}],
         'dimensionFilter': {'filter': {'fieldName': 'eventName', 'stringFilter': {'value': 'generate_lead'}}}},
    ]
    totals, daily, pages, channels, leads = _post(GA4_URL.format(pid=quote(str(pid))), {'requests': reqs})['reports']
    # With two date ranges GA4 adds a dateRange dimension: date_range_0 is now, _1 the period before.
    t = {d[-1] if d else 'date_range_0': v for d, v in _rows(totals)}
    now, before = t.get('date_range_0', [0, 0, 0, 0]), t.get('date_range_1', [0, 0, 0, 0])
    ld = {d[-1]: v[0] for d, v in _rows(leads)}
    by_day = {d[0]: v for d, v in _rows(daily)}
    today = timezone.localdate()
    keys = [(today - timedelta(days=i)).strftime('%Y%m%d') for i in range(days - 1, -1, -1)]
    series = [by_day.get(k, [0, 0])[0] for k in keys]
    views_series = [by_day.get(k, [0, 0])[1] for k in keys]
    ch = _rows(channels)
    ch_total = sum(v[0] for _, v in ch) or 1
    return {
        'kpis': [
            _kpi('users', 'Visitors', now[0], before[0], series),
            _kpi('sessions', 'Visits', now[1], before[1]),
            _kpi('views', 'Page views', now[2], before[2], views_series),
            _kpi('leads', 'Contact-form leads', ld.get('date_range_0', 0), ld.get('date_range_1', 0)),
        ],
        'avg_minutes': round(now[3] / 60, 1),
        'pages': [{'path': d[0], 'views': int(v[0])} for d, v in _rows(pages)],
        'channels': [{'name': d[0], 'sessions': int(v[0]), 'pct': round(100 * v[0] / ch_total)} for d, v in ch],
        'series': series, 'views_series': views_series,
        'labels': [(today - timedelta(days=i)).strftime('%d %b') for i in range(days - 1, -1, -1)],
        'sessions': int(now[1]), 'leads': int(ld.get('date_range_0', 0)),
    }


def search(days):
    """Search Console: clicks, impressions, position and top queries. Data lags about 3 days."""
    site = getattr(settings, 'WEBSITE_SEARCH_CONSOLE_SITE', '')
    if not site:
        return None
    end = timezone.localdate() - timedelta(days=3)
    start, prev_end = end - timedelta(days=days - 1), end - timedelta(days=days)
    prev_start = prev_end - timedelta(days=days - 1)
    url = GSC_URL.format(site=quote(site, safe=''))

    def q(s, e, **extra):
        return _post(url, {'startDate': s.isoformat(), 'endDate': e.isoformat(), **extra}).get('rows') or []

    now, before = (q(start, end) or [{}])[0], (q(prev_start, prev_end) or [{}])[0]
    all_queries = q(start, end, dimensions=['query'], rowLimit=200)
    queries = all_queries[:10]
    by_date = {r['keys'][0]: r for r in q(start, end, dimensions=['date'], rowLimit=500)}
    dates = [start + timedelta(days=i) for i in range(days)]
    clicks = [by_date.get(d.isoformat(), {}).get('clicks', 0) for d in dates]
    shown = [by_date.get(d.isoformat(), {}).get('impressions', 0) for d in dates]
    pages = q(start, end, dimensions=['page'], rowLimit=8)
    # "Almost page one": people see you, but you sit below the top results.
    opportunities = sorted((r for r in all_queries if r['impressions'] >= 10 and 3.5 < r['position'] <= 20),
                           key=lambda r: -r['impressions'])[:8]
    return {
        'kpis': [
            _kpi('clicks', 'Clicks from Google', now.get('clicks', 0), before.get('clicks', 0), clicks),
            _kpi('impressions', 'Shown in Google', now.get('impressions', 0), before.get('impressions', 0), shown),
        ],
        'labels': [d.strftime('%d %b') for d in dates], 'clicks_series': clicks, 'shown_series': shown,
        'pages': [{'url': r['keys'][0], 'clicks': int(r['clicks']), 'impressions': int(r['impressions'])}
                  for r in pages],
        'opportunities': [{'query': r['keys'][0], 'clicks': int(r['clicks']), 'impressions': int(r['impressions']),
                           'position': round(r['position'], 1)} for r in opportunities],
        'low_ctr': [{'query': r['keys'][0], 'impressions': int(r['impressions']), 'ctr': round(100 * r['ctr'], 1),
                     'position': round(r['position'], 1)}
                    for r in all_queries if r['position'] <= 3 and r['impressions'] >= 20 and r['ctr'] < 0.05][:5],
        'ctr': round(100 * now.get('ctr', 0), 1),
        'position': round(now.get('position', 0), 1) if now.get('position') else None,
        'queries': [{'query': r['keys'][0], 'clicks': int(r['clicks']), 'impressions': int(r['impressions']),
                     'position': round(r['position'], 1)} for r in queries],
        'through': end,
    }


def tips(data):
    """Plain-English suggestions worked out from the numbers (no AI needed)."""
    out = []
    ga, gsc = data.get('ga'), data.get('gsc')
    if gsc:
        for o in gsc['opportunities'][:3]:
            out.append(('fa-arrow-trend-up', f'You are #{o["position"]:g} for "{o["query"]}"',
                        f'Google showed you {o["impressions"]} times but you got {o["clicks"]} clicks. A page or blog '
                        f'post aimed at exactly this phrase (in the title and first heading) can move you into the top 3, '
                        f'where most clicks go.'))
        for o in gsc['low_ctr'][:2]:
            out.append(('fa-heading', f'Rewrite the Google title for "{o["query"]}"',
                        f'You are already #{o["position"]:g}, but only {o["ctr"]}% of people click. A clearer title and '
                        f'description (what you offer, Perinthalmanna / Kerala, a reason to click) usually doubles that.'))
    if ga:
        names = {c['name'] for c in ga['channels'] if c['sessions']}
        if ga['sessions'] and 'Organic Social' not in names:
            out.append(('fa-share-nodes', 'No visits from social media yet',
                        'Put ralfiz.com in your Instagram and Facebook bio, add link stickers to stories, and end posts '
                        'with the page link. Every post you publish from the hub can carry a link.'))
        if ga['sessions'] >= 30 and not ga['leads']:
            out.append(('fa-envelope-open-text', 'Visitors, but no contact-form leads',
                        'Add a clear "Get a free quote" button and a WhatsApp button near the top of the home and '
                        'services pages, so people can ask without scrolling.'))
    out.append(('fa-gauge-high', 'Keep the site fast on phones',
                'Test it at pagespeed.web.dev and aim for 90+ on mobile. Oversized images are the usual cause of a '
                'slow page. Faster pages rank higher and fewer visitors leave before it loads.'))
    out.append(('fa-pen-nib', 'Publish one useful post a month',
                'Short guides people in Kerala search for (e.g. "website cost for small business in Kerala", '
                '"billing software for shops") bring steady free visitors and leads.'))
    return out[:6]


def _kpi(key, label, now, before, spark=None):
    change = round(100 * (now - before) / before, 1) if before else None
    return {'key': key, 'label': label, 'value': int(now), 'change': change, 'spark': spark or []}


def report(days, refresh=False):
    """Everything the Website page shows, cached for an hour. Errors are returned, not raised."""
    key = f'social:website:v{REPORT_VERSION}:{days}'
    data = None if refresh else cache.get(key)
    if data is None:
        data = {'ga': None, 'gsc': None, 'errors': []}
        for name, fn in (('ga', analytics), ('gsc', search)):
            try:
                data[name] = fn(days)
            except WebsiteError as exc:
                data['errors'].append(str(exc))
            except (KeyError, ValueError, TypeError, IndexError):
                log.exception('website %s report could not be read', name)
                data['errors'].append(f'Google sent back {name.upper()} data in an unexpected shape.')
        cache.set(key, data, CACHE_SECONDS if not data['errors'] else 300)
    return data


def summary_text(data, days):
    """The report as compact text for the AI (numbers and phrases only)."""
    lines = [f'Period: last {days} days.']
    ga, gsc = data.get('ga'), data.get('gsc')
    if ga:
        lines.append('Google Analytics: ' + ', '.join(f"{k['label']} {k['value']}"
                     + (f" ({k['change']:+}% vs previous period)" if k['change'] is not None else '') for k in ga['kpis'])
                     + f", average visit {ga['avg_minutes']} min.")
        lines.append('Visits by channel: ' + (', '.join(f"{c['name']} {c['sessions']}" for c in ga['channels']) or 'none yet'))
        lines.append('Top pages: ' + (', '.join(f"{p['path']} {p['views']} views" for p in ga['pages']) or 'none yet'))
    if gsc:
        lines.append('Google Search: ' + ', '.join(f"{k['label']} {k['value']}" for k in gsc['kpis'])
                     + f", click rate {gsc['ctr']}%, average position {gsc['position']}.")
        lines.append('Top searches (clicks/impressions/position): ' + '; '.join(
            f"\"{q['query']}\" {q['clicks']}/{q['impressions']}/#{q['position']}" for q in gsc['queries']))
        lines.append('Searches where we are on page 1-2 but not top 3: ' + ('; '.join(
            f"\"{q['query']}\" #{q['position']} shown {q['impressions']}" for q in gsc['opportunities']) or 'none'))
        lines.append('Top pages in Google: ' + '; '.join(f"{p['url']} {p['clicks']} clicks" for p in gsc['pages']))
    return '\n'.join(lines)


# ---------------------------------------------------------------- Google reviews (Places API)
# Read-only: rating, review count and the 5 newest reviews Google shows publicly. Needs a Maps
# Platform API key with "Places API (New)" enabled. Replying needs the Business Profile API instead.

PLACES_URL = 'https://places.googleapis.com/v1/'
REVIEW_FIELDS = 'id,displayName,rating,userRatingCount,googleMapsUri,reviews'


def _places(method, path, field_mask, body=None):
    key = getattr(settings, 'GOOGLE_MAPS_API_KEY', '')
    try:
        r = requests.request(method, PLACES_URL + path, json=body, timeout=TIMEOUT,
                             headers={'X-Goog-Api-Key': key, 'X-Goog-FieldMask': field_mask})
    except requests.RequestException as exc:
        raise WebsiteError(f'Could not reach Google: {exc}')
    if r.status_code != 200:
        try:
            msg = r.json().get('error', {}).get('message', '')
        except ValueError:
            msg = ''
        raise WebsiteError(f'Google reviews: {msg[:200] or r.status_code}')
    return r.json()


def place_id():
    """The business's Google place id: WEBSITE_PLACE_ID, or found once by name and remembered."""
    pid = getattr(settings, 'WEBSITE_PLACE_ID', '')
    if pid:
        return pid
    query = getattr(settings, 'WEBSITE_PLACE_QUERY', '') or 'Ralfiz Technologies Perinthalmanna'
    ck = f'social:website:place-id:{query}'
    pid = cache.get(ck)
    if not pid:
        found = _places('POST', 'places:searchText', 'places.id', {'textQuery': query}).get('places') or []
        if not found:
            raise WebsiteError(f'Google Maps found no business for "{query}". Set WEBSITE_PLACE_ID.')
        pid = found[0]['id']
        cache.set(ck, pid, 30 * 24 * 3600)
    return pid


def google_reviews(refresh=False):
    """Rating, count and the newest reviews, cached for 12 hours. Returns None when not set up."""
    if not getattr(settings, 'GOOGLE_MAPS_API_KEY', ''):
        return None
    ck = f'social:website:v{REPORT_VERSION}:reviews'
    data = None if refresh else cache.get(ck)
    if data is None:
        try:
            p = _places('GET', f'places/{place_id()}', REVIEW_FIELDS)
            reviews = sorted(p.get('reviews') or [], key=lambda r: r.get('publishTime', ''), reverse=True)
            data = {'name': (p.get('displayName') or {}).get('text', ''), 'rating': p.get('rating'),
                    'count': p.get('userRatingCount', 0), 'url': p.get('googleMapsUri', ''), 'error': '',
                    'reviews': [{
                        'author': (r.get('authorAttribution') or {}).get('displayName', 'Google user'),
                        'author_url': (r.get('authorAttribution') or {}).get('uri', ''),
                        'photo': (r.get('authorAttribution') or {}).get('photoUri', ''),
                        'rating': int(r.get('rating') or 0),
                        'text': ((r.get('originalText') or r.get('text') or {}).get('text', '')),
                        'when': r.get('relativePublishTimeDescription', ''),
                    } for r in reviews]}
        except WebsiteError as exc:
            data = {'error': str(exc), 'reviews': []}
        cache.set(ck, data, 12 * 3600 if not data['error'] else 300)
    return data
