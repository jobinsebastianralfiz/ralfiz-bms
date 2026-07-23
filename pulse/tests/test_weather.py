"""get_weather: mapping, defaults, and failure shapes -- no live HTTP."""

from unittest import mock

from django.test import TestCase, override_settings
from rest_framework.exceptions import PermissionDenied

from pulse import tools
from pulse.scoping import PulseScope


def owner_scope():
    return PulseScope(user=None, employee=None, can_query_business=True)


class FakeResponse:
    def __init__(self, status_code, payload):
        self.status_code = status_code
        self._payload = payload

    def json(self):
        return self._payload


SAMPLE = {
    'name': 'Kochi',
    'weather': [{'description': 'light rain', 'main': 'Rain', 'icon': '10n'}],
    'main': {'temp': 29.4, 'feels_like': 33.1, 'humidity': 84},
    'wind': {'speed': 3.5},
}

FORECAST = {
    'city': {'timezone': 19800},   # IST = UTC+5:30
    'list': [
        # dt 39900 UTC + 19800 = 59700s into the day = 16:35 local.
        {'dt': 39900, 'main': {'temp': 31.2}, 'pop': 0.06,
         'weather': [{'main': 'Clouds', 'icon': '02d'}]},
        {'dt': 50700, 'main': {'temp': 26.4}, 'pop': 0.44,
         'weather': [{'main': 'Rain', 'icon': '10n'}]},
    ],
}


def two_call_mock():
    """requests.get answers current weather first, then the forecast."""
    return mock.patch(
        'requests.get',
        side_effect=[FakeResponse(200, SAMPLE), FakeResponse(200, FORECAST)],
    )


@override_settings(OPENWEATHER_API_KEY='k', PULSE_WEATHER_CITY='Kochi,IN')
class WeatherToolTests(TestCase):
    def test_maps_openweather_payload(self):
        with two_call_mock() as get:
            result = tools.get_weather(owner_scope())
        self.assertEqual(result['city'], 'Kochi')
        self.assertEqual(result['description'], 'light rain')
        self.assertEqual(result['condition'], 'rain')
        self.assertEqual(result['icon'], '10n')
        self.assertTrue(result['is_night'])
        self.assertEqual(result['temp_c'], 29.4)
        self.assertEqual(result['humidity_pct'], 84)
        self.assertEqual(result['wind_kmh'], 12.6)  # 3.5 m/s
        self.assertEqual(get.call_args_list[0].kwargs['params']['q'], 'Kochi,IN')

    def test_maps_forecast_hours(self):
        with two_call_mock():
            result = tools.get_weather(owner_scope())
        self.assertEqual(len(result['hourly']), 2)
        first = result['hourly'][0]
        self.assertEqual(first['at'], '16:35')
        self.assertEqual(first['temp_c'], 31)
        self.assertEqual(first['condition'], 'clouds')
        self.assertFalse(first['is_night'])
        self.assertEqual(first['pop_pct'], 6)
        self.assertTrue(result['hourly'][1]['is_night'])
        self.assertEqual(result['high_c'], 31)   # max of slots + current
        self.assertEqual(result['low_c'], 26)

    def test_forecast_failure_keeps_current_weather(self):
        import requests
        with mock.patch(
            'requests.get',
            side_effect=[FakeResponse(200, SAMPLE), requests.ConnectionError()],
        ):
            result = tools.get_weather(owner_scope())
        self.assertEqual(result['temp_c'], 29.4)
        self.assertNotIn('hourly', result)

    def test_named_city_overrides_default(self):
        with mock.patch('requests.get', return_value=FakeResponse(200, SAMPLE)) as get:
            tools.get_weather(owner_scope(), city='Mumbai')
        self.assertEqual(get.call_args.kwargs['params']['q'], 'Mumbai')

    def test_unknown_city_is_a_plain_error(self):
        with mock.patch('requests.get', return_value=FakeResponse(404, {})):
            result = tools.get_weather(owner_scope(), city='Atlantis')
        self.assertIn('error', result)

    def test_network_failure_is_a_plain_error(self):
        import requests
        with mock.patch('requests.get', side_effect=requests.ConnectionError):
            result = tools.get_weather(owner_scope())
        self.assertIn('error', result)

    @override_settings(OPENWEATHER_API_KEY='')
    def test_missing_key_names_the_variable(self):
        result = tools.get_weather(owner_scope())
        self.assertIn('OPENWEATHER_API_KEY', result['error'])

    def test_refuses_unprivileged_scope(self):
        scope = PulseScope(user=None, employee=None, can_query_business=False)
        with self.assertRaises(PermissionDenied):
            tools.get_weather(scope)


@override_settings(OPENWEATHER_API_KEY='k', PULSE_WEATHER_CITY='Kochi,IN')
class WeatherEndpointTests(TestCase):
    def setUp(self):
        from django.contrib.auth.models import User
        from django.core.cache import cache
        cache.clear()   # the view caches for 10 minutes; tests must not share
        self.owner = User.objects.create_user('boss', password='x', is_staff=True)
        self.outsider = User.objects.create_user('intern', password='x')

    def test_owner_gets_cached_weather(self):
        self.client.force_login(self.owner)
        with two_call_mock() as get:
            first = self.client.get('/api/pulse/weather/')
            second = self.client.get('/api/pulse/weather/')
        self.assertEqual(first.status_code, 200)
        self.assertEqual(first.json()['city'], 'Kochi')
        self.assertEqual(second.json(), first.json())
        # One current + one forecast call; second page hit served from cache.
        self.assertEqual(get.call_count, 2)

    def test_non_owner_is_refused(self):
        self.client.force_login(self.outsider)
        self.assertEqual(self.client.get('/api/pulse/weather/').status_code, 403)
