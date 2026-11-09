"""Functions: the runnable examples from lesson 3.1 of the Complete Python Tutorial.

Run it with:  python3 12_functions.py
Then change the code and run it again."""

# ----------------------------------------------------------------------
# functions.py
# ----------------------------------------------------------------------
def greet(name):
    """Return a greeting for the given name."""     # docstring: describes the function
    return f"Hello, {name}!"

message = greet("Anu")
print(message)
print(greet.__doc__)

def add_gst(amount, rate=18):          # rate has a DEFAULT value
    return round(amount * (1 + rate / 100), 2)

print(add_gst(1000))                   # 1180.0  uses default 18
print(add_gst(1000, 5))                # 1050.0  positional
print(add_gst(rate=12, amount=500))    # keyword arguments: any order

def log(message):
    print("LOG:", message)             # no return statement → returns None

result = log("started")
print(result)                          # None

# ----------------------------------------------------------------------
# multi_return.py
# ----------------------------------------------------------------------
def bill_summary(items):
    subtotal = sum(qty * price for qty, price in items)
    gst = round(subtotal * 0.18, 2)
    return subtotal, gst, subtotal + gst      # returns a tuple

sub, tax, total = bill_summary([(2, 350), (1, 2450)])
print(f"Subtotal {sub}, GST {tax}, Total {total}")

# ----------------------------------------------------------------------
# args_kwargs.py
# ----------------------------------------------------------------------
def total(*numbers):                    # any number of positional args → tuple
    return sum(numbers)

print(total(1, 2), total(5, 10, 15, 20))

def create_user(username, **details):   # any keyword args → dict
    return {"username": username, **details}

print(create_user("anu", city="Kochi", role="intern"))

def send_sms(phone, text, *, sender="RALFIZ", flash=False):   # after * → keyword-only
    return f"[{sender}] {phone}: {text} (flash={flash})"

print(send_sms("9895663498", "OTP is 4821", sender="BOOKIT"))

# Unpacking into a call
args = ["9895000001", "Hi"]
opts = {"sender": "SHOP", "flash": True}
print(send_sms(*args, **opts))

# ----------------------------------------------------------------------
# mutable_default.py
# ----------------------------------------------------------------------
def add_bad(item, cart=[]):
    cart.append(item)
    return cart

print(add_bad("a"), add_bad("b"))       # ['a', 'b'] ['a', 'b']  ← shared!

def add_good(item, cart=None):
    if cart is None:
        cart = []
    cart.append(item)
    return cart

print(add_good("a"), add_good("b"))     # ['a'] ['b']

# ----------------------------------------------------------------------
# scope.py
# ----------------------------------------------------------------------
company = "Ralfiz"                 # global

def show():
    city = "Perinthalmanna"        # local: exists only inside show()
    print(company, city)           # can READ the global

show()

counter = 0
def increment():
    global counter                 # needed to ASSIGN a global (avoid in real code)
    counter += 1

increment(); increment()
print(counter)

def outer():
    count = 0
    def inner():
        nonlocal count             # modify the enclosing function's variable
        count += 1
        return count
    inner(); inner()
    return count

print(outer())                     # 2
