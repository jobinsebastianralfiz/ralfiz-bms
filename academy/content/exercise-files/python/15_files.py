"""File handling: text, CSV & JSON: the runnable examples from lesson 3.4 of the Complete Python Tutorial.

Run it with:  python3 15_files.py
Then change the code and run it again."""

# ----------------------------------------------------------------------
# text_files.py
# ----------------------------------------------------------------------
# 'with' closes the file automatically, even if an error happens
with open("notes.txt", "w", encoding="utf-8") as f:
    f.write("Day 1: Python basics\n")
    f.write("Day 2: Data structures\n")

with open("notes.txt", "a", encoding="utf-8") as f:
    f.write("Day 3: Functions\n")

with open("notes.txt", encoding="utf-8") as f:
    content = f.read()                 # whole file as one string
print(content)

with open("notes.txt", encoding="utf-8") as f:
    for line_no, line in enumerate(f, start=1):   # line by line: memory-friendly
        print(line_no, line.strip())

# ----------------------------------------------------------------------
# pathlib_demo.py
# ----------------------------------------------------------------------
from pathlib import Path

reports = Path("reports")
reports.mkdir(exist_ok=True)                       # create folder if needed
file = reports / "2026-11-sales.txt"               # join paths with /
file.write_text("Total: 14347\n", encoding="utf-8")

print(file.exists(), file.name, file.stem, file.suffix)
print(file.read_text(encoding="utf-8"))
print([p.name for p in reports.glob("*.txt")])     # list matching files

# ----------------------------------------------------------------------
# csv_demo.py
# ----------------------------------------------------------------------
import csv

rows = [
    {"name": "Anu", "course": "Python", "fee": 15000},
    {"name": "Rahul", "course": "Django", "fee": 18000},
    {"name": "Diya", "course": "Python", "fee": 15000},
]
with open("students.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=["name", "course", "fee"])
    writer.writeheader()
    writer.writerows(rows)

with open("students.csv", newline="", encoding="utf-8") as f:
    reader = csv.DictReader(f)          # each row becomes a dict
    total = 0
    for row in reader:
        print(row["name"], row["course"], row["fee"])
        total += int(row["fee"])        # CSV values are ALWAYS strings
print("Total fees:", total)

# ----------------------------------------------------------------------
# json_demo.py
# ----------------------------------------------------------------------
import json

settings = {"shop": "4Z Watches", "gst": 18, "branches": ["Perinthalmanna", "Manjeri"], "open": True}

with open("settings.json", "w", encoding="utf-8") as f:
    json.dump(settings, f, indent=2, ensure_ascii=False)

with open("settings.json", encoding="utf-8") as f:
    loaded = json.load(f)
print(loaded["branches"])

text = json.dumps(settings)           # dict → JSON string (for APIs)
back = json.loads(text)               # JSON string → dict
print(type(text), type(back))
