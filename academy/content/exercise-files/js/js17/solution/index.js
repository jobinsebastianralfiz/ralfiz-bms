// js17 · Ralfiz Bank and Library (solution)
// Run: node index.js

// ---------- Part 1: Ralfiz Bank ----------
class BankAccount {
  #balance = 0;
  #history = [];

  constructor(owner) {
    this.owner = owner;
  }

  deposit(amount) {
    this.#check(amount);
    this.#balance += amount;
    this.#history.push({ type: 'deposit', amount });
    return this;
  }

  withdraw(amount) {
    this.#check(amount);
    if (amount > this.#balance) {
      throw new RangeError(`Insufficient funds: balance is ${this.#balance}`);
    }
    this.#balance -= amount;
    this.#history.push({ type: 'withdraw', amount });
    return this;
  }

  get balance() {
    return this.#balance;
  }

  get statement() {
    return this.#history.map((entry) => ({ ...entry }));
  }

  #check(amount) {
    if (!Number.isInteger(amount) || amount <= 0) {
      throw new TypeError(`Amount must be a positive integer, got ${amount}`);
    }
  }
}

class SavingsAccount extends BankAccount {
  constructor(owner, annualRate) {
    super(owner);
    this.annualRate = annualRate;
  }

  addMonthlyInterest() {
    const interest = Math.round((this.balance * this.annualRate) / 12);
    if (interest > 0) this.deposit(interest);
    return interest;
  }
}

// ---------- Part 2: Library (composition) ----------
class Book {
  #onLoan = false;

  constructor(isbn, title) {
    this.isbn = isbn;
    this.title = title;
  }

  get available() {
    return !this.#onLoan;
  }

  checkOut() {
    if (this.#onLoan) throw new Error(`"${this.title}" is already on loan`);
    this.#onLoan = true;
  }

  checkIn() {
    this.#onLoan = false;
  }
}

class Member {
  #loans = new Map();

  constructor(id, name, limit = 2) {
    Object.assign(this, { id, name, limit });
  }

  canBorrow() {
    return this.#loans.size < this.limit;
  }

  addLoan(isbn, dueDay) {
    this.#loans.set(isbn, dueDay);
  }

  removeLoan(isbn) {
    if (!this.#loans.has(isbn)) throw new Error(`${this.name} does not have ${isbn}`);
    const due = this.#loans.get(isbn);
    this.#loans.delete(isbn);
    return due;
  }
}

const perDay = (rupees) => (daysLate) => Math.max(0, daysLate) * rupees;
const capped = (policy, max) => (daysLate) => Math.min(policy(daysLate), max);

class Library {
  #books = new Map();
  #members = new Map();

  constructor({ loanDays = 14, fine = perDay(5) } = {}) {
    this.loanDays = loanDays;
    this.fine = fine;
  }

  add(...items) {
    for (const item of items) {
      if (item instanceof Book) this.#books.set(item.isbn, item);
      else if (item instanceof Member) this.#members.set(item.id, item);
      else throw new TypeError('Only books and members can be added');
    }
    return this;
  }

  lend(isbn, memberId, today) {
    const book = this.#find(this.#books, isbn, 'Book');
    const member = this.#find(this.#members, memberId, 'Member');
    if (!book.available) throw new Error(`"${book.title}" is already on loan`);
    if (!member.canBorrow()) {
      throw new Error(`${member.name} has reached their loan limit (${member.limit})`);
    }
    book.checkOut();
    member.addLoan(isbn, today + this.loanDays);
    return `${member.name} borrowed "${book.title}" (due day ${today + this.loanDays})`;
  }

  giveBack(isbn, memberId, today) {
    const member = this.#find(this.#members, memberId, 'Member');
    const due = member.removeLoan(isbn);
    this.#find(this.#books, isbn, 'Book').checkIn();
    return this.fine(today - due);
  }

  #find(map, key, kind) {
    const item = map.get(key);
    if (!item) throw new Error(`${kind} ${key} not found`);
    return item;
  }
}

// ---------- Demo ----------
const tryIt = (label, fn) => {
  try {
    console.log(label, fn());
  } catch (err) {
    console.log(`Refused: ${err.name}: ${err.message}`);
  }
};

console.log('--- Ralfiz Bank ---');
const acc = new BankAccount('Anu').deposit(25000).withdraw(1200);
console.log('Balance:', acc.balance);
tryIt('Withdraw 99999:', () => acc.withdraw(99999));
tryIt('Deposit -5:', () => acc.deposit(-5));
console.log('Statement:', acc.statement);

const savings = new SavingsAccount('Rahul', 0.04).deposit(23800);
console.log('Interest:', savings.addMonthlyInterest(), '| After interest:', savings.balance);
console.log('savings instanceof BankAccount:', savings instanceof BankAccount);

console.log('--- Library ---');
const lib = new Library({ fine: capped(perDay(5), 50) }).add(
  new Book('B1', 'Clean Code'),
  new Book('B2', 'Eloquent JavaScript'),
  new Book('B3', 'Refactoring'),
  new Member('M1', 'Anu'),
  new Member('M2', 'Rahul', 1),
);
tryIt('Lend B1 to Anu:', () => lib.lend('B1', 'M1', 1));
tryIt('Lend B1 to Rahul:', () => lib.lend('B1', 'M2', 2));
tryIt('Lend B2 to Rahul:', () => lib.lend('B2', 'M2', 3));
tryIt('Lend B3 to Rahul:', () => lib.lend('B3', 'M2', 4));
console.log('Anu returns B1 on day 21, fine:', lib.giveBack('B1', 'M1', 21));
console.log('Rahul returns B2 on day 40, fine (capped):', lib.giveBack('B2', 'M2', 40));

const strict = new Library({ fine: perDay(5) }).add(new Book('B9', 'SICP'), new Member('M9', 'Fathima'));
strict.lend('B9', 'M9', 1);
console.log('Uncapped fine 25 days late:', strict.giveBack('B9', 'M9', 40));
