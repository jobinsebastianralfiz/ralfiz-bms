// Weather Station - SOLUTION (lesson 1.12)
// Run with: dart run bin/main.dart
import 'dart:async';

/// The fake sensor sends this value when it glitches.
const glitch = -999.0;

/// A lazy stream of Celsius readings, one every 200 ms.
Stream<double> sensor() async* {
  const readings = [28.0, 29.5, glitch, 33.2, 31.0, 35.8, 30.1, 36.4];
  for (final c in readings) {
    await Future.delayed(const Duration(milliseconds: 200));
    yield c;
  }
}

/// Drops glitches and converts Celsius to Fahrenheit.
Stream<double> cleanFahrenheit(Stream<double> celsius) =>
    celsius.where((c) => c != glitch).map((c) => c * 9 / 5 + 32);

/// Sends alerts to any number of listeners.
class AlertCenter {
  final _controller = StreamController<String>.broadcast();

  Stream<String> get alerts => _controller.stream;

  void raise(String message) => _controller.add(message);

  Future<void> close() => _controller.close();
}

Future<void> main() async {
  final center = AlertCenter();
  center.alerts.listen((a) => print('Phone: $a'));
  final watchSub = center.alerts.listen((a) => print('Watch: $a'));

  // Part 1: await for over a transformed stream, first five clean readings.
  var count = 0;
  await for (final f in cleanFahrenheit(sensor()).take(5)) {
    count++;
    final text = f.toStringAsFixed(1);
    print('Reading $count: $text F');
    if (f > 91) center.raise('Hot! $text F');
  }

  // Part 2: the watch stops listening; only the phone gets the next alert.
  // Alerts are delivered asynchronously, so give the last one a moment first.
  await Future.delayed(Duration.zero);
  await watchSub.cancel();
  print('Watch unpaired');

  // Part 3: methods that return a Future need the stream to finish.
  final all = await cleanFahrenheit(sensor()).toList();
  final n = all.length;
  final maxF = all.reduce((a, b) => a > b ? a : b).toStringAsFixed(1);
  print('Max of $n readings: $maxF F');
  center.raise('Daily max $maxF F');

  // Part 4: listen to an endless stream and cancel it.
  final ticker = Stream.periodic(
    const Duration(milliseconds: 250),
    (i) => i + 1,
  );
  final tickSub = ticker.listen((t) => print('Tick $t'));
  await Future.delayed(const Duration(milliseconds: 1100));
  await tickSub.cancel();
  print('Ticker cancelled');

  // Part 5: close the controller so listeners get their done event.
  await center.close();
  print('Station closed');
}
