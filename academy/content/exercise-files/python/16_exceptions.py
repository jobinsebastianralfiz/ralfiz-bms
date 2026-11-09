"""Errors & exceptions: the runnable examples from lesson 3.5 of the Complete Python Tutorial.

Run it with:  python3 16_exceptions.py
Then change the code and run it again."""

# ----------------------------------------------------------------------
# traceback.py
# ----------------------------------------------------------------------
def get_price(prices, item):
    return prices[item]

prices = {"watch": 2450}
# get_price(prices, "clock")    # uncomment to see the traceback, then read it from the bottom

# ----------------------------------------------------------------------
# try_except.py
# ----------------------------------------------------------------------
def safe_divide(a, b):
    try:
        result = a / b
    except ZeroDivisionError:
        print("Cannot divide by zero")
        return None
    except TypeError as e:
        print("Bad input:", e)
        return None
    else:
        print("Division succeeded")       # runs only if NO exception
        return result
    finally:
        print("-- finished --")           # ALWAYS runs (cleanup)

print(safe_divide(10, 2))
print(safe_divide(10, 0))
print(safe_divide(10, "x"))

# ----------------------------------------------------------------------
# validate_input.py
# ----------------------------------------------------------------------
def parse_age(text):
    try:
        age = int(text)
    except ValueError:
        return None, "Please enter a number"
    if not 0 < age < 120:
        return None, "Age must be between 1 and 119"
    return age, None

for attempt in ["twenty", "-4", "23"]:        # pretend user inputs
    age, error = parse_age(attempt)
    if error:
        print(f"{attempt!r}: {error}")
    else:
        print("Accepted age", age)
        break

# ----------------------------------------------------------------------
# custom_exceptions.py
# ----------------------------------------------------------------------
class PaymentError(Exception):
    """Base class for payment problems."""

class InsufficientBalance(PaymentError):
    def __init__(self, needed, available):
        super().__init__(f"Need ₹{needed}, wallet has ₹{available}")
        self.needed = needed
        self.available = available

class InvalidAmount(PaymentError):
    pass

def pay(amount, balance):
    if amount <= 0:
        raise InvalidAmount("Amount must be positive")
    if amount > balance:
        raise InsufficientBalance(amount, balance)
    return balance - amount

for amt in [200, -5, 900]:
    try:
        print("New balance:", pay(amt, 500))
    except InsufficientBalance as e:
        print("Top up needed:", e.needed - e.available)
    except PaymentError as e:              # catches the whole family
        print("Payment failed:", e)

# ----------------------------------------------------------------------
# chaining.py
# ----------------------------------------------------------------------
class ConfigError(Exception):
    pass

def load_port(value):
    try:
        return int(value)
    except ValueError as exc:
        raise ConfigError(f"PORT must be a number, got {value!r}") from exc

try:
    load_port("80a")
except ConfigError as e:
    print(e)
    print("Original cause:", repr(e.__cause__))
