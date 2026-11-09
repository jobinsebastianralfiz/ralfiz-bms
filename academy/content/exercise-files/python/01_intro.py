"""Introduction & setup: the runnable examples from lesson 1.1 of the Complete Python Tutorial.

Run it with:  python3 01_intro.py
Then change the code and run it again."""

# ----------------------------------------------------------------------
# hello.py
# ----------------------------------------------------------------------
print("Hello, World!")
print("Welcome to Ralfiz Technologies")
print("Python", "is", "fun")             # multiple values are separated by a space
print("2026", "11", "09", sep="-")        # custom separator
print("Loading", end="... ")              # end controls what comes after (default: new line)
print("done!")

# ----------------------------------------------------------------------
# comments_indentation.py
# ----------------------------------------------------------------------
# This is a single-line comment. Python ignores it.

"""
Triple-quoted strings are often used as multi-line notes
or as documentation (docstrings) for functions and classes.
"""

age = 20
if age >= 18:
    print("Adult")          # 4 spaces of indentation = inside the if block
    print("Can vote")
print("This line always runs")   # back to no indentation = outside the block
