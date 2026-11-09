"""Dates, times & money: the runnable examples from lesson 6.1 of the Complete Python Tutorial.

Run it with:  python3 27_datetime.py
Then change the code and run it again."""

# ----------------------------------------------------------------------
# dates.py
# ----------------------------------------------------------------------
from datetime import date, datetime, timedelta

d = date(2026, 11, 9)
print(d, d.year, d.month, d.day, d.strftime("%A"))     # weekday name
print(d + timedelta(days=30))                           # due date
print((date(2026, 12, 25) - d).days, "days to Christmas")

dt = datetime(2026, 11, 9, 14, 30)
print(dt.strftime("%d %b %Y, %I:%M %p"))                # 09 Nov 2026, 02:30 PM
parsed = datetime.strptime("09/11/2026 18:45", "%d/%m/%Y %H:%M")
print(parsed, parsed.isoformat())
print(datetime.fromisoformat("2026-11-09T18:45:00"))

# Age calculation
dob = date(2004, 3, 15)
today = date(2026, 11, 9)
age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
print("Age:", age)

# Indian financial year (April → March)
def financial_year(day: date) -> str:
    start = day.year if day.month >= 4 else day.year - 1
    return f"{start}-{str(start + 1)[-2:]}"
print(financial_year(date(2026, 3, 31)), financial_year(date(2026, 4, 1)))

# ----------------------------------------------------------------------
# money.py
# ----------------------------------------------------------------------
from decimal import Decimal, ROUND_HALF_UP

print(sum([0.1] * 10))                         # 0.9999999999999999 with float
print(sum([Decimal("0.1")] * 10))              # 1.0 with Decimal

PAISA = Decimal("0.01")
def money(value: Decimal) -> Decimal:
    return value.quantize(PAISA, rounding=ROUND_HALF_UP)

price = Decimal("99.99")
gst = money(price * Decimal("18") / 100)
total = price + gst
grand = total.quantize(Decimal("1"), rounding=ROUND_HALF_UP)
print(f"Price {price}, GST {gst}, Total {total}, Rounded {grand}, Round-off {grand - total}")

def format_inr(amount: Decimal) -> str:
    """Indian grouping: 12,34,567.89"""
    sign = "-" if amount < 0 else ""
    whole, frac = f"{abs(amount):.2f}".split(".")
    last3, rest = whole[-3:], whole[:-3]
    groups = []
    while len(rest) > 2:
        groups.insert(0, rest[-2:])
        rest = rest[:-2]
    if rest:
        groups.insert(0, rest)
    return f"{sign}₹{','.join(groups + [last3]) if groups else last3}.{frac}"

print(format_inr(Decimal("1234567.5")), format_inr(Decimal("999")), format_inr(Decimal("306950")))
