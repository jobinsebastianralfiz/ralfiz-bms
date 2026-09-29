// js17 · Ralfiz Bank and Library
// Run: node index.js

// ---------- Part 1: Ralfiz Bank ----------
class BankAccount {
  // TODO(1): add private fields #balance (starts at 0) and #history (starts as [])

  constructor(owner) {
    this.owner = owner;
  }

  // TODO(2): deposit(amount) and withdraw(amount)
  //   - throw a TypeError when amount is not a positive integer
  //   - withdraw throws a RangeError when amount > balance:
  //       `Insufficient funds: balance is ${balance}`
  //   - push { type: 'deposit' | 'withdraw', amount } to #history
  //   - return this so calls can be chained

  // TODO(3): getters "balance" and "statement" (return a copy of #history)
}

// TODO(4): class SavingsAccount extends BankAccount
//   constructor(owner, annualRate): call super(owner) first
//   addMonthlyInterest(): deposit Math.round(balance * annualRate / 12)
//   and return the interest amount

// ---------- Part 2: Library (composition) ----------
// TODO(5): class Book with isbn and title, a private #onLoan flag,
//   an "available" getter, checkOut() (throws if already on loan) and checkIn()

// TODO(6): class Member with id, name, limit = 2 and a private #loans Map
//   (isbn -> due day), canBorrow(), addLoan(isbn, dueDay), removeLoan(isbn)

// Fine policies are plain functions, passed into the Library
const perDay = (rupees) => (daysLate) => Math.max(0, daysLate) * rupees;
const capped = (policy, max) => (daysLate) => Math.min(policy(daysLate), max);

// TODO(7): class Library
//   constructor({ loanDays = 14, fine = perDay(5) } = {})
//   add(...items), lend(isbn, memberId, today), giveBack(isbn, memberId, today)
//   lend() must check the book and the member before changing anything.
//   giveBack() returns this.fine(today - dueDay).

// ---------- Demo: uncomment as you finish each TODO ----------
const acc = new BankAccount('Anu');
console.log('Owner:', acc.owner);

// acc.deposit(25000).withdraw(1200);
// console.log('Balance:', acc.balance);
// try { acc.withdraw(99999); } catch (err) { console.log(`${err.name}: ${err.message}`); }

// const savings = new SavingsAccount('Rahul', 0.04).deposit(23800);
// console.log('Interest:', savings.addMonthlyInterest(), 'Balance:', savings.balance);

// const lib = new Library({ fine: capped(perDay(5), 50) });
// ...add books and members, lend and return, print the fines

console.log('Starter ran. Work through the TODOs.');
