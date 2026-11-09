"""Lambda, recursion & higher-order functions: the runnable examples from lesson 3.2 of the Complete Python Tutorial.

Run it with:  python3 13_functional.py
Then change the code and run it again."""

# ----------------------------------------------------------------------
# first_class.py
# ----------------------------------------------------------------------
def shout(text):
    return text.upper() + "!"

def whisper(text):
    return text.lower() + "..."

def speak(style, message):        # takes a FUNCTION as an argument
    return style(message)

print(speak(shout, "Hello"))
print(speak(whisper, "Hello"))

actions = {"loud": shout, "soft": whisper}    # functions stored in a dict
print(actions["loud"]("dispatch"))

# ----------------------------------------------------------------------
# lambda.py
# ----------------------------------------------------------------------
square = lambda x: x * x          # same as: def square(x): return x * x
print(square(7))

employees = [
    {"name": "Anu", "salary": 32000, "joined": 2024},
    {"name": "Rahul", "salary": 45000, "joined": 2022},
    {"name": "Diya", "salary": 38000, "joined": 2023},
]
by_salary = sorted(employees, key=lambda e: e["salary"], reverse=True)
print([e["name"] for e in by_salary])

newest = max(employees, key=lambda e: e["joined"])
print("Newest:", newest["name"])

# ----------------------------------------------------------------------
# map_filter.py
# ----------------------------------------------------------------------
from functools import reduce

prices = [100, 250, 75, 400]
print(list(map(lambda p: p * 1.18, prices)))        # transform each
print(list(filter(lambda p: p > 90, prices)))       # keep matching
print(reduce(lambda acc, p: acc + p, prices, 0))    # combine to one value

# Comprehensions are usually clearer in Python:
print([p * 1.18 for p in prices])
print([p for p in prices if p > 90])
print(sum(prices))

# ----------------------------------------------------------------------
# recursion.py
# ----------------------------------------------------------------------
def factorial(n):
    if n <= 1:              # base case: stops the recursion
        return 1
    return n * factorial(n - 1)

print(factorial(5))         # 120

# Real use: walking nested data (folders, category trees, org charts)
categories = {
    "Electronics": {"Phones": {}, "Watches": {"Smart": {}, "Analog": {}}},
    "Clothing": {"Men": {}, "Women": {}},
}

def print_tree(tree, depth=0):
    for name, children in tree.items():
        print("  " * depth + "- " + name)
        print_tree(children, depth + 1)

print_tree(categories)

# Memoisation makes slow recursion fast
from functools import lru_cache

@lru_cache(maxsize=None)
def fib(n):
    return n if n < 2 else fib(n - 1) + fib(n - 2)

print(fib(80))
