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
        {'dateRanges': rng[:1], 'dimensions': [{'name': 'date'}], 'metrics': [{'name': 'activeUsers'}],
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
    by_day = {d[0]: v[0] for d, v in _rows(daily)}
    today = timezone.localdate()
    series = [by_day.get((today - timedelta(days=i)).strftime('%Y%m%d'), 0) for i in range(days - 1, -1, -1)]
    ch = _rows(channels)
    ch_total = sum(v[0] for _, v in ch) or 1
    return {
        'kpis': [
            _kpi('users', 'Visitors', now[0], before[0], series),
            _kpi('sessions', 'Visits', now[1], before[1]),
            _kpi('views', 'Page views', now[2], before[2]),
            _kpi('leads', 'Contact-form leads', ld.get('date_range_0', 0), ld.get('date_range_1', 0)),
        ],
        'avg_minutes': round(now[3] / 60, 1),
        'pages': [{'path': d[0], 'views': int(v[0])} for d, v in _rows(pages)],
        'channels': [{'name': d[0], 'sessions': int(v[0]), 'pct': round(100 * v[0] / ch_total)} for d, v in ch],
        'series': series,
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
    queries = q(start, end, dimensions=['query'], rowLimit=10)
    return {
        'kpis': [
            _kpi('clicks', 'Clicks from Google', now.get('clicks', 0), before.get('clicks', 0)),
            _kpi('impressions', 'Shown in Google', now.get('impressions', 0), before.get('impressions', 0)),
        ],
        'ctr': round(100 * now.get('ctr', 0), 1),
        'position': round(now.get('position', 0), 1) if now.get('position') else None,
        'queries': [{'query': r['keys'][0], 'clicks': int(r['clicks']), 'impressions': int(r['impressions']),
                     'position': round(r['position'], 1)} for r in queries],
        'through': end,
    }


def _kpi(key, label, now, before, spark=None):
    change = round(100 * (now - before) / before, 1) if before else None
    return {'key': key, 'label': label, 'value': int(now), 'change': change, 'spark': spark or []}


def report(days, refresh=False):
    """Everything the Website page shows, cached for an hour. Errors are returned, not raised."""
    key = f'social:website:{days}'
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
