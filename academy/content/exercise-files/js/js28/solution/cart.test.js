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

  it('rejects zero, negative and fractional quantities', () => {
    expect(() => cart.add(pen, 0)).toThrow(CartError);
    expect(() => cart.add(pen, -1)).toThrow('Invalid quantity');
    expect(() => cart.add(pen, 1.5)).toThrow(/Invalid quantity: 1\.5/);
    expect(cart.count).toBe(0);
  });

  it('does not allow more than the stock', () => {
    cart.add(bag, 2);
    expect(() => cart.add(bag)).toThrow('Only 2 Laptop bag in stock');
    expect(cart.count).toBe(2);
  });

  it('adding the same product twice adds the quantities', () => {
    cart.add(pen, 2);
    cart.add(pen, 3);
    expect(cart.count).toBe(5);
    expect(cart.items()).toHaveLength(1);
  });

  it('removes a product', () => {
    cart.add(pen);
    cart.add(bag);
    cart.remove('PEN');
    expect(cart.items().map(i => i.sku)).toEqual(['BAG']);
  });
});

describe('totals', () => {
  it('adds 18% GST to the subtotal', () => {
    const cart = createCart();
    cart.add(pen, 5);
    cart.add(bag);
    expect(cart.totals()).toEqual({ subtotal: 1350, discount: 0, tax: 243, total: 1593 });
  });

  it('rounds money to 2 decimals', () => {
    const cart = createCart();
    cart.add(lamp, 3);
    const { subtotal, total } = cart.totals();
    expect(subtotal).toBeCloseTo(7499.97, 2);
    expect(total).toBeCloseTo(8849.96, 2);
  });

  it('caps a percentage coupon at its max', () => {
    const cart = createCart();
    cart.add(bag, 2);
    cart.applyCoupon({ code: 'SAVE50', percent: 50, max: 500 });
    expect(cart.totals()).toMatchObject({ subtotal: 2500, discount: 500 });
  });
});

describe('coupons and time', () => {
  const diwali = { code: 'DIWALI', percent: 10, expires: new Date('2026-09-30T23:59:59Z') };

  it('rejects an expired coupon (injected clock)', () => {
    const cart = createCart({ now: () => new Date('2026-10-01T00:00:00Z') });
    expect(() => cart.applyCoupon(diwali)).toThrow('Coupon DIWALI has expired');
  });

  describe('with fake system time', () => {
    beforeEach(() => vi.useFakeTimers());
    afterEach(() => vi.useRealTimers());

    it('accepts the coupon before it expires', () => {
      vi.setSystemTime(new Date('2026-09-28T10:00:00Z'));
      const cart = createCart();
      cart.add(pen, 10);
      cart.applyCoupon(diwali);
      expect(cart.totals().discount).toBe(20);
    });

    it('rejects it after the sale', () => {
      vi.setSystemTime(new Date('2026-11-15T00:00:00Z'));
      expect(() => createCart().applyCoupon(diwali)).toThrow(/expired/);
    });
  });
});

describe('checkout', () => {
  it('charges the total in INR and empties the cart', async () => {
    const payments = { charge: vi.fn().mockResolvedValue({ id: 'PAY-1' }) };
    const cart = createCart();
    cart.add(pen, 5);
    await expect(cart.checkout(payments)).resolves.toEqual({ id: 'PAY-1', total: 118 });
    expect(payments.charge).toHaveBeenCalledTimes(1);
    expect(payments.charge).toHaveBeenCalledWith(118, 'INR');
    expect(cart.count).toBe(0);
  });

  it('wraps payment failures and keeps the cart', async () => {
    const payments = { charge: vi.fn().mockRejectedValue(new Error('card declined')) };
    const cart = createCart();
    cart.add(pen, 5);
    const err = await cart.checkout(payments).catch(e => e);
    expect(err).toBeInstanceOf(CartError);
    expect(err.message).toBe('Payment failed');
    expect(err.cause.message).toBe('card declined');
    expect(cart.count).toBe(5);
  });

  it('refuses an empty cart without charging', async () => {
    const payments = { charge: vi.fn() };
    await expect(createCart().checkout(payments)).rejects.toThrow('Cart is empty');
    expect(payments.charge).not.toHaveBeenCalled();
  });

  it('works with a spy on a real payments object', async () => {
    const payments = { async charge(amount) { return { id: `LIVE-${amount}` }; } };
    const spy = vi.spyOn(payments, 'charge');
    const cart = createCart();
    cart.add(bag);
    const receipt = await cart.checkout(payments);
    expect(spy).toHaveBeenCalledOnce();
    expect(receipt.id).toBe('LIVE-1475');
    spy.mockRestore();
  });
});

describe('debounce', () => {
  beforeEach(() => vi.useFakeTimers());
  afterEach(() => vi.useRealTimers());

  it('calls once after the quiet period', () => {
    const save = vi.fn();
    const autosave = debounce(save, 300);
    autosave('R');
    autosave('Ra');
    autosave('Ralfiz');
    vi.advanceTimersByTime(299);
    expect(save).not.toHaveBeenCalled();
    vi.advanceTimersByTime(1);
    expect(save).toHaveBeenCalledOnce();
    expect(save).toHaveBeenCalledWith('Ralfiz');
  });
});