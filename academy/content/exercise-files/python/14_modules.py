"""Modules, packages & the standard library: the runnable examples from lesson 3.3 of the Complete Python Tutorial.

Run it with:  python3 14_modules.py
Then change the code and run it again."""

# ----------------------------------------------------------------------
# imports.py
# ----------------------------------------------------------------------
import math                         # import the whole module
from random import choice, randint  # import specific names
import statistics as stats          # alias
from datetime import date

print(math.sqrt(144), math.ceil(4.2), math.floor(4.8), math.pi)
print(choice(["Kochi", "Kozhikode", "Thrissur"]), randint(1, 6))
print(stats.mean([72, 88, 95]), stats.median([72, 88, 95, 61]))
print(date.today().year >= 2024)

# ----------------------------------------------------------------------
# stdlib_tour.py
# ----------------------------------------------------------------------
import random, string, os, sys, uuid, hashlib
from collections import Counter, defaultdict, namedtuple, deque
from itertools import combinations, permutations, groupby, islice

# random + string: generate an OTP and a coupon code
print("OTP:", "".join(random.choices(string.digits, k=6)))
print("Coupon:", "".join(random.choices(string.ascii_uppercase + string.digits, k=8)))

# uuid: unique IDs; hashlib: fingerprints (NOT for passwords — use bcrypt/argon2)
print(uuid.uuid4())
print(hashlib.sha256(b"ralfiz").hexdigest()[:16])

# namedtuple: lightweight record
Point = namedtuple("Point", ["lat", "lng"])
p = Point(10.97, 76.22)
print(p.lat, p)

# deque: fast append/pop from both ends (queues)
queue = deque(["token-1", "token-2"])
queue.append("token-3"); print(queue.popleft(), list(queue))

# itertools
print(list(combinations(["A", "B", "C"], 2)))
print(len(list(permutations(range(4)))))
sales = [("Mon", 5), ("Mon", 3), ("Tue", 7)]
for day, rows in groupby(sales, key=lambda r: r[0]):
    print(day, sum(qty for _, qty in rows))

print(sys.version.split()[0], os.sep)
