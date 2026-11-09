"""Day 1 warm-up: run `python fundamentals.py` and read the output line by line."""
import copy
import functools
import logging
import time
from collections import Counter, defaultdict

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
logger = logging.getLogger(__name__)

# ---------- 1. Mutability: the bug every junior ships once ----------
def add_item_buggy(item, cart=[]):        # default list is created ONCE
    cart.append(item)
    return cart

def add_item(item, cart=None):            # correct pattern
    if cart is None:
        cart = []
    cart.append(item)
    return cart

print(add_item_buggy("watch"), add_item_buggy("strap"))   # ['watch', 'strap'] twice!
print(add_item("watch"), add_item("strap"))               # ['watch'] ['strap']

order = {"id": 1, "items": [{"sku": "W1", "qty": 1}]}
shallow, deep = copy.copy(order), copy.deepcopy(order)
order["items"][0]["qty"] = 5
print(shallow["items"][0]["qty"], deep["items"][0]["qty"])  # 5 1

# ---------- 2. Comprehensions & the collections module ----------
orders = [
    {"id": 1, "customer": "Anu", "amount": 1200, "status": "paid", "city": "Perinthalmanna"},
    {"id": 2, "customer": "Rahul", "amount": 450, "status": "pending", "city": "Malappuram"},
    {"id": 3, "customer": "Anu", "amount": 3100, "status": "paid", "city": "Perinthalmanna"},
    {"id": 4, "customer": "Fathima", "amount": 980, "status": "refunded", "city": "Manjeri"},
]
paid_total = sum(o["amount"] for o in orders if o["status"] == "paid")
ids_by_customer = defaultdict(list)
for o in orders:
    ids_by_customer[o["customer"]].append(o["id"])
status_count = Counter(o["status"] for o in orders)
top_two = sorted(orders, key=lambda o: o["amount"], reverse=True)[:2]
amount_by_id = {o["id"]: o["amount"] for o in orders}
cities = {o["city"] for o in orders}
print(paid_total, dict(ids_by_customer), status_count.most_common(1), [o["id"] for o in top_two])
print(any(o["status"] == "refunded" for o in orders), all(o["amount"] > 0 for o in orders))

first, *rest = [o["id"] for o in orders]
for index, (name, amount) in enumerate(zip(["a", "b"], [10, 20]), start=1):
    print(index, name, amount)

# ---------- 3. Functions: *args, **kwargs, keyword-only ----------
def send_sms(phone, message, *, sender="RALFIZ", **meta):
    """sender is keyword-only: send_sms("98..", "hi", "X") is an error -> fewer bugs."""
    return f"[{sender}] to {phone}: {message} {meta or ''}".strip()

print(send_sms("9895663498", "Your booking is confirmed", sender="BOOKIT", booking_id=42))

def make_discount(percent):              # closure: inner function remembers `percent`
    def apply(amount):
        return round(amount * (100 - percent) / 100, 2)
    return apply

festival = make_discount(10)
print(festival(1999))                    # 1799.1

# ---------- 4. Decorators you will actually use ----------
def timed(func):
    @functools.wraps(func)               # keeps func.__name__ / docstring
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        try:
            return func(*args, **kwargs)
        finally:
            logger.info("%s took %.1f ms", func.__name__, (time.perf_counter() - start) * 1000)
    return wrapper

def retry(times=3, delay=0.2, exceptions=(Exception,)):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(1, times + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as exc:
                    if attempt == times:
                        raise
                    logger.warning("%s failed (%s) — retry %d/%d", func.__name__, exc, attempt, times - 1)
                    time.sleep(delay * attempt)   # simple backoff
        return wrapper
    return decorator

calls = {"n": 0}

@timed
@retry(times=3, exceptions=(ConnectionError,))
def call_payment_gateway():
    calls["n"] += 1
    if calls["n"] < 3:
        raise ConnectionError("gateway timeout")
    return "SUCCESS"

print(call_payment_gateway(), "after", calls["n"], "attempts")

# ---------- 5. Exceptions with meaning ----------
class PaymentError(Exception):
    """Base class for all payment problems."""

class InsufficientBalance(PaymentError):
    def __init__(self, needed, available):
        super().__init__(f"Need Rs {needed}, wallet has Rs {available}")
        self.needed, self.available = needed, available

def pay_from_wallet(amount, balance):
    if amount > balance:
        raise InsufficientBalance(amount, balance)
    return balance - amount

try:
    pay_from_wallet(500, 120)
except PaymentError as exc:              # catch the family, not bare `except:`
    print("Payment failed:", exc)
else:
    print("never runs here")
finally:
    print("always runs — close files, release locks")
