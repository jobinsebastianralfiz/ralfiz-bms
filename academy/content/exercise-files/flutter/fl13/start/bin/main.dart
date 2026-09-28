// Weather Fetcher - STARTER (lesson 1.11)
// Run with: dart run bin/main.dart
// This file compiles as it is. Fill in TODO(1) to TODO(6).
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
  // TODO(1): Look up the city in _fakeData.
  //   Wait for its delay (use 500 ms if the city is unknown) with Future.delayed.
  //   Throw CityNotFoundException if the city is unknown.
  //   Otherwise destructure the record and return
  //   (city: city, tempC: temp, sky: sky).
  throw UnimplementedError('fetchWeather');
}

/// Turns a Weather record into one line of text, e.g. "Kochi: 29.5 C, Humid".
String describe(Weather w) {
  // TODO(2): Destructure w with a pattern: final (:city, :tempC, :sky) = w;
  //   Format tempC with one decimal place and return the line.
  return w.city;
}

Future<void> main() async {
  final watch = Stopwatch()..start();

  // TODO(3): Fetch Kochi with await and print describe(...) of the result.

  // TODO(4): Reset the stopwatch. Fetch Dubai, then Toronto, one after the
  //   other in a for loop, printing each. Then print "Sequential: <ms> ms".
  watch.reset();

  // TODO(5): Reset the stopwatch. Fetch Dubai and Toronto together with
  //   Future.wait, print each result, then print "Parallel: <ms> ms".

  // TODO(6): Fetch 'Atlantis' inside try / on CityNotFoundException and print
  //   "Error: <e>". Then fetch 'London' with .timeout(Duration(seconds: 2)),
  //   print "London timed out after 2 s" on TimeoutException and print "Done"
  //   in a finally block.
  print('Elapsed so far: ' + watch.elapsedMilliseconds.toString() + ' ms');
}
