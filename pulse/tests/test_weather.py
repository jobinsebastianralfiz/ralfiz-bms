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
    'weather': [{'description': 'light rain'}],
    'main': {'temp': 29.4, 'feels_like': 33.1, 'humidity': 84},
    'wind': {'speed': 3.5},
}


@override_settings(OPENWEATHER_API_KEY='k', PULSE_WEATHER_CITY='Kochi,IN')
class WeatherToolTests(TestCase):
    def test_maps_openweather_payload(self):
        with mock.patch('requests.get', return_value=FakeResponse(200, SAMPLE)) as get:
            result = tools.get_weather(owner_scope())
        self.assertEqual(result['city'], 'Kochi')
        self.assertEqual(result['description'], 'light rain')
        self.assertEqual(result['temp_c'], 29.4)
        self.assertEqual(result['humidity_pct'], 84)
        self.assertEqual(result['wind_kmh'], 12.6)  # 3.5 m/s
        self.assertEqual(get.call_args.kwargs['params']['q'], 'Kochi,IN')

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
