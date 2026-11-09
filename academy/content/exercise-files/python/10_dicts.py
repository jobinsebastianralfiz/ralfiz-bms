"""Dictionaries: the runnable examples from lesson 2.3 of the Complete Python Tutorial.

Run it with:  python3 10_dicts.py
Then change the code and run it again."""

# ----------------------------------------------------------------------
# dict_basics.py
# ----------------------------------------------------------------------
student = {
    "id": 101,
    "name": "Anu",
    "course": "Python Full Stack",
    "skills": ["python", "sql"],
}
print(student["name"])
print(student.get("phone"))                 # None instead of KeyError
print(student.get("phone", "not given"))    # with a default
print("course" in student)                  # checks KEYS

student["phone"] = "9895000001"             # add
student["course"] = "Django Backend"        # update
print(student)
print(len(student))

# ----------------------------------------------------------------------
# dict_loops.py
# ----------------------------------------------------------------------
stock = {"watch": 12, "strap": 40, "clock": 0, "battery": 150}

for item in stock:                        # keys
    print(item, end=" ")
print()
for qty in stock.values():
    print(qty, end=" ")
print()
for item, qty in stock.items():           # most common
    status = "OUT" if qty == 0 else qty
    print(f"{item:<8} {status}")

print(list(stock.keys()))
print(sum(stock.values()), "items in total")

# ----------------------------------------------------------------------
# dict_methods.py
# ----------------------------------------------------------------------
config = {"debug": True, "db": "sqlite"}
config.update({"db": "postgresql", "port": 5432})   # merge/overwrite
print(config)

removed = config.pop("debug")            # remove and return
print(removed, config)

config.setdefault("timezone", "Asia/Kolkata")   # set only if missing
config.setdefault("db", "mysql")                  # ignored: key exists
print(config)

defaults = {"theme": "light", "lang": "en"}
user = {"lang": "ml"}
merged = defaults | user                 # Python 3.9+: right side wins
print(merged)

# ----------------------------------------------------------------------
# count_group.py
# ----------------------------------------------------------------------
payments = ["UPI", "Cash", "UPI", "Card", "UPI", "Cash"]

# Manual counting
counts = {}
for mode in payments:
    counts[mode] = counts.get(mode, 0) + 1
print(counts)

# The standard library does it for you
from collections import Counter, defaultdict
print(Counter(payments).most_common(2))

orders = [("Anu", 1200), ("Rahul", 450), ("Anu", 3100), ("Diya", 980)]
by_customer = defaultdict(list)          # missing keys start as []
for name, amount in orders:
    by_customer[name].append(amount)
print(dict(by_customer))
print({name: sum(a) for name, a in by_customer.items()})

# ----------------------------------------------------------------------
# nested.py
# ----------------------------------------------------------------------
order = {
    "order_id": "ORD-5531",
    "customer": {"name": "Fathima", "phone": "9895000003", "city": "Manjeri"},
    "items": [
        {"sku": "W-101", "name": "Analog Watch", "qty": 1, "price": 2450},
        {"sku": "S-220", "name": "Leather Strap", "qty": 2, "price": 350},
    ],
    "paid": True,
}

print(order["customer"]["city"])
for item in order["items"]:
    print(f"{item['name']}: {item['qty']} × ₹{item['price']}")
total = sum(i["qty"] * i["price"] for i in order["items"])
print("Total:", total)

# Safe deep access when keys might be missing
coupon = order.get("discount", {}).get("code", "NONE")
print("Coupon:", coupon)
