"""Closures & decorators: the runnable examples from lesson 5.2 of the Complete Python Tutorial.

Run it with:  python3 22_decorators.py
Then change the code and run it again."""

# ----------------------------------------------------------------------
# closures.py
# ----------------------------------------------------------------------
def make_multiplier(factor):
    def multiply(x):
        return x * factor          # 'factor' is remembered from the outer call
    return multiply

double = make_multiplier(2)
gst = make_multiplier(1.18)
print(double(21), gst(1000))

def make_counter():
    count = 0
    def increment():
        nonlocal count
        count += 1
        return count
    return increment

c = make_counter()
print(c(), c(), c())

# ----------------------------------------------------------------------
# decorator_basics.py
# ----------------------------------------------------------------------
import functools

def announce(func):
    @functools.wraps(func)                      # keep the original name and docstring
    def wrapper(*args, **kwargs):
        print(f"→ calling {func.__name__}{args}")
        result = func(*args, **kwargs)
        print(f"← {func.__name__} returned {result}")
        return result
    return wrapper

@announce                                        # same as: add = announce(add)
def add(a, b):
    """Add two numbers."""
    return a + b

add(3, 4)
print(add.__name__, "|", add.__doc__)

# ----------------------------------------------------------------------
# real_decorators.py
# ----------------------------------------------------------------------
import functools, time

def timer(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        try:
            return func(*args, **kwargs)
        finally:
            print(f"[timer] {func.__name__}: {(time.perf_counter() - start) * 1000:.2f} ms")
    return wrapper

def retry(times=3, exceptions=(Exception,)):       # decorator WITH arguments = 3 levels
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(1, times + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    print(f"[retry] attempt {attempt} failed: {e}")
                    if attempt == times:
                        raise
        return wrapper
    return decorator

def require_role(role):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(user, *args, **kwargs):
            if user.get("role") != role:
                raise PermissionError(f"{user['name']} is not {role}")
            return func(user, *args, **kwargs)
        return wrapper
    return decorator

calls = {"n": 0}

@timer
@retry(times=3, exceptions=(ConnectionError,))
def fetch_rates():
    calls["n"] += 1
    if calls["n"] < 3:
        raise ConnectionError("gateway timeout")
    return {"USD": 83.2}

print(fetch_rates())

@require_role("admin")
def delete_invoice(user, invoice_no):
    return f"{invoice_no} deleted by {user['name']}"

print(delete_invoice({"name": "Jobin", "role": "admin"}, "INV-7"))
try:
    delete_invoice({"name": "Intern", "role": "staff"}, "INV-7")
except PermissionError as e:
    print("Denied:", e)

# ----------------------------------------------------------------------
# cache.py
# ----------------------------------------------------------------------
from functools import cache
import time

@cache
def slow_square(n):
    time.sleep(0.2)          # pretend this is an expensive DB or API call
    return n * n

start = time.perf_counter(); slow_square(9); first = time.perf_counter() - start
start = time.perf_counter(); slow_square(9); second = time.perf_counter() - start
print(f"first call {first:.3f}s, cached call {second:.6f}s")
