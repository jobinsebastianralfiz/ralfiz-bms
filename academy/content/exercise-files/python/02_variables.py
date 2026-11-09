"""Variables & data types: the runnable examples from lesson 1.2 of the Complete Python Tutorial.

Run it with:  python3 02_variables.py
Then change the code and run it again."""

# ----------------------------------------------------------------------
# variables.py
# ----------------------------------------------------------------------
name = "Anu"            # str
age = 21                # int
cgpa = 8.45             # float
is_intern = True        # bool
mentor = None           # NoneType: "no value yet"

print(name, age, cgpa, is_intern, mentor)
print(type(name), type(age), type(cgpa), type(is_intern), type(mentor))

# A variable can be re-assigned, even to another type (allowed, but avoid it)
age = 22
print("Next year:", age)

# Multiple assignment and swapping
x, y, z = 1, 2, 3
x, y = y, x             # swap without a temp variable
print(x, y, z)

a = b = 0               # same value to many names
print(a, b)

# ----------------------------------------------------------------------
# conversion.py
# ----------------------------------------------------------------------
print(int("25") + 5)          # 30   string → int
print(float("99.50"))         # 99.5
print(str(100) + " rupees")   # "100 rupees"
print(int(9.99))              # 9    (truncates, does NOT round)
print(round(9.99))            # 10
print(int("1010", 2))         # 10   binary string → int
print(bool(0), bool(""), bool([]), bool(None))    # all False ("falsy")
print(bool(5), bool("hi"), bool([0]))             # all True ("truthy")

# Converting invalid text raises an error — handled properly in Lesson 16
try:
    int("12abc")
except ValueError as e:
    print("Error:", e)

# ----------------------------------------------------------------------
# identity.py
# ----------------------------------------------------------------------
a = [1, 2, 3]
b = a            # b points to the SAME list
b.append(4)
print(a)         # [1, 2, 3, 4]  — a changed too!
print(a is b)    # True: same object
print(id(a) == id(b))

c = [1, 2, 3, 4]
print(a == c)    # True: same value
print(a is c)    # False: different objects
