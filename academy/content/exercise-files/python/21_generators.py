"""Iterators & generators: the runnable examples from lesson 5.1 of the Complete Python Tutorial.

Run it with:  python3 21_generators.py
Then change the code and run it again."""

# ----------------------------------------------------------------------
# iterator_protocol.py
# ----------------------------------------------------------------------
nums = [10, 20, 30]
it = iter(nums)          # get an iterator
print(next(it))          # 10
print(next(it))          # 20
print(next(it))          # 30
try:
    next(it)
except StopIteration:
    print("Iterator exhausted — this is how a for loop knows to stop")

# ----------------------------------------------------------------------
# custom_iterator.py
# ----------------------------------------------------------------------
class Countdown:
    def __init__(self, start):
        self.current = start
    def __iter__(self):
        return self
    def __next__(self):
        if self.current <= 0:
            raise StopIteration
        value = self.current
        self.current -= 1
        return value

for n in Countdown(5):
    print(n, end=" ")
print("🚀")

# ----------------------------------------------------------------------
# generators.py
# ----------------------------------------------------------------------
def countdown(n):
    while n > 0:
        yield n            # pause here, hand out n
        n -= 1

print(list(countdown(5)))

def invoice_numbers(prefix="INV", start=1):
    n = start
    while True:            # infinite, but only produces values on demand
        yield f"{prefix}-{n:04d}"
        n += 1

gen = invoice_numbers()
print(next(gen), next(gen), next(gen))

# Memory comparison
import sys
big_list = [n * 2 for n in range(1_000_000)]
big_gen = (n * 2 for n in range(1_000_000))
print(f"list: {sys.getsizeof(big_list):,} bytes | generator: {sys.getsizeof(big_gen)} bytes")

# ----------------------------------------------------------------------
# pipeline.py
# ----------------------------------------------------------------------
# create a sample log file
with open("access.log", "w") as f:
    for i in range(1, 2001):
        status = 500 if i % 97 == 0 else (404 if i % 13 == 0 else 200)
        f.write(f"2026-11-09 10:{i % 60:02d} GET /api/v1/bookings/{i} {status}\n")

def read_lines(path):
    with open(path) as f:
        for line in f:                       # one line in memory at a time
            yield line.rstrip("\n")

def parse(lines):
    for line in lines:
        date, time, method, path, status = line.split()
        yield {"path": path, "status": int(status)}

def errors_only(records):
    return (r for r in records if r["status"] >= 500)

pipeline = errors_only(parse(read_lines("access.log")))
for record in pipeline:
    print(record)

# ----------------------------------------------------------------------
# itertools_demo.py
# ----------------------------------------------------------------------
from itertools import count, islice, chain, cycle, accumulate, batched  # batched: Python 3.12+

print(list(islice(count(100, 5), 4)))              # 100 105 110 115
print(list(chain([1, 2], (3, 4), "ab")))           # join iterables
colors = cycle(["red", "green"])
print([next(colors) for _ in range(5)])
print(list(accumulate([100, 250, 75])))            # running total: 100 350 425
print(list(batched(range(10), 4)))                 # chunks: process 4 at a time
