import 'package:flutter_test/flutter_test.dart';
import 'package:shopping_cart/main.dart';

void main() {
  late CartModel cart;

  setUp(() => cart = CartModel());

  test('starts empty', () {
    expect(cart.count, 0);
    expect(cart.total, 0);
  });

  test('add updates count and total and notifies listeners', () {
    var calls = 0;
    cart.addListener(() => calls++);
    cart.add(catalog[0]); // Canvas Tote 499
    cart.add(catalog[1]); // Steel Bottle 799
    expect(cart.count, 2);
    expect(cart.total, 1298);
    expect(calls, 2);
  });

  test('adding the same product twice is ignored', () {
    cart.add(catalog[0]);
    cart.add(catalog[0]);
    expect(cart.count, 1);
  });

  test('remove and clear', () {
    cart.add(catalog[0]);
    cart.add(catalog[2]);
    cart.remove(catalog[0]);
    expect(cart.items.single.name, 'Desk Lamp');
    cart.clear();
    expect(cart.items, isEmpty);
  });

  test('items cannot be changed from outside the model', () {
    expect(() => cart.items.add(catalog[0]), throwsUnsupportedError);
  });
}
