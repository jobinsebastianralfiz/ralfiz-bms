"""The world clock on the dashboard: its own page (framed on '/'), with
current weather for every city fetched once from Open-Meteo and cached."""
from unittest import mock

import requests
from django.contrib.auth.models import User
from django.core.cache import cache
from django.test import TestCase, override_settings
from django.urls import reverse

from .views import WORLD_CLOCK_CITIES, currency_rates, world_clock_weather

LOCMEM = {'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'}}


def _row(code=61, is_day=1):
    return {'current': {'temperature_2m': 27.4, 'weather_code': code, 'is_day': is_day},
            'daily': {'temperature_2m_max': [31.0], 'temperature_2m_min': [23.5],
                      'precipitation_probability_max': [80]}}


def _response(rows):
    resp = mock.Mock(status_code=200)
    resp.json.return_value = rows
    resp.raise_for_status.return_value = None
    return resp


@override_settings(CACHES=LOCMEM)
class WorldClockWeatherTests(TestCase):
    def setUp(self):
        cache.clear()

    def test_maps_each_city_and_caches(self):
        rows = [_row() for _ in WORLD_CLOCK_CITIES]
        with mock.patch('requests.get', return_value=_response(rows)) as get:
            data = world_clock_weather()
            world_clock_weather()
        self.assertEqual(get.call_count, 1)
        self.assertEqual(set(data['cities']), set(WORLD_CLOCK_CITIES))
        self.assertEqual(data['cities']['Asia/Kolkata'],
                         {'t': 27.4, 'c': 'rain', 'x': 'Light rain', 'd': True,
                          'hi': 31.0, 'lo': 23.5, 'p': 80})

    def test_unreachable_service_gives_empty_and_is_not_cached(self):
        with mock.patch('requests.get', side_effect=requests.ConnectionError) as get:
            self.assertEqual(world_clock_weather()['cities'], {})
            world_clock_weather()
        self.assertEqual(get.call_count, 2)


@override_settings(CACHES=LOCMEM)
class WorldClockPageTests(TestCase):
    def setUp(self):
        cache.clear()
        owner = User.objects.create_user('owner', password='pw', is_staff=True, is_superuser=True)
        self.client.force_login(owner)

    def test_page_frames_from_same_origin_with_weather(self):
        rows = [_row(code=0) for _ in WORLD_CLOCK_CITIES]
        with mock.patch('requests.get', return_value=_response(rows)):
            resp = self.client.get(reverse('world_clock') + '?embed=1')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp['X-Frame-Options'], 'SAMEORIGIN')
        self.assertContains(resp, 'id="wx-data"')
        self.assertContains(resp, '"Asia/Dubai"')
        self.assertContains(resp, 'body{background:transparent}')
        self.assertNotContains(resp, 'Plan a call time')

    def test_dashboard_embeds_the_clock(self):
        with mock.patch('requests.get', side_effect=requests.ConnectionError):
            resp = self.client.get(reverse('dashboard'))
        self.assertContains(resp, reverse('world_clock') + '?embed=1')
        # The clock replaced the headline figures; Quick Actions links to it.
        self.assertNotContains(resp, 'home-stat')
        self.assertContains(resp, 'World Clock</a>')
        # No sidebar here: its links open from "All modules"
        self.assertContains(resp, '<body class="layout-top">')
        self.assertContains(resp, 'id="modulesBtn"')

    def test_needs_login(self):
        self.client.logout()
        self.assertEqual(self.client.get(reverse('world_clock')).status_code, 302)


FX_BODY = {'result': 'success', 'time_last_update_unix': 1793318551,
           'rates': {'INR': 1, 'USD': 0.0105, 'AED': 0.0385, 'XYZ': 9.9}}


@override_settings(CACHES=LOCMEM)
class CurrencyConverterTests(TestCase):
    def setUp(self):
        cache.clear()

    def test_keeps_listed_currencies_and_caches(self):
        with mock.patch('requests.get', return_value=_response(FX_BODY)) as get:
            data = currency_rates()
            currency_rates()
        self.assertEqual(get.call_count, 1)
        self.assertEqual(data['rates'], {'INR': 1, 'USD': 0.0105, 'AED': 0.0385})
        self.assertTrue(data['updatedAt'].startswith('2026-10-30'))

    def test_failure_gives_empty_and_is_not_cached(self):
        with mock.patch('requests.get', return_value=_response({'result': 'error', 'error-type': 'unsupported-code'})) as get:
            self.assertEqual(currency_rates()['rates'], {})
            currency_rates()
        self.assertEqual(get.call_count, 2)

    def test_dashboard_shows_converter(self):
        owner = User.objects.create_user('fxowner', password='pw', is_staff=True, is_superuser=True)
        self.client.force_login(owner)
        with mock.patch('requests.get', return_value=_response(FX_BODY)):
            resp = self.client.get(reverse('dashboard'))
        self.assertContains(resp, 'Currency Converter')
        self.assertContains(resp, 'id="fx-data"')
        self.assertContains(resp, '<option value="AED">AED')
        self.assertNotContains(resp, '<option value="SAR">')  # not in the feed: not offered
