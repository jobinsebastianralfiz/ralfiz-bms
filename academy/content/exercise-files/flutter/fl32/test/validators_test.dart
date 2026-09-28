import 'package:flutter_test/flutter_test.dart';
import 'package:event_registration/main.dart';

void main() {
  group('validateName', () {
    test('rejects null and blank values', () {
      expect(validateName(null), 'Enter your name');
      expect(validateName('   '), 'Enter your name');
    });
    test('accepts a real name', () => expect(validateName('Asha Nair'), isNull));
  });

  group('validateEmail', () {
    test('rejects empty', () => expect(validateEmail(''), 'Enter your email'));
    test('rejects a missing domain', () {
      expect(validateEmail('asha@'), 'Enter a valid email');
      expect(validateEmail('asha.example.com'), 'Enter a valid email');
    });
    test('trims and accepts a normal address', () {
      expect(validateEmail(' asha@example.com '), isNull);
    });
  });

  group('validatePhone', () {
    test('needs exactly 10 digits', () {
      expect(validatePhone('98765'), 'Enter a 10-digit phone number');
      expect(validatePhone(null), 'Enter a 10-digit phone number');
      expect(validatePhone('9876543210'), isNull);
    });
  });
}
