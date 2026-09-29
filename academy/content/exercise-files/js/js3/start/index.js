// Lesson 1.1: Shop Bill, version 1
// Run with: node index.js

// TODO(1): declare the fixed configuration with const and UPPER_SNAKE_CASE:
//          SHOP_NAME = 'Ralfiz Store', GST_RATE = 0.18,
//          MEMBER_DISCOUNT_RATE = 0.1
const SHOP_NAME = 'Shop name here';

const customerName = 'Asha';
const isMember = true;
const couponCode = null; // no coupon on this bill

// TODO(2): declare price and quantity constants for three lines:
//          Notebook 120 x 3, Gel pen 25 x 4, File folder 60 x 2
//          then compute subtotal from them.
const subtotal = 0;

// TODO(3): compute discount (members only, use the ? : operator),
//          taxable (subtotal - discount), gst and total.
const discount = 0;
const total = 0;

console.log(`${SHOP_NAME}: bill for ${customerName}`);
console.log('Subtotal:', subtotal);
console.log('Member discount:', discount);
console.log('Total:', total);

// TODO(4): print a typeof report for:
//          customerName, isMember, couponCode,
//          invoiceNo (make it the BigInt 20260000001042n) and
//          trackingId (make it Symbol('tracking'))

// TODO(5): make a const array items with the three item names,
//          push 'Sticky notes' and print items and items.length.
//          Then add the line  items = [];  run the file, read the
//          TypeError, and delete that line again.
