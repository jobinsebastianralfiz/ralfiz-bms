"""Tuples & sets: the runnable examples from lesson 2.2 of the Complete Python Tutorial.

Run it with:  python3 09_tuples_sets.py
Then change the code and run it again."""

# ----------------------------------------------------------------------
# tuples.py
# ----------------------------------------------------------------------
location = (10.9760, 76.2254)          # latitude, longitude of Perinthalmanna
rgb = 37, 99, 235                      # parentheses are optional
single = ("only",)                     # one-item tuple NEEDS a trailing comma
print(type(single), type(("only")))    # tuple vs str!

lat, lng = location                    # unpacking
print(f"Lat {lat}, Lng {lng}")

try:
    location[0] = 0
except TypeError as e:
    print("Tuples are immutable:", e)

# Returning several values from a function = returning a tuple
def min_max(values):
    return min(values), max(values)

low, high = min_max([7, 3, 9, 1])
print(low, high)

# Extended unpacking
first, *middle, last = [1, 2, 3, 4, 5]
print(first, middle, last)

# Tuples can be dictionary keys (lists can't)
distances = {("Kochi", "Kozhikode"): 185, ("Kochi", "Thrissur"): 75}
print(distances[("Kochi", "Thrissur")])

# ----------------------------------------------------------------------
# sets.py
# ----------------------------------------------------------------------
visitors = ["anu", "rahul", "anu", "diya", "rahul"]
unique = set(visitors)
print(unique, len(unique))              # order not guaranteed

skills = {"python", "django"}
skills.add("postgresql")
skills.add("python")                    # duplicate ignored
skills.discard("java")                  # no error if missing (remove() would raise)
print(skills)

empty_set = set()                       # NOT {} — that's an empty dict
print(type(empty_set), type({}))

# ----------------------------------------------------------------------
# set_operations.py
# ----------------------------------------------------------------------
monday = {"anu", "rahul", "diya", "arjun"}
tuesday = {"rahul", "diya", "sneha"}

print("Both days:     ", monday & tuesday)     # intersection
print("Either day:    ", monday | tuesday)     # union
print("Only Monday:   ", monday - tuesday)     # difference
print("Exactly one day:", monday ^ tuesday)    # symmetric difference

required = {"python", "git", "sql"}
candidate = {"python", "git", "html"}
print("Missing skills:", required - candidate)
print("Has all?", required <= candidate)        # subset check

# Membership in a set is MUCH faster than in a list for large data
blocked_ids = set(range(1_000_000))
print(999_999 in blocked_ids)
