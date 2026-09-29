import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { createCart, debounce, CartError } from './cart.js';

const pen = { sku: 'PEN', title: 'Gel pen', price: 20, stock: 50 };
const bag = { sku: 'BAG', title: 'Laptop bag', price: 1250, stock: 2 };
const lamp = { sku: 'LAMP', title: 'Desk lamp', price: 2499.99, stock: 5 };

describe('adding items', () => {
  let cart;
  beforeEach(() => {
    cart = createCart();
  });

  it('starts empty', () => {
    expect(cart.count).toBe(0);
    expect(cart.items()).toEqual([]);
  });

  it('adds a product with a quantity', () => {
    cart.add(pen, 3);
    expect(cart.items()).toEqual([{ sku: 'PEN', title: 'Gel pen', qty: 3, lineTotal: 60 }]);
  });

  // TODO(1): quantities 0, -1 and 1.5 throw a CartError mentioning "Invalid quantity"
  it.todo('rejects zero, negative and fractional quantities');
  // TODO(2): adding 2 bags works, a third throws "Only 2 Laptop bag in stock"
  it.todo('does not allow more than the stock');
  // TODO(3): add pen 2, then pen 3: count should be 5 (this finds a bug in cart.js)
  it.todo('adding the same product twice adds the quantities');
});

describe('totals', () => {
  it('adds 18% GST to the subtotal', () => {
    const cart = createCart();
    cart.add(pen, 5);
    cart.add(bag);
    expect(cart.totals()).toEqual({ subtotal: 1350, discount: 0, tax: 243, total: 1593 });
  });

  // TODO(4): 3 lamps: subtotal close to 7499.97 and total close to 8849.96 (toBeCloseTo)
  it.todo('rounds money to 2 decimals');
  // TODO(5): TDD. 2 bags + { percent: 50, max: 500 }: discount is 500. Watch it fail first.
  it.todo('caps a percentage coupon at its max');
});

describe('coupons and time', () => {
  // TODO(6): inject now: () => new Date('2026-10-01T00:00:00Z') and expect a coupon that
  // expired on 2026-09-30 to throw "has expired". Then write a second test with
  // vi.useFakeTimers() + vi.setSystemTime() and no injected clock.
  it.todo('rejects an expired coupon');
});

describe('checkout', () => {
  // TODO(7): payments.charge = vi.fn().mockResolvedValue({ id: 'PAY-1' }).
  // Expect { id: 'PAY-1', total: 118 } for 5 pens, charge called once with (118, 'INR'),
  // and an empty cart afterwards. Then test mockRejectedValue: CartError, err.cause,
  // and the cart is kept.
  it.todo('charges the total in INR and empties the cart');
  it.todo('wraps payment failures and keeps the cart');
});

describe('debounce', () => {
  // TODO(8): with fake timers, three quick calls run the function once, with the
  // last arguments, only after 300 ms.
  it.todo('calls once after the quiet period');
});

// These imports are used by the TODO tests you will write.
void [vi, afterEach, CartError, debounce, lamp];