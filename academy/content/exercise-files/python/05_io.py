"""Input & output: the runnable examples from lesson 1.5 of the Complete Python Tutorial.

Run it with:  python3 05_io.py
Then change the code and run it again."""

# ----------------------------------------------------------------------
# simulated_input.py
# ----------------------------------------------------------------------
raw_age = "21"            # pretend the user typed this
age = int(raw_age)
category = "adult" if age >= 18 else "minor"
print(f"Age {age}: {category}")

# ----------------------------------------------------------------------
# receipt.py
# ----------------------------------------------------------------------
shop = "4Z WATCHES"
lines = [("Titan Analog", 1, 2450), ("Leather Strap", 2, 350), ("Battery", 3, 60)]

print(shop.center(36))
print("-" * 36)
print(f"{'Item':<18}{'Qty':>4}{'Amount':>14}")
total = 0
for item, qty, price in lines:
    amount = qty * price
    total += amount
    print(f"{item:<18}{qty:>4}{amount:>14,.2f}")
print("-" * 36)
print(f"{'TOTAL':<22}{total:>14,.2f}")
