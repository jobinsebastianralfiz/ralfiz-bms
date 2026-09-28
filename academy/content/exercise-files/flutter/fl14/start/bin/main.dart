// Weather Station - STARTER (lesson 1.12)
// Run with: dart run bin/main.dart
// This file compiles as it is. Fill in TODO(1) to TODO(7).
import 'dart:async';

/// The fake sensor sends this value when it glitches.
const glitch = -999.0;

/// A lazy stream of Celsius readings, one every 200 ms.
Stream<double> sensor() async* {
  const readings = [28.0, 29.5, glitch, 33.2, 31.0, 35.8, 30.1, 36.4];
  // TODO(1): Loop over readings. For each one, wait 200 ms with
  //   Future.delayed, then yield the value.
  yield readings.first;
}

/// Drops glitches and converts Celsius to Fahrenheit (C * 9 / 5 + 32).
Stream<double> cleanFahrenheit(Stream<double> celsius) {
  // TODO(2): Use where to drop glitch values and map to convert.
  return celsius;
}

/// Sends alerts to any number of listeners.
class AlertCenter {
  // TODO(3): Create a private BROADCAST StreamController<String>.
  //   Expose its stream in the alerts getter, add messages in raise,
  //   and close the controller in close.
  Stream<String> get alerts => const Stream.empty();

  void raise(String message) {}

  Future<void> close() async {}
}

Future<void> main() async {
  final center = AlertCenter();
  center.alerts.listen((a) => print('Phone: $a'));
  // TODO(4): Listen a second time for the watch ("Watch: <alert>") and keep
  //   the StreamSubscription in a variable named watchSub.

  // TODO(5): Use await for over cleanFahrenheit(sensor()).take(5).
  //   Print "Reading <n>: <value with 1 decimal> F" and call center.raise
  //   with "Hot! <value> F" when the value is above 91.

  // TODO(6): await Future.delayed(Duration.zero) so the last alert arrives,
  //   then cancel watchSub and print "Watch unpaired". Then collect all
  //   clean readings with toList(), print "Max of <n> readings: <max> F"
  //   and raise "Daily max <max> F".

  // TODO(7): Listen to Stream.periodic(250 ms, (i) => i + 1), printing
  //   "Tick <t>". After 1100 ms cancel the subscription and print
  //   "Ticker cancelled". Finally close the center and print "Station closed".
}
