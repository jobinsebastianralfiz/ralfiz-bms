// Lesson 1.1: Shop Bill, version 1 (solution)
// Run with: node index.js

const SHOP_NAME = 'Ralfiz Store';
const GST_RATE = 0.18;
const MEMBER_DISCOUNT_RATE = 0.1;

const customerName = 'Asha';
const isMember = true;
const couponCode = null; // no coupon on this bill
const invoiceNo = 20260000001042n;
const trackingId = Symbol('tracking');

const notebookPrice = 120;
const notebookQty = 3;
const penPrice = 25;
const penQty = 4;
const folderPrice = 60;
const folderQty = 2;

const subtotal =
  notebookPrice * notebookQty + penPrice * penQty + folderPrice * folderQty;
const discount = isMember ? subtotal * MEMBER_DISCOUNT_RATE : 0;
const taxable = subtotal - discount;
const gst = taxable * GST_RATE;
const total = taxable + gst;

console.log(`${SHOP_NAME}: bill for ${customerName}`);
console.log('Invoice:', invoiceNo);
console.log('Subtotal:', subtotal);
console.log('Member discount:', discount);
console.log('Taxable:', taxable);
// toFixed(2) rounds to 2 decimals for display (lesson 1.4 explains why)
console.log('GST (18%):', gst.toFixed(2));
console.log('Total:', total.toFixed(2));
console.log('Coupon:', couponCode === null ? 'none' : couponCode);

console.log('\n--- typeof report ---');
console.log('customerName:', typeof customerName);
console.log('isMember:', typeof isMember);
console.log('couponCode:', typeof couponCode, '(null: a famous quirk)');
console.log('invoiceNo:', typeof invoiceNo);
console.log('trackingId:', typeof trackingId);

console.log('\n--- const is not immutable ---');
const items = ['Notebook', 'Gel pen', 'File folder'];
items.push('Sticky notes'); // allowed: changes the array, not the binding
console.log(items, 'length:', items.length);
// items = []; // TypeError: Assignment to constant variable.
