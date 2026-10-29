"""Holiday suggestions for HR > Calendar > Import.

Google's public India calendar (no key needed) has the central gazetted holidays
and festivals such as Vishu and Onam, but it isn't Kerala's list: it has Holi and
Guru Nanak Jayanti, and misses May Day and Mannam Jayanthi. So everything comes
back as a suggestion. Kerala holidays are ticked, the rest are not, and HR saves
only what it ticks. Lunar dates move every year, so they always come from the feed.
"""
import re
import urllib.request
from datetime import date

FEED = ('https://calendar.google.com/calendar/ical/'
        'en.indian%23holiday%40group.v.calendar.google.com/public/basic.ics')

# Names in Google's feed that Kerala closes for (lower case, matched as substrings)
KERALA = ['republic day', 'independence day', 'gandhi jayanti', 'ramzan id', 'good friday', 'vishu',
          'bakrid', 'muharram', 'onam', 'milad un-nabi', 'janmashtami', 'dussehra', 'maha navami',
          'diwali', 'christmas', 'maha shivaratri', 'ambedkar jayanti', 'maundy thursday']
SKIP = ['eve', 'smarta']

# Kerala holidays on the same date every year, which Google's feed doesn't list
KERALA_FIXED = [(1, 2, 'Mannam Jayanthi'), (5, 1, 'May Day'), (8, 28, 'Ayyankali Jayanthi')]


class ImportError_(Exception):
    pass


def _is_kerala(name):
    low = name.lower()
    return any(k in low for k in KERALA) and not any(k in low for k in SKIP)


def parse_ics(text, year):
    text = text.replace('\r\n ', '').replace('\n ', '')
    out = []
    for block in re.findall(r'BEGIN:VEVENT(.*?)END:VEVENT', text, re.S):
        when = re.search(r'DTSTART;VALUE=DATE:(\d{8})', block)
        name = re.search(r'SUMMARY:(.*)', block)
        if not when or not name:
            continue
        day = date(int(when[1][:4]), int(when[1][4:6]), int(when[1][6:]))
        if day.year != year:
            continue
        desc = re.search(r'DESCRIPTION:(.*)', block)
        public = bool(desc and desc[1].startswith('Public holiday'))
        out.append({'date': day, 'name': name[1].strip().replace('\\,', ','), 'public': public,
                    'tentative': 'tentative' in name[1].lower(), 'source': 'google'})
    return out


def fetch(year):
    try:
        req = urllib.request.Request(FEED, headers={'User-Agent': 'RalfizBMS/1.0'})
        with urllib.request.urlopen(req, timeout=15) as resp:
            text = resp.read().decode('utf-8', 'replace')
    except OSError as exc:
        raise ImportError_(f"Couldn't reach Google's holiday calendar ({exc}). Add holidays by hand for now.")
    return parse_ics(text, year)


def suggestions(year, existing):
    """One row per date, Kerala holidays ticked. `existing` is a set of dates already marked."""
    by_date = {}
    fixed = [{'date': date(year, m, d), 'name': n, 'public': False, 'source': 'kerala'} for m, d, n in KERALA_FIXED]
    for ev in fetch(year) + fixed:
        row = by_date.setdefault(ev['date'], {'date': ev['date'], 'kerala_names': [], 'others': [],
                                              'public': False, 'source': 'google'})
        if ev['source'] == 'kerala' or _is_kerala(ev['name']):
            row['kerala_names'].append(ev['name'])
            if ev['source'] == 'kerala':
                row['source'] = 'kerala'
        else:
            row['others'].append(ev['name'])
        row['public'] = row['public'] or ev['public']
    out = []
    for row in sorted(by_date.values(), key=lambda r: r['date']):
        kerala = bool(row['kerala_names'])
        names = row['kerala_names'] if kerala else row['others'][:1]
        out.append({
            'date': row['date'], 'name': ' / '.join(names),
            'others': [n for n in row['others'] if n not in names],
            'kind': 'public' if row['public'] else 'kerala', 'source': row['source'],
            'kerala': kerala, 'exists': row['date'] in existing,
            'checked': kerala and row['date'] not in existing,
            'tentative': 'tentative' in ' '.join(names).lower(),
        })
    return out
