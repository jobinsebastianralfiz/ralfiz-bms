"""Conditions: if, elif, else, match: the runnable examples from lesson 1.6 of the Complete Python Tutorial.

Run it with:  python3 06_conditions.py
Then change the code and run it again."""

# ----------------------------------------------------------------------
# grades.py
# ----------------------------------------------------------------------
marks = 78

if marks >= 90:
    grade = "A+"
elif marks >= 80:
    grade = "A"
elif marks >= 70:
    grade = "B+"
elif marks >= 60:
    grade = "B"
elif marks >= 40:
    grade = "C"
else:
    grade = "Fail"

print(f"Marks {marks} → Grade {grade}")

# ----------------------------------------------------------------------
# loan_eligibility.py
# ----------------------------------------------------------------------
age = 29
monthly_income = 42000
credit_score = 710
has_existing_loan = False

if 21 <= age <= 60:
    if monthly_income >= 25000 and credit_score >= 700:
        limit = monthly_income * (20 if not has_existing_loan else 10)
        print(f"Eligible. Loan limit: ₹{limit:,}")
    else:
        print("Not eligible: income or credit score too low")
else:
    print("Not eligible: age outside 21–60")

# ----------------------------------------------------------------------
# ternary.py
# ----------------------------------------------------------------------
stock = 0
status = "In stock" if stock > 0 else "Out of stock"
print(status)

items_in_cart = 3
print(f"{items_in_cart} item{'s' if items_in_cart != 1 else ''}")

# ----------------------------------------------------------------------
# truthy.py
# ----------------------------------------------------------------------
cart = []
if not cart:                      # Pythonic, instead of: if len(cart) == 0
    print("Your cart is empty")

coupon = "DIWALI10"
if coupon:
    print("Applying coupon", coupon)

# ----------------------------------------------------------------------
# match_status.py
# ----------------------------------------------------------------------
def describe(status):
    match status:
        case "pending":
            return "Waiting for confirmation"
        case "confirmed" | "paid":            # either value
            return "All set!"
        case "cancelled":
            return "Booking cancelled"
        case _:                               # default
            return f"Unknown status: {status}"

for s in ["pending", "paid", "cancelled", "lost"]:
    print(s, "→", describe(s))

# Patterns can also unpack structures
def handle(command):
    match command.split():
        case ["add", item, qty]:
            return f"Adding {qty} × {item}"
        case ["remove", item]:
            return f"Removing {item}"
        case _:
            return "Invalid command"

print(handle("add watch 2"))
print(handle("remove strap"))
