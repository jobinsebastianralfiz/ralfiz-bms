"""Context managers: the runnable examples from lesson 5.3 of the Complete Python Tutorial.

Run it with:  python3 23_context.py
Then change the code and run it again."""

# ----------------------------------------------------------------------
# class_cm.py
# ----------------------------------------------------------------------
class Transaction:
    def __init__(self, name):
        self.name = name
        self.operations = []

    def __enter__(self):                       # runs at the start of 'with'
        print(f"BEGIN {self.name}")
        return self                            # bound to the variable after 'as'

    def __exit__(self, exc_type, exc, tb):     # ALWAYS runs at the end
        if exc_type:
            print(f"ROLLBACK {self.name} because: {exc}")
        else:
            print(f"COMMIT {self.name}: {self.operations}")
        return False                           # False = let the exception propagate

with Transaction("transfer-1") as tx:
    tx.operations.append("debit Anu 500")
    tx.operations.append("credit Rahul 500")

try:
    with Transaction("transfer-2") as tx:
        tx.operations.append("debit Anu 500")
        raise ValueError("credit failed")
except ValueError:
    print("Handled after rollback")

# ----------------------------------------------------------------------
# contextlib_demo.py
# ----------------------------------------------------------------------
from contextlib import contextmanager, suppress
import time, os

@contextmanager
def timer(label):
    start = time.perf_counter()
    try:
        yield                                  # the body of the 'with' runs here
    finally:
        print(f"{label}: {(time.perf_counter() - start) * 1000:.1f} ms")

with timer("build report"):
    total = sum(range(2_000_000))

@contextmanager
def temporary_file(path, text):
    with open(path, "w") as f:
        f.write(text)
    try:
        yield path
    finally:
        os.remove(path)                        # cleanup even if an error happens
        print("removed", path)

with temporary_file("tmp.txt", "hello") as p:
    print(open(p).read())

with suppress(FileNotFoundError):              # ignore one specific, expected error
    os.remove("does-not-exist.txt")
print("continued safely")
