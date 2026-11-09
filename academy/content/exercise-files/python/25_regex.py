"""Regular expressions: the runnable examples from lesson 5.5 of the Complete Python Tutorial.

Run it with:  python3 25_regex.py
Then change the code and run it again."""

# ----------------------------------------------------------------------
# regex_basics.py
# ----------------------------------------------------------------------
import re

text = "Call 9895663498 or 98470 12345. Office: 04933-227788. Email: info@ralfiz.com, hr@ralfiz.com"

print(re.findall(r"\b[6-9]\d{9}\b", text))                    # 10-digit mobiles
print(re.findall(r"[\w.+-]+@[\w-]+\.[\w.]+", text))           # emails
print(re.search(r"\d{5}-\d{6}", text).group())                # first landline

# Validation: fullmatch = the WHOLE string must match
PIN = re.compile(r"[1-9]\d{5}")
for pin in ["679322", "012345", "67932"]:
    print(pin, bool(PIN.fullmatch(pin)))

GSTIN = re.compile(r"\d{2}[A-Z]{5}\d{4}[A-Z][1-9A-Z]Z[0-9A-Z]")
print(bool(GSTIN.fullmatch("32ABCDE1234F1Z5")))

# Replace and clean
print(re.sub(r"\s+", " ", "too    many     spaces"))
print(re.sub(r"(\d{6})(\d{4})", r"XXXXXX\2", "9895663498"))  # mask using a group
print(re.split(r"[,;|]\s*", "python, django;postgres| flutter"))

# ----------------------------------------------------------------------
# regex_groups.py
# ----------------------------------------------------------------------
import re

log = """2026-11-09 10:01:22 ERROR [payments] Razorpay timeout order=ORD-5531
2026-11-09 10:02:10 INFO  [auth] login ok user=anu
2026-11-09 10:05:47 ERROR [bookings] slot clash order=ORD-5540"""

pattern = re.compile(
    r"(?P<date>\d{4}-\d{2}-\d{2}) (?P<time>[\d:]+) (?P<level>\w+)\s+\[(?P<module>\w+)\] (?P<msg>.*)"
)
for m in pattern.finditer(log):
    if m["level"] == "ERROR":
        print(m["time"], m["module"], "→", m["msg"])

print(re.findall(r"order=(ORD-\d+)", log))
print(re.findall(r"error", log, flags=re.IGNORECASE))
