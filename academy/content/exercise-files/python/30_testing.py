"""Testing, logging & clean code: the runnable examples from lesson 6.4 of the Complete Python Tutorial.

Run it with:  python3 30_testing.py
Then change the code and run it again."""

# ----------------------------------------------------------------------
# logging_demo.py
# ----------------------------------------------------------------------
import logging, sys

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s %(levelname)-8s %(name)s | %(message)s",
    datefmt="%H:%M:%S",
    stream=sys.stdout,
    force=True,
)
log = logging.getLogger("billing")

log.debug("Calculating invoice %s", "INV-7")       # lazy formatting with %s
log.info("Invoice created for %s", "4Z Watches")
log.warning("GST number missing for customer %d", 42)
try:
    1 / 0
except ZeroDivisionError:
    log.exception("Unexpected error while computing discount")   # includes the traceback

# ----------------------------------------------------------------------
# assert_tests.py
# ----------------------------------------------------------------------
def apply_discount(amount, percent):
    if not 0 <= percent <= 100:
        raise ValueError("percent must be between 0 and 100")
    return round(amount * (1 - percent / 100), 2)

assert apply_discount(1000, 10) == 900
assert apply_discount(199.99, 15) == 169.99
try:
    apply_discount(100, 120)
    raise AssertionError("expected ValueError")
except ValueError:
    pass
print("All tests passed ✅")
