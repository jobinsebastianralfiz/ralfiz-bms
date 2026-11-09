"""Encapsulation, properties & magic methods: the runnable examples from lesson 4.3 of the Complete Python Tutorial.

Run it with:  python3 19_encapsulation.py
Then change the code and run it again."""

# ----------------------------------------------------------------------
# private.py
# ----------------------------------------------------------------------
class Account:
    def __init__(self, pin):
        self._balance = 0          # _single: "internal, please don't touch" (convention)
        self.__pin = pin           # __double: name-mangled to _Account__pin

    def check_pin(self, pin):
        return pin == self.__pin

acc = Account("1234")
print(acc._balance)               # works, but you're breaking the convention
print(acc.check_pin("1234"))
try:
    print(acc.__pin)
except AttributeError as e:
    print("AttributeError:", e)
print(acc._Account__pin)          # still reachable: Python trusts developers

# ----------------------------------------------------------------------
# property.py
# ----------------------------------------------------------------------
class Product:
    def __init__(self, name, price, gst_rate=18):
        self.name = name
        self.price = price            # goes through the setter below
        self.gst_rate = gst_rate

    @property
    def price(self):
        return self._price

    @price.setter
    def price(self, value):
        if value < 0:
            raise ValueError("Price cannot be negative")
        self._price = value

    @property
    def price_with_gst(self):         # computed, read-only attribute
        return round(self._price * (1 + self.gst_rate / 100), 2)

p = Product("Watch", 2450)
print(p.price, p.price_with_gst)      # no () — reads like an attribute
p.price = 2000
print(p.price_with_gst)
try:
    p.price = -10
except ValueError as e:
    print(e)

# ----------------------------------------------------------------------
# class_static.py
# ----------------------------------------------------------------------
from datetime import date

class Student:
    def __init__(self, name, birth_year):
        self.name = name
        self.birth_year = birth_year

    @classmethod
    def from_csv_row(cls, row: str):          # alternative constructor
        name, year = row.split(",")
        return cls(name.strip(), int(year))

    @staticmethod
    def is_valid_name(name: str) -> bool:     # utility: needs neither self nor cls
        return name.replace(" ", "").isalpha()

    def age(self):
        return date.today().year - self.birth_year

s = Student.from_csv_row("Fathima, 2004")
print(s.name, s.age() > 0)
print(Student.is_valid_name("Anu Mathew"), Student.is_valid_name("R2D2"))

# ----------------------------------------------------------------------
# dunder.py
# ----------------------------------------------------------------------
from functools import total_ordering

@total_ordering                                   # fills in <=, >, >= from __eq__ and __lt__
class Money:
    def __init__(self, amount, currency="INR"):
        self.amount = round(amount, 2)
        self.currency = currency

    def __add__(self, other):                     # a + b
        self._check(other)
        return Money(self.amount + other.amount, self.currency)

    def __mul__(self, factor):                    # a * 3
        return Money(self.amount * factor, self.currency)

    def __eq__(self, other):                      # a == b
        return (self.amount, self.currency) == (other.amount, other.currency)

    def __lt__(self, other):                      # a < b  (enables sorting)
        self._check(other)
        return self.amount < other.amount

    def __bool__(self):                           # if money:
        return self.amount != 0

    def __repr__(self):
        return f"Money({self.amount}, {self.currency!r})"

    def __str__(self):
        return f"₹{self.amount:,.2f}" if self.currency == "INR" else f"{self.amount:,.2f} {self.currency}"

    def _check(self, other):
        if self.currency != other.currency:
            raise ValueError("Currency mismatch")

a, b = Money(1500), Money(2450.5)
print(a + b, a * 3, a < b, max(a, b), sorted([b, a]))
print(bool(Money(0)))

class Playlist:
    def __init__(self, *songs):
        self.songs = list(songs)
    def __len__(self):              return len(self.songs)
    def __getitem__(self, i):       return self.songs[i]      # indexing, slicing, for-loops
    def __contains__(self, song):   return song in self.songs

pl = Playlist("Song A", "Song B", "Song C")
print(len(pl), pl[0], pl[-1], "Song B" in pl)
for s in pl:
    print("▶", s)
