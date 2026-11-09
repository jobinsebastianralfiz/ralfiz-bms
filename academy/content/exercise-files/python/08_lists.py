"""Lists: the runnable examples from lesson 2.1 of the Complete Python Tutorial.

Run it with:  python3 08_lists.py
Then change the code and run it again."""

# ----------------------------------------------------------------------
# list_basics.py
# ----------------------------------------------------------------------
fruits = ["mango", "banana", "jackfruit", "pineapple"]
mixed = [1, "two", 3.0, True, None, [5, 6]]     # any types, even nested lists
empty = []

print(fruits[0], fruits[-1])        # mango pineapple
print(fruits[1:3])                  # ['banana', 'jackfruit']
print(len(fruits))                  # 4
print("mango" in fruits)            # True
print(mixed[5][1])                  # 6 — nested access

fruits[1] = "papaya"                # lists are MUTABLE
print(fruits)

# ----------------------------------------------------------------------
# list_methods.py
# ----------------------------------------------------------------------
cart = ["watch"]
cart.append("strap")                # add one item at the end
cart.extend(["battery", "box"])     # add many items
cart.insert(0, "gift card")         # add at a position
print(cart)

cart.remove("box")                  # remove by value (first match)
last = cart.pop()                   # remove and return the last item
first = cart.pop(0)                 # remove and return by index
print(last, first, cart)

del cart[0]                         # delete by index
print(cart)

nums = [5, 3, 8, 3, 1]
print(nums.index(8), nums.count(3))  # position of 8, how many 3s
nums.clear()
print(nums)

# ----------------------------------------------------------------------
# sorting.py
# ----------------------------------------------------------------------
prices = [499, 99, 1299, 249]
print(sorted(prices))               # NEW sorted list; original unchanged
print(prices)
prices.sort(reverse=True)           # sorts IN PLACE, returns None
print(prices)

names = ["anu", "Rahul", "fathima", "Arjun"]
print(sorted(names))                       # uppercase sorts before lowercase!
print(sorted(names, key=str.lower))        # case-insensitive
print(sorted(names, key=len))              # by length

products = [("Watch", 2450), ("Strap", 350), ("Clock", 899)]
print(sorted(products, key=lambda p: p[1]))   # by price (lambda: Lesson 13)

# ----------------------------------------------------------------------
# builtins.py
# ----------------------------------------------------------------------
marks = [72, 88, 95, 61, 79]
print(sum(marks), min(marks), max(marks))
print(f"Average: {sum(marks) / len(marks):.1f}")
print(any(m < 40 for m in marks))       # did anyone fail?
print(all(m >= 60 for m in marks))      # did everyone get 60+?
print(list(reversed(marks)))
print(list(range(0, 50, 10)))
print([0] * 5)                          # [0, 0, 0, 0, 0]

# ----------------------------------------------------------------------
# copying.py
# ----------------------------------------------------------------------
import copy

original = [1, 2, [3, 4]]
alias = original               # same list — NOT a copy
shallow = original.copy()      # or original[:] or list(original)
deep = copy.deepcopy(original)

original[0] = 100
original[2].append(5)

print("alias:  ", alias)       # [100, 2, [3, 4, 5]]
print("shallow:", shallow)     # [1, 2, [3, 4, 5]] — inner list is shared!
print("deep:   ", deep)        # [1, 2, [3, 4]]    — fully independent

# ----------------------------------------------------------------------
# matrix.py
# ----------------------------------------------------------------------
# rows = students, columns = 3 subjects
scores = [
    [78, 85, 92],
    [64, 70, 58],
    [90, 95, 88],
]
for i, row in enumerate(scores, start=1):
    print(f"Student {i}: total={sum(row)}, avg={sum(row)/len(row):.1f}")

subject_totals = [sum(col) for col in zip(*scores)]   # zip(*) transposes
print("Subject totals:", subject_totals)

grid = [[0] * 3 for _ in range(3)]    # correct way to build a 3x3 grid
grid[0][0] = 1
print(grid)
