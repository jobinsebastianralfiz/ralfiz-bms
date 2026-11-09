"""Strings in depth: the runnable examples from lesson 1.4 of the Complete Python Tutorial.

Run it with:  python3 04_strings.py
Then change the code and run it again."""

# ----------------------------------------------------------------------
# create_strings.py
# ----------------------------------------------------------------------
s1 = 'single quotes'
s2 = "double quotes"
s3 = "It's easy"                 # mix quotes to avoid escaping
s4 = 'He said "hello"'
s5 = """Multi-line
string keeps
line breaks"""
path = r"C:\new\test"            # raw string: backslashes are literal
print(s3, s4)
print(s5)
print("Tab:\tafter tab | New line:\nsecond line")
print(path)
print(len("Ralfiz"))             # 6

# ----------------------------------------------------------------------
# slicing.py
# ----------------------------------------------------------------------
word = "PYTHON"
print(word[0], word[-1])      # P N
print(word[0:3])              # PYT   (start included, stop excluded)
print(word[2:])               # THON
print(word[:4])               # PYTH
print(word[::2])              # PTO   (every 2nd char)
print(word[::-1])             # NOHTYP (reverse!)

phone = "9895663498"
print("Masked:", "X" * 6 + phone[-4:])    # XXXXXX3498

# Strings are IMMUTABLE — you create new strings instead of changing them
try:
    word[0] = "J"
except TypeError as e:
    print("Error:", e)
word = "J" + word[1:]
print(word)                   # JYTHON

# ----------------------------------------------------------------------
# methods.py
# ----------------------------------------------------------------------
raw = "   anu MATHEW   "
print(repr(raw.strip()))          # 'anu MATHEW'  remove surrounding spaces
print(raw.strip().title())        # Anu Mathew
print(raw.upper(), raw.lower())
print("kerala".capitalize())      # Kerala

email = "Intern@Ralfiz.com"
print(email.lower().endswith("@ralfiz.com"))   # True
print(email.find("@"), email.find("#"))        # 6 -1 (not found)
print(email.count("a"))

csv_line = "INV-101,Smart Band,2,1999"
parts = csv_line.split(",")       # → list
print(parts)
print(" | ".join(parts))          # list → string

print("2026-11-09".replace("-", "/"))
print("12345".isdigit(), "abc".isalpha(), "abc123".isalnum(), "   ".isspace())
print("Invoice".center(20, "*"))
print("7".zfill(4))               # 0007 — useful for invoice numbers

# ----------------------------------------------------------------------
# fstrings.py
# ----------------------------------------------------------------------
name = "Rahul"
amount = 125000.5
rate = 0.0725
items = 3

print(f"Hello {name}, you bought {items} items")
print(f"Amount: ₹{amount:,.2f}")            # thousand separator + 2 decimals
print(f"Interest: {rate:.1%}")              # 7.2%
print(f"{'Item':<12}{'Qty':>5}{'Price':>10}")   # alignment: < left, > right, ^ centre
print(f"{'Watch':<12}{2:>5}{2450:>10.2f}")
print(f"{'Strap':<12}{5:>5}{350:>10.2f}")
print(f"Invoice no: INV-{7:05d}")           # INV-00007
print(f"{2 + 3 = }")                        # debug shortcut: prints "2 + 3 = 5"
print(f"{name!r}")                          # repr: 'Rahul'
