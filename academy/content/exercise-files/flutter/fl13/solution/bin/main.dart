// Weather Fetcher - SOLUTION (lesson 1.11)
// Run with: dart run bin/main.dart
import 'dart:async';

/// Thrown when the fake service has no data for a city.
class CityNotFoundException implements Exception {
  CityNotFoundException(this.city);
  final String city;

  @override
  String toString() => 'No weather data for $city';
}

/// A light data type: a record with named fields.
typedef Weather = ({String city, double tempC, String sky});

/// Fake server data: (temperature, sky, delay in milliseconds).
const _fakeData = <String, (double, String, int)>{
  'Kochi': (29.5, 'Humid', 800),
  'Dubai': (38.0, 'Sunny', 1200),
  'Toronto': (12.0, 'Cloudy', 1000),
  'London': (15.5, 'Rain', 3000), // slow on purpose
};

/// Simulates a network call that takes some time.
Future<Weather> fetchWeather(String city) async {
  final entry = _fakeData[city];
  final delayMs = entry?.$3 ?? 500;
  await Future.delayed(Duration(milliseconds: delayMs));
  if (entry == null) throw CityNotFoundException(city);
  final (temp, sky, _) = entry;
  return (city: city, tempC: temp, sky: sky);
}

/// Turns a Weather record into one line of text.
String describe(Weather w) {
  final (:city, :tempC, :sky) = w;
  final temp = tempC.toStringAsFixed(1);
  return '$city: $temp C, $sky';
}

Future<void> main() async {
  final watch = Stopwatch()..start();

  // 1. One city
  final kochi = await fetchWeather('Kochi');
  print(describe(kochi));

  // 2. Two cities, one after the other
  watch.reset();
  for (final city in ['Dubai', 'Toronto']) {
    print(describe(await fetchWeather(city)));
  }
  final sequentialMs = watch.elapsedMilliseconds;
  print('Sequential: $sequentialMs ms');

  // 3. The same two cities in parallel
  watch.reset();
  final both = await Future.wait([
    fetchWeather('Dubai'),
    fetchWeather('Toronto'),
  ]);
  both.map(describe).forEach(print);
  final parallelMs = watch.elapsedMilliseconds;
  print('Parallel: $parallelMs ms');

  // 4. Unknown city
  try {
    await fetchWeather('Atlantis');
  } on CityNotFoundException catch (e) {
    print('Error: $e');
  }

  // 5. Slow city with a timeout
  try {
    final london = await fetchWeather('London')
        .timeout(const Duration(seconds: 2));
    print(describe(london));
  } on TimeoutException {
    print('London timed out after 2 s');
  } finally {
    print('Done');
  }
}
