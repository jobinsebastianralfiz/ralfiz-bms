"""Loops: for & while: the runnable examples from lesson 1.7 of the Complete Python Tutorial.

Run it with:  python3 07_loops.py
Then change the code and run it again."""

# ----------------------------------------------------------------------
# for_loops.py
# ----------------------------------------------------------------------
for city in ["Kochi", "Kozhikode", "Thrissur"]:
    print("Delivering to", city)

for i in range(5):            # 0, 1, 2, 3, 4
    print(i, end=" ")
print()
for i in range(1, 11, 2):     # start, stop (excluded), step → 1 3 5 7 9
    print(i, end=" ")
print()
for i in range(10, 0, -3):    # counting down: 10 7 4 1
    print(i, end=" ")
print()

for ch in "Py":               # strings are iterable too
    print(ch)

# ----------------------------------------------------------------------
# enumerate_zip.py
# ----------------------------------------------------------------------
students = ["Anu", "Rahul", "Fathima"]
marks = [91, 76, 84]

for position, name in enumerate(students, start=1):
    print(position, name)

for name, mark in zip(students, marks):     # walk two lists together
    print(f"{name}: {mark}")

# ----------------------------------------------------------------------
# while_loop.py
# ----------------------------------------------------------------------
# How many years until a ₹1,00,000 deposit doubles at 7% per year?
balance = 100000
years = 0
while balance < 200000:
    balance *= 1.07
    years += 1
print(f"Doubles in {years} years → ₹{balance:,.0f}")

# Sum of digits of a number
n = 98765
total = 0
while n > 0:
    total += n % 10      # last digit
    n //= 10             # drop last digit
print("Sum of digits:", total)

# ----------------------------------------------------------------------
# break_continue.py
# ----------------------------------------------------------------------
orders = [120, -5, 340, 0, 999, 75]

for amount in orders:
    if amount <= 0:
        continue                 # skip invalid, go to next item
    if amount > 500:
        print("Large order found:", amount)
        break                    # stop the loop completely
    print("Processing", amount)

# for ... else: the else runs only if the loop did NOT break
def is_prime(n):
    if n < 2:
        return False
    for d in range(2, int(n ** 0.5) + 1):
        if n % d == 0:
            break
    else:
        return True
    return False

print([n for n in range(1, 30) if is_prime(n)])

# ----------------------------------------------------------------------
# nested.py
# ----------------------------------------------------------------------
for row in range(1, 5):
    print("* " * row)

print()
for i in range(1, 4):
    for j in range(1, 6):
        print(f"{i * j:4}", end="")
    print()
