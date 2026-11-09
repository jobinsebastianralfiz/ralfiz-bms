"""Classes & objects: the runnable examples from lesson 4.1 of the Complete Python Tutorial.

Run it with:  python3 17_classes.py
Then change the code and run it again."""

# ----------------------------------------------------------------------
# bank_account.py
# ----------------------------------------------------------------------
class BankAccount:
    bank_name = "Ralfiz Co-op Bank"          # CLASS attribute: shared by all accounts

    def __init__(self, owner, balance=0):     # constructor: runs when an object is created
        self.owner = owner                    # INSTANCE attributes: unique per object
        self.balance = balance
        self.transactions = []

    def deposit(self, amount):
        if amount <= 0:
            raise ValueError("Deposit must be positive")
        self.balance += amount
        self.transactions.append(("deposit", amount))
        return self.balance

    def withdraw(self, amount):
        if amount > self.balance:
            raise ValueError("Insufficient balance")
        self.balance -= amount
        self.transactions.append(("withdraw", amount))
        return self.balance

    def statement(self):
        lines = [f"{self.owner} @ {self.bank_name}"]
        for kind, amt in self.transactions:
            lines.append(f"  {kind:<9} ₹{amt:>8,}")
        lines.append(f"  Balance   ₹{self.balance:>8,}")
        return "\n".join(lines)

anu = BankAccount("Anu", 5000)           # create objects
rahul = BankAccount("Rahul")

anu.deposit(2500)
anu.withdraw(1200)
rahul.deposit(10000)

print(anu.statement())
print(rahul.balance, rahul.bank_name)
print(isinstance(anu, BankAccount))

# ----------------------------------------------------------------------
# class_vs_instance.py
# ----------------------------------------------------------------------
class Intern:
    company = "Ralfiz Technologies"     # shared
    count = 0                           # shared counter

    def __init__(self, name):
        self.name = name                # per object
        Intern.count += 1               # update the shared value via the class

a = Intern("Anu")
b = Intern("Rahul")
print(a.company, b.company, Intern.count)

Intern.company = "Ralfiz Tech"          # change for everyone
print(a.company, b.company)

# ----------------------------------------------------------------------
# str_repr.py
# ----------------------------------------------------------------------
class Product:
    def __init__(self, name, price):
        self.name = name
        self.price = price

    def __str__(self):                 # for end users: print(obj), str(obj)
        return f"{self.name} — ₹{self.price:,}"

    def __repr__(self):                # for developers: debugging, lists, the shell
        return f"Product(name={self.name!r}, price={self.price})"

p = Product("Analog Watch", 2450)
print(p)
print([p])
print(repr(p))
