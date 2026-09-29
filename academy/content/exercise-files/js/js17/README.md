# js17 · Ralfiz Bank and Library (classes in depth)

Build two small object models with modern classes.

## Run

    cd javascript/js17/start
    node index.js

You need Node.js 22 or newer. There are no dependencies.

## Part 1: Ralfiz Bank
- BankAccount with private #balance and #history
- deposit(amount) and withdraw(amount): positive integers only (TypeError otherwise);
  a withdrawal larger than the balance throws a RangeError; both return this
- getters: balance and statement (a copy of the history)
- SavingsAccount extends BankAccount with an annual rate and addMonthlyInterest()

## Part 2: Library (composition)
- Book: private #onLoan, available getter, checkOut(), checkIn()
- Member: private #loans Map (isbn to due day), canBorrow(), addLoan(), removeLoan()
- Library: HAS books, members and a fine policy function passed to the constructor.
  lend() checks everything before changing any state.

## Acceptance criteria
- Balance: 23800 after depositing 25000 and withdrawing 1200
- Withdrawing 99999 prints "RangeError: Insufficient funds: balance is 23800"
- After monthly interest at 4% the balance is 23879
- Lending an already borrowed book, or going over a member's limit, prints a "Refused:" line
- Returning a book 6 days late with perDay(5) prints a fine of 30; the capped policy never exceeds 50
- acc.#balance is not reachable from outside the class (try it: it is a SyntaxError)
