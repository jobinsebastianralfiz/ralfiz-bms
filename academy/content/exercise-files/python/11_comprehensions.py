"""Comprehensions: the runnable examples from lesson 2.4 of the Complete Python Tutorial.

Run it with:  python3 11_comprehensions.py
Then change the code and run it again."""

# ----------------------------------------------------------------------
# list_comp.py
# ----------------------------------------------------------------------
# Loop version
squares = []
for n in range(1, 6):
    squares.append(n * n)
print(squares)

# Comprehension version — same result
print([n * n for n in range(1, 6)])

prices = [499, 1299, 99, 2450, 350]
print([p for p in prices if p >= 500])                 # filter
print([round(p * 1.18, 2) for p in prices])            # transform: add 18% GST
print(["expensive" if p > 1000 else "cheap" for p in prices])   # if-else goes BEFORE for

names = ["  anu ", "RAHUL", "diya  "]
print([n.strip().title() for n in names])

# ----------------------------------------------------------------------
# dict_set_comp.py
# ----------------------------------------------------------------------
products = ["watch", "strap", "clock"]
prices = [2450, 350, 899]

price_map = {name: price for name, price in zip(products, prices)}
print(price_map)

with_gst = {name: round(p * 1.18) for name, p in price_map.items() if p > 500}
print(with_gst)

emails = ["a@gmail.com", "b@ralfiz.com", "c@gmail.com"]
domains = {e.split("@")[1] for e in emails}
print(domains)

# ----------------------------------------------------------------------
# nested_gen.py
# ----------------------------------------------------------------------
matrix = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
flat = [n for row in matrix for n in row]       # read left to right like nested loops
print(flat)

pairs = [(x, y) for x in "AB" for y in range(1, 3)]
print(pairs)

# Generator expression: round brackets, lazy, no list built in memory
total = sum(n * n for n in range(1_000_000))
print(total)
