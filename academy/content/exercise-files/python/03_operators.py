"""Operators: the runnable examples from lesson 1.3 of the Complete Python Tutorial.

Run it with:  python3 03_operators.py
Then change the code and run it again."""

# ----------------------------------------------------------------------
# arithmetic.py
# ----------------------------------------------------------------------
a, b = 17, 5
print("a + b  =", a + b)     # 22
print("a - b  =", a - b)     # 12
print("a * b  =", a * b)     # 85
print("a / b  =", a / b)     # 3.4   true division → always float
print("a // b =", a // b)    # 3     floor division
print("a % b  =", a % b)     # 2     remainder (modulo)
print("a ** b =", a ** b)    # 1419857  power
print("divmod =", divmod(a, b))   # (3, 2) quotient and remainder together

# Real use: convert minutes to hours and minutes
minutes = 135
print(minutes // 60, "h", minutes % 60, "min")   # 2 h 15 min

# Even / odd check
print(10 % 2 == 0)   # True → even

# ----------------------------------------------------------------------
# comparison_logical.py
# ----------------------------------------------------------------------
marks = 72
print(marks > 40, marks == 100, marks != 72, marks >= 72)
print(40 <= marks < 75)            # chained comparison: True

attendance = 68
passed = marks >= 40 and attendance >= 75
print("Passed:", passed)           # False: attendance too low

is_weekend = False
is_holiday = True
print("Office closed:", is_weekend or is_holiday)   # True
print("Working day:", not (is_weekend or is_holiday))

# Short-circuit: the right side is evaluated only when needed
name = ""
display = name or "Guest"          # common pattern for default values
print(display)

# ----------------------------------------------------------------------
# other_operators.py
# ----------------------------------------------------------------------
total = 100
total += 50     # total = total + 50
total -= 20
total *= 2
total //= 3
print(total)    # 86

cities = ["Perinthalmanna", "Malappuram", "Kochi"]
print("Kochi" in cities)          # True
print("Delhi" not in cities)      # True
print("py" in "python")           # substring check: True

result = None
print(result is None)             # the correct way to check None

# ----------------------------------------------------------------------
# precedence.py
# ----------------------------------------------------------------------
print(2 + 3 * 4)        # 14
print((2 + 3) * 4)      # 20
print(-2 ** 2)          # -4  (** binds tighter than unary minus)
print(2 ** 3 ** 2)      # 512 (** is right-associative: 2 ** 9)

# ----------------------------------------------------------------------
# float_precision.py
# ----------------------------------------------------------------------
print(0.1 + 0.2)                 # 0.30000000000000004
print(0.1 + 0.2 == 0.3)          # False!

import math
print(math.isclose(0.1 + 0.2, 0.3))   # True: compare floats safely

# For MONEY always use Decimal (created from strings)
from decimal import Decimal
print(Decimal("0.1") + Decimal("0.2"))           # 0.3 exactly
price = Decimal("1499.50")
print(price * 3)                                  # 4498.50
