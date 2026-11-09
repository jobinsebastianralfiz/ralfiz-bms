"""Build the intern Python & Django course (track `django`) from the BookIt training kit.

The kit lives in academy/content/exercise-files/django/ (day1, day2, snippets, bookit).
This script writes academy/content/django.json and adds the kit's files to
files-index.json. Re-run it after editing a lesson, then `python manage.py import_labs`.

    python academy/content/sources/build_django_course.py
"""
import json
from html import escape
from pathlib import Path

CONTENT = Path(__file__).resolve().parent.parent
KIT = CONTENT / 'exercise-files' / 'django'


def code(src):
    return f'<pre class="code">{escape(src.strip())}</pre>'


def q(question, options, answer, explanation):
    return {'question': question, 'options': options, 'answer': answer, 'explanation': explanation}


def f(*paths):
    return [f'django/{p}' for p in paths]


DESCRIPTIONS = {
    'day1/fundamentals.py': 'Day 1 warm-up: mutability, comprehensions, closures, decorators and exceptions.',
    'day1/sales_report.py': 'Day 1 project: validate a POS sales CSV and write a JSON summary plus errors.csv.',
    'day1/data/sales.csv': 'Nine sales rows, three of them deliberately broken.',
    'day2/invoice.py': 'Day 2 project: a GST invoice engine in plain Python (CGST/SGST/IGST, round-off, FY numbers).',
    'day2/test_invoice.py': 'pytest suite for the invoice engine: fixtures, parametrize, pytest.raises.',
    'day2/pincode_client.py': 'Address autofill from an Indian PIN code: requests session, retries, timeouts, a generator.',
    'snippets/orm_reports.py': 'Eight ORM report queries for the Django shell, plus the N+1 problem measured.',
}


# ---------------------------------------------------------------------------
# Lessons
# ---------------------------------------------------------------------------

L1 = {
    'id': 'dj1', 'num': '1.1', 'title': 'Python traps every junior ships once', 'minutes': 60,
    'summaryHtml': '<p>Mutable default arguments, shallow versus deep copies, and the comprehension and <code>collections</code> tools you will use every day to summarise business data.</p>',
    'contentHtml': '\n'.join([
        '<h3>In plain words</h3>',
        '<p>Python names point at objects. When two names point at the same list or dict, changing it through one name changes what the other name sees. Most “my cart has items from another customer” bugs come from this one fact.</p>',
        '<h3>Trap 1: the mutable default argument</h3>',
        '<p>A default value is created <strong>once</strong>, when the function is defined, not every time it is called. A list default is therefore shared by every call.</p>',
        code('''
def add_item_buggy(item, cart=[]):        # default list is created ONCE
    cart.append(item)
    return cart

def add_item(item, cart=None):            # correct pattern
    if cart is None:
        cart = []
    cart.append(item)
    return cart

print(add_item_buggy("watch"), add_item_buggy("strap"))   # ['watch', 'strap'] twice!
print(add_item("watch"), add_item("strap"))               # ['watch'] ['strap']
'''),
        '<p>Rule: never use a list, dict or set as a default. Use <code>None</code> and create the object inside the function.</p>',
        '<h3>Trap 2: shallow copy</h3>',
        '<p><code>copy.copy()</code> copies only the outer container. The inner list of items is still shared. <code>copy.deepcopy()</code> copies all the way down.</p>',
        code('''
order = {"id": 1, "items": [{"sku": "W1", "qty": 1}]}
shallow, deep = copy.copy(order), copy.deepcopy(order)
order["items"][0]["qty"] = 5
print(shallow["items"][0]["qty"], deep["items"][0]["qty"])  # 5 1
'''),
        '<h3>Identity, equality and fast lookups</h3>',
        '<ul>',
        '<li><code>==</code> compares values; <code>is</code> compares identity (the same object). Use <code>is</code> only for <code>None</code>, <code>True</code> and <code>False</code>.</li>',
        '<li>Immutable: <code>int</code>, <code>float</code>, <code>str</code>, <code>tuple</code>, <code>frozenset</code>, <code>Decimal</code>. Mutable: <code>list</code>, <code>dict</code>, <code>set</code> and most objects.</li>',
        '<li>Membership in a <code>set</code> is O(1); in a <code>list</code> it is O(n). Keep “already processed IDs” in a set.</li>',
        '<li><code>sorted(data, key=...)</code> returns a new list; <code>list.sort()</code> sorts in place and returns <code>None</code>.</li>',
        '</ul>',
        '<h3>Summarising data in one line</h3>',
        '<p>Business code is mostly “group these rows and add them up”. Learn these tools well:</p>',
        '<table><thead><tr><th>Tool</th><th>Use it for</th></tr></thead><tbody>',
        '<tr><td><code>sum(x for x in rows if ...)</code></td><td>A total with a filter, without building a list</td></tr>',
        '<tr><td><code>defaultdict(list)</code></td><td>Group rows by a key: order ids per customer</td></tr>',
        '<tr><td><code>Counter(...)</code></td><td>Count by a key; <code>.most_common(n)</code> gives the top n</td></tr>',
        '<tr><td><code>sorted(rows, key=..., reverse=True)[:n]</code></td><td>Top n rows by a field</td></tr>',
        '<tr><td><code>{k: v for ...}</code> and <code>{x for ...}</code></td><td>Dict and set comprehensions: lookup tables and unique values</td></tr>',
        '<tr><td><code>any()</code> / <code>all()</code></td><td>“Is there at least one refunded order?” / “Are all amounts positive?”</td></tr>',
        '</tbody></table>',
        code('''
paid_total = sum(o["amount"] for o in orders if o["status"] == "paid")
ids_by_customer = defaultdict(list)
for o in orders:
    ids_by_customer[o["customer"]].append(o["id"])
status_count = Counter(o["status"] for o in orders)
top_two = sorted(orders, key=lambda o: o["amount"], reverse=True)[:2]
'''),
        '<p>Unpacking keeps loops readable: <code>first, *rest = ids</code>, and <code>for i, (name, amount) in enumerate(zip(names, amounts), start=1)</code>.</p>',
        '<div class="callout"><strong>Readability check:</strong> use a comprehension when it fits on one or two lines and reads like English. If it has two <code>for</code> clauses and an <code>if</code>, write a loop. Your teammate reads code ten times more often than you write it.</div>',
        '<h3>The daily workflow</h3>',
        '<p>Every Ralfiz project has its own virtual environment and a pinned requirements file. “Works on my machine” is not an acceptable status.</p>',
        code('''
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
git switch -c feat/sales-report
git add -p && git commit -m "feat: validate sales rows"
'''),
        '<div class="warn">Never commit <code>.env</code> files, passwords, API keys, <code>.venv/</code> or database files. A key leaked in a public repo is abused within minutes.</div>',
    ]),
    'terms': [
        {'term': 'Mutable', 'definition': 'An object that can change in place: list, dict, set. Strings, ints and tuples are immutable.'},
        {'term': 'Mutable default argument', 'definition': 'A list or dict used as a parameter default. It is created once and shared by every call.'},
        {'term': 'Shallow copy', 'definition': 'copy.copy(): a new outer object whose inner objects are still shared with the original.'},
        {'term': 'Deep copy', 'definition': 'copy.deepcopy(): copies the object and everything inside it.'},
        {'term': 'Generator expression', 'definition': 'A comprehension in round brackets, e.g. sum(x for x in rows). It yields values one by one without building a list.'},
        {'term': 'defaultdict', 'definition': 'A dict that creates a default value (an empty list, 0) the first time a missing key is used.'},
        {'term': 'Counter', 'definition': 'A dict subclass that counts things; most_common(n) returns the n most frequent.'},
    ],
    'examTip': 'In interviews, “what does this print?” with a list default argument is one of the most common Python questions. Explain that defaults are evaluated once at definition time.',
    'lab': {
        'files': f('day1/fundamentals.py'),
        'steps': [
            'Download the lesson files, open day1/fundamentals.py and run python fundamentals.py.',
            'Before reading each print line, write down what you expect it to print. Then compare with the real output.',
            'Explain to yourself why add_item_buggy prints [\'watch\', \'strap\'] twice.',
            'Change the shallow copy example so that changing order no longer affects shallow, without using deepcopy (hint: copy the items list too).',
            'Add a line that prints the total amount per city using defaultdict(int).',
            'Add a line that prints the set of customers who have a paid order, using a set comprehension.',
        ],
        'check': [
            'The paid total prints 4300 and the top two order ids are [3, 1].',
            'Your per-city totals print Perinthalmanna: 4300, Malappuram: 450, Manjeri: 980.',
            'Your paid-customers set contains only Anu.',
        ],
    },
    'quiz': [
        q('def f(x, acc=[]): acc.append(x); return acc. What does print(f(1), f(2)) show?',
          ['[1] [2]', '[1, 2] [1, 2]', '[1] [1, 2]', 'An error'], 1,
          'The default list is created once and both calls append to it. Both results are the same list object, printed after both calls ran, so you see [1, 2] twice.'),
        q('After shallow = copy.copy(order), you change order["items"][0]["qty"]. What happens to shallow?',
          ['Nothing, shallow is a copy', 'shallow sees the change because the inner list is shared', 'Python raises an error', 'shallow is reset to an empty dict'], 1,
          'A shallow copy only copies the outer dict. The items list inside is the same object in both.'),
        q('Which tool counts orders per status and gives the most common one?',
          ['defaultdict(list)', 'Counter', 'set comprehension', 'enumerate'], 1,
          'Counter(o["status"] for o in orders).most_common(1) counts and ranks in one step.'),
        q('What is the safest default for a parameter that should start as an empty list?',
          ['cart=[]', 'cart=list', 'cart=None, then create the list inside', 'cart=()'], 2,
          'Use None as the default and create a fresh list inside the function on each call.'),
        q('When should you use is instead of ==?',
          ['Always, it is faster', 'Only for singletons such as None, True and False', 'For comparing strings', 'For comparing numbers'], 1,
          '== checks equal values; is checks the same object in memory. Two equal strings or numbers may be different objects.'),
    ],
}

L2 = {
    'id': 'dj2', 'num': '1.2', 'title': 'Functions, decorators and exceptions', 'minutes': 60,
    'summaryHtml': '<p>Keyword-only arguments, closures, the <code>@timed</code> and <code>@retry</code> decorators you will meet in real code, and an exception hierarchy that callers can catch cleanly.</p>',
    'contentHtml': '\n'.join([
        '<h3>Keyword-only arguments</h3>',
        '<p>Everything after a bare <code>*</code> must be passed by name. This stops callers from mixing up two string arguments.</p>',
        code('''
def send_sms(phone, message, *, sender="RALFIZ", **meta):
    """sender is keyword-only: send_sms("98..", "hi", "X") is an error -> fewer bugs."""
    return f"[{sender}] to {phone}: {message} {meta or ''}".strip()

send_sms("9895663498", "Your booking is confirmed", sender="BOOKIT", booking_id=42)
'''),
        '<p><code>**meta</code> collects any extra keyword arguments into a dict, here <code>{\'booking_id\': 42}</code>.</p>',
        '<h3>Closures</h3>',
        '<p>An inner function remembers the variables of the function that created it. That lets you build configured functions.</p>',
        code('''
def make_discount(percent):
    def apply(amount):
        return round(amount * (100 - percent) / 100, 2)
    return apply

festival = make_discount(10)
festival(1999)   # 1799.1
'''),
        '<h3>Decorators</h3>',
        '<p>A decorator is a function that takes a function and returns a new one that wraps it. Django uses them everywhere: <code>@login_required</code>, <code>@require_POST</code>, <code>@transaction.atomic</code>. Writing two yourself makes them stop feeling like magic.</p>',
        code('''
def timed(func):
    @functools.wraps(func)               # keeps func.__name__ / docstring
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        try:
            return func(*args, **kwargs)
        finally:
            logger.info("%s took %.1f ms", func.__name__, (time.perf_counter() - start) * 1000)
    return wrapper
'''),
        '<p><code>@retry(times=3, exceptions=(ConnectionError,))</code> takes arguments, so it is a function that <em>returns</em> a decorator: three levels deep. It retries only the exceptions you name, waits a little longer each time (backoff), and re-raises on the last attempt so failures are never swallowed.</p>',
        '<div class="warn">Always use <code>functools.wraps</code>. Without it every decorated function is called <code>wrapper</code> in logs and tracebacks.</div>',
        '<h3>Exceptions with meaning</h3>',
        '<p>Create one base class per area and specific subclasses under it. Callers catch the base class; the message is safe to show.</p>',
        code('''
class PaymentError(Exception):
    """Base class for all payment problems."""

class InsufficientBalance(PaymentError):
    def __init__(self, needed, available):
        super().__init__(f"Need Rs {needed}, wallet has Rs {available}")
        self.needed, self.available = needed, available

try:
    pay_from_wallet(500, 120)
except PaymentError as exc:              # catch the family, not bare `except:`
    print("Payment failed:", exc)
else:
    print("runs only when no exception")
finally:
    print("always runs: close files, release locks")
'''),
        '<p>Never write a bare <code>except:</code>. It also catches <code>KeyboardInterrupt</code> and hides real bugs.</p>',
    ]),
    'terms': [
        {'term': 'Keyword-only argument', 'definition': 'A parameter after * in the signature; it can only be passed as name=value.'},
        {'term': '**kwargs', 'definition': 'Collects extra keyword arguments into a dict.'},
        {'term': 'Closure', 'definition': 'An inner function that keeps access to variables of the function that created it.'},
        {'term': 'Decorator', 'definition': 'A function that wraps another function to add behaviour before or after it, applied with @name.'},
        {'term': 'functools.wraps', 'definition': 'Copies the wrapped function’s name and docstring onto the wrapper.'},
        {'term': 'Backoff', 'definition': 'Waiting longer between each retry so a struggling server gets time to recover.'},
        {'term': 'Exception hierarchy', 'definition': 'A base exception class with specific subclasses, so callers can catch a whole family.'},
    ],
    'examTip': 'Stacked decorators apply bottom-up: in @timed over @retry, retry wraps the function first and timed measures all the attempts together.',
    'lab': {
        'files': f('day1/fundamentals.py'),
        'steps': [
            'Run python fundamentals.py and find the two WARNING lines from @retry and the INFO line from @timed.',
            'Swap the order of @timed and @retry. Run again and explain why the timing line now appears differently.',
            'Call send_sms("9895663498", "hi", "X") and read the TypeError. Fix the call by passing sender by name.',
            'Write a decorator log_calls that logs the function name and its arguments before calling it. Apply it to pay_from_wallet.',
            'Add a CardDeclined(PaymentError) exception and raise it from a new pay_by_card function. Catch it with the existing except PaymentError block.',
        ],
        'check': [
            'The script ends with SUCCESS after 3 attempts and Payment failed: Need Rs 500, wallet has Rs 120.',
            'With the decorators swapped you see one timing line per attempt instead of one in total.',
            'Your CardDeclined is caught by except PaymentError without adding a new except branch.',
        ],
    },
    'quiz': [
        q('def send_sms(phone, message, *, sender="RALFIZ"). Which call is valid?',
          ['send_sms("98..", "hi", "X")', 'send_sms("98..", "hi", sender="X")', 'send_sms(sender="X")', 'send_sms("98..")'], 1,
          'sender comes after *, so it must be passed by name. phone and message are required.'),
        q('Why use functools.wraps inside a decorator?',
          ['It makes the function faster', 'It keeps the original function name and docstring', 'It is required for the decorator to run', 'It catches exceptions'], 1,
          'Without wraps the decorated function reports its name as wrapper, which makes logs and debugging confusing.'),
        q('A retry decorator should re-raise the exception on the last attempt because…',
          ['Python requires it', 'otherwise a real failure would be silently swallowed', 'it makes the retry faster', 'logging only works with raise'], 1,
          'If the final attempt fails the caller must know. Returning None would hide the outage.'),
        q('Which block runs whether or not an exception was raised?',
          ['else', 'except', 'finally', 'elif'], 2,
          'finally always runs. else runs only when no exception occurred.'),
    ],
}

L3 = {
    'id': 'dj3', 'num': '1.3', 'title': 'Project: daily sales report from a CSV', 'minutes': 90,
    'summaryHtml': '<p>A real command-line tool: read a POS export, validate every row, reject bad rows with a reason, and write a JSON summary. Dataclasses, <code>Decimal</code>, <code>argparse</code> and <code>pathlib</code>.</p>',
    'contentHtml': '\n'.join([
        '<h3>The job</h3>',
        '<p>A shop sends you its daily POS export. Some rows are broken: a missing quantity, <code>abc</code> as a price, a negative quantity. The tool must never crash on bad data. It keeps the good rows, explains every bad one, and produces totals.</p>',
        code('python sales_report.py data/sales.csv --out report.json --top 5'),
        '<h3>Model the row with a frozen dataclass</h3>',
        code('''
@dataclass(frozen=True)
class Sale:
    invoice_no: str
    date: str
    product: str
    qty: int
    unit_price: Decimal
    payment_mode: str

    @property
    def total(self) -> Decimal:
        return self.unit_price * self.qty
'''),
        '<p><code>frozen=True</code> means a Sale cannot be changed after it is created. A computed value such as <code>total</code> is a <code>@property</code>, so it can never get out of step with qty and price.</p>',
        '<h3>Money is Decimal, never float</h3>',
        '<p><code>0.1 + 0.2</code> is <code>0.30000000000000004</code> in float. On an invoice that is a wrong rupee figure. Parse prices with <code>Decimal("2450.00")</code> (from the string, not from a float).</p>',
        '<h3>Validate in one place and raise a meaningful error</h3>',
        code('''
def parse_row(row: dict[str, str]) -> Sale:
    missing = [key for key in REQUIRED if not (row.get(key) or "").strip()]
    if missing:
        raise RowError(f"missing {', '.join(missing)}")
    try:
        qty = int(row["qty"])
        price = Decimal(row["unit_price"])
    except (ValueError, InvalidOperation) as exc:
        raise RowError("bad number in qty/unit_price") from exc
    if qty <= 0 or price < 0:
        raise RowError("qty must be > 0 and unit_price >= 0")
    ...
'''),
        '<p><code>raise ... from exc</code> keeps the original error attached for debugging. The loader catches only <code>RowError</code>, records the line number (<code>enumerate(..., start=2)</code> because line 1 is the header) and moves on.</p>',
        '<h3>Clean the data while parsing</h3>',
        '<p>The export has <code>UPI</code>, <code>upi</code> and <code>Cash</code>. <code>.strip().upper()</code> normalises the payment mode so the summary groups them correctly.</p>',
        '<h3>A testable main()</h3>',
        '<p><code>main(argv=None)</code> parses arguments and returns an exit code, and the file ends with <code>sys.exit(main())</code>. A test can call <code>main(["data/sales.csv", "--top", "3"])</code> directly without starting a new process.</p>',
        '<div class="callout">Money totals are written to JSON as strings (<code>str(Decimal)</code>). JSON has no decimal type, and a float would bring the rounding problem back.</div>',
        '<h3>The brief</h3>',
        '<p>A watch retailer exports sales from their POS as CSV every evening. The owner wants a summary on WhatsApp each night, and the accountant wants every bad row explained.</p>',
        '<h3>Acceptance criteria (mentor checks at 4:30)</h3>',
        '<ul>',
        '<li>Grand total for the sample is exactly 14347.00, with 3 rejected rows (lines 6, 7, 9).</li>',
        '<li>No float anywhere in money calculations.</li>',
        '<li>A custom <code>RowError</code> exception; no bare <code>except</code>.</li>',
        '<li>Small functions, one job each: parse, load, summarise, write.</li>',
        '<li>Committed on branch <code>feat/sales-report</code> and pushed.</li>',
        '</ul>',
        '<p><strong>Stretch goals:</strong> a <code>--date</code> filter; a WhatsApp-ready text summary with ₹ formatting; three pytest tests for <code>parse_row</code>.</p>',
    ]),
    'terms': [
        {'term': 'dataclass', 'definition': 'A class decorator that writes __init__, __repr__ and __eq__ for you from typed fields.'},
        {'term': 'frozen dataclass', 'definition': 'A dataclass whose fields cannot be reassigned after creation.'},
        {'term': 'Decimal', 'definition': 'Exact base-10 numbers from the decimal module. Use for money; never float.'},
        {'term': 'csv.DictReader', 'definition': 'Reads a CSV file and gives each row as a dict keyed by the header names.'},
        {'term': 'argparse', 'definition': 'The standard library module for command-line arguments and --help.'},
        {'term': 'Exit code', 'definition': '0 means success; any other number tells the shell or a scheduler that the run failed.'},
        {'term': 'Exception chaining', 'definition': 'raise NewError(...) from exc keeps the original exception as the cause.'},
    ],
    'examTip': 'If an interviewer asks how you handle money in Python, answer: Decimal created from strings, quantize to two places with ROUND_HALF_UP, and store as a decimal column in the database.',
    'lab': {
        'files': f('day1/sales_report.py', 'day1/data/sales.csv'),
        'steps': [
            'Open a terminal in the day1 folder and run python sales_report.py data/sales.csv --out out/report.json --top 3.',
            'Open out/report.json and out/errors.csv. Match each rejected line in errors.csv with the broken row in sales.csv.',
            'Add a new rule: a payment_mode that is not UPI, CASH or CARD is rejected with the message "unknown payment mode".',
            'Add a row INV-1009,2026-11-03,Wall Clock,1,899.00,Cheque to sales.csv and confirm it lands in errors.csv.',
            'Add a "by_date" section to the summary with the revenue for each date.',
            'Run python sales_report.py missing.csv and check that it logs an error and returns exit code 1 (echo $? on Mac/Linux).',
        ],
        'check': [
            'Before your changes: Valid rows: 6 | Rejected: 3 and Grand total: Rs 14347.00.',
            'by_payment_mode shows CARD 2800.00, CASH 2649.00 and UPI 8898.00 (upi and UPI are grouped).',
            'After adding the Cheque row, Rejected becomes 4 and the grand total does not change.',
            'by_date shows 2026-11-02: 9450.00 and 2026-11-03: 4897.00.',
        ],
    },
    'quiz': [
        q('Why is unit_price parsed with Decimal(row["unit_price"]) instead of float()?',
          ['Decimal is faster', 'float cannot represent values like 0.1 exactly, so money totals drift', 'CSV files only support Decimal', 'float cannot be negative'], 1,
          'Binary floating point cannot store most decimal fractions exactly. Decimal does base-10 arithmetic like an accountant.'),
        q('Why does enumerate(csv.DictReader(f), start=2) start at 2?',
          ['Python lists start at 2', 'Line 1 of the file is the header, so the first data row is line 2', 'To skip the first data row', 'DictReader skips a line'], 1,
          'Reporting the real file line number lets the shop find and fix the row.'),
        q('What does frozen=True on the Sale dataclass give you?',
          ['Faster CSV reading', 'Sales cannot be modified after creation', 'Automatic JSON export', 'Fields become optional'], 1,
          'A frozen dataclass raises an error if you try to reassign a field, so a parsed sale stays exactly as validated.'),
        q('Why does main() accept argv and return an int?',
          ['argparse requires it', 'So tests can call it directly and check the exit code', 'To make it run faster', 'Because print needs it'], 1,
          'A main that takes argv and returns an exit code is easy to test and works with sys.exit for the shell.'),
    ],
}

L4 = {
    'id': 'dj4', 'num': '2.1', 'title': 'Project: a GST invoice engine', 'minutes': 90,
    'summaryHtml': '<p>Pure-Python invoicing as Indian businesses need it: CGST + SGST inside the state, IGST across states, round-off to the rupee, GSTIN validation and financial-year invoice numbers.</p>',
    'contentHtml': '\n'.join([
        '<h3>Classes that model the business</h3>',
        '<ul>',
        '<li>Class = a noun in the domain (<code>Invoice</code>, <code>LineItem</code>, <code>Party</code>). Method = a verb it can do (<code>add</code>, <code>totals</code>).</li>',
        '<li><code>@property</code> exposes calculated values (<code>taxable_value</code>) that read like attributes and are always up to date.</li>',
        '<li><code>@classmethod</code> for alternative constructors (<code>Invoice.from_dict(...)</code>); <code>@staticmethod</code> for helpers that need neither the instance nor the class.</li>',
        '<li>Dunder methods make objects feel native: <code>__str__</code> for users, <code>__repr__</code> for developers, <code>__eq__</code> for comparisons.</li>',
        '<li>Prefer composition over inheritance. An Invoice <em>has</em> LineItems; it is not a kind of list.</li>',
        '<li>In a dataclass, a list field needs <code>field(default_factory=list)</code>. It is the dataclass version of the mutable default bug from Day 1.</li>',
        '<li>Type hints (<code>list[LineItem]</code>, <code>str | None</code>) are documentation the editor checks for you.</li>',
        '</ul>',
        '<h3>The rules</h3>',
        '<ul>',
        '<li>Money is always <code>Decimal</code>, rounded <code>ROUND_HALF_UP</code> to 2 places.</li>',
        '<li>Seller and buyer in the same state (same state code): <strong>CGST + SGST</strong>, half the rate each.</li>',
        '<li>Different states: <strong>IGST</strong> at the full rate.</li>',
        '<li>The grand total is rounded to the nearest rupee; the difference is shown as <code>round_off</code>.</li>',
        '<li>Invoice numbers follow the Indian financial year (April to March): <code>RLZ/2026-27/0001</code>.</li>',
        '</ul>',
        '<h3>Rounding in one helper</h3>',
        code('''
PAISA = Decimal("0.01")

def money(value: Decimal) -> Decimal:
    return value.quantize(PAISA, rounding=ROUND_HALF_UP)
'''),
        '<p>Python’s default rounding is banker’s rounding (<code>round(2.5) == 2</code>). Accountants expect half-up. Putting it in one function means nobody rounds differently by accident.</p>',
        '<h3>Validate when the object is created</h3>',
        '<p><code>__post_init__</code> runs right after a dataclass’s generated <code>__init__</code>. An invalid party or line item can never exist.</p>',
        code('''
GSTIN_RE = re.compile(r"^\\d{2}[A-Z]{5}\\d{4}[A-Z][1-9A-Z]Z[0-9A-Z]$")

@dataclass(frozen=True)
class Party:
    name: str
    state_code: str  # "32" = Kerala, "29" = Karnataka ...
    gstin: str | None = None

    def __post_init__(self) -> None:
        if self.gstin:
            if not GSTIN_RE.match(self.gstin):
                raise ValueError(f"Invalid GSTIN: {self.gstin}")
            if self.gstin[:2] != self.state_code:
                raise ValueError("GSTIN state code does not match party state")
'''),
        '<p>The first two digits of a GSTIN are the state code, so a Karnataka party with a <code>32…</code> GSTIN is rejected.</p>',
        '<h3>An Enum instead of magic strings</h3>',
        code('''
class SupplyType(str, Enum):
    INTRA = "intra"  # CGST + SGST
    INTER = "inter"  # IGST
'''),
        '<p><code>Invoice.supply_type</code> is a property derived from the two state codes. It is never stored, so it can never be wrong.</p>',
        '<h3>The financial year</h3>',
        code('''
def financial_year(d: date) -> str:
    """Indian FY runs April -> March. 9 Nov 2026 -> '2026-27'."""
    start = d.year if d.month >= 4 else d.year - 1
    return f"{start}-{str(start + 1)[-2:]}"
'''),
        '<div class="warn">The <code>InvoiceNumberGenerator</code> here keeps its counter in memory. In Django two users saving at the same moment could get the same number. The fix is a database row locked with <code>select_for_update()</code>, which you will see in lesson 4.1.</div>',
        '<div class="callout">GST slabs change by government notification. In real projects keep the allowed rates in settings or the database and confirm them with the accountant.</div>',
    ]),
    'terms': [
        {'term': 'CGST / SGST', 'definition': 'Central and State GST, each half of the rate, charged when seller and buyer are in the same state.'},
        {'term': 'IGST', 'definition': 'Integrated GST at the full rate, charged on supplies between different states.'},
        {'term': 'GSTIN', 'definition': 'The 15-character GST number. Its first two digits are the state code (32 = Kerala).'},
        {'term': 'HSN / SAC', 'definition': 'Codes that classify goods (HSN) and services (SAC) on a GST invoice.'},
        {'term': 'ROUND_HALF_UP', 'definition': 'Rounding where .5 always goes up, the way accountants round.'},
        {'term': '__post_init__', 'definition': 'A dataclass hook that runs after __init__; the place for validation.'},
        {'term': 'Financial year', 'definition': 'India’s accounting year, 1 April to 31 March, written as 2026-27.'},
    ],
    'examTip': 'Taxable value is computed per line before tax; tax is then calculated on each line and added up. Rounding each step to paise in one helper keeps the invoice matching the accountant’s figures.',
    'lab': {
        'files': f('day2/invoice.py'),
        'steps': [
            'Run python invoice.py in the day2 folder and read the totals table.',
            'Change the buyer’s state code from "32" to "29" and run again. Check that CGST and SGST become 0 and IGST appears.',
            'Try Party("Wrong", "29", gstin="32ABCDE1234F1Z5") in a Python shell and read the error.',
            'Add a 10% discount to the website line (discount=Decimal("2500")) and check the new taxable value.',
            'Add a method Invoice.amount_in_words() that returns the grand total in words for the PDF (start with rupees only).',
        ],
        'check': [
            'The unchanged script prints taxable 28499.00, cgst 2564.91, sgst 2564.91, round_off 0.18 and grand_total 33629.00.',
            'With the buyer in state 29, igst is 5129.82 and cgst and sgst are 0.00.',
            'With the discount the taxable value is 25999.00.',
        ],
    },
    'quiz': [
        q('A Kerala seller (32) invoices a Karnataka buyer (29) at 18%. Which tax applies?',
          ['9% CGST + 9% SGST', '18% IGST', '18% CGST', 'No GST'], 1,
          'Different state codes mean an inter-state supply, so IGST at the full rate.'),
        q('What does financial_year(date(2026, 3, 31)) return?',
          ['2026-27', '2025-26', '2026-26', '2025-25'], 1,
          'March is before April, so the year started in April 2025: 2025-26.'),
        q('Why is validation in __post_init__ instead of a separate validate() method?',
          ['It is faster', 'An invalid object can never be created, so nobody can forget to call validate()', 'dataclasses do not allow other methods', 'It is required by Enum'], 1,
          'Validating at construction makes invalid states impossible rather than merely discouraged.'),
        q('Why does Invoice use items: list[LineItem] = field(default_factory=list)?',
          ['It is shorter', 'A plain = [] would be shared by every invoice; the factory makes a fresh list each time', 'Lists cannot be type-hinted', 'It makes the list read-only'], 1,
          'Dataclasses refuse a bare mutable default for exactly this reason. default_factory creates a new list per instance.'),
        q('Why does the engine return Decimal values and not formatted strings like "₹11,800.00"?',
          ['Strings are slower', 'Keep data and presentation separate: templates, PDFs and APIs decide the formatting', 'Decimal cannot be formatted', 'JSON needs Decimal'], 1,
          'The engine computes exact values. Each place that shows them formats them for its own audience.'),
        q('Why is the in-memory InvoiceNumberGenerator not safe in a web app?',
          ['Python cannot count', 'Several server processes and simultaneous requests could hand out the same number', 'It uses Decimal', 'Invoice numbers must be random'], 1,
          'Each worker process has its own counter, and two requests can race. A locked database row gives one shared, ordered sequence.'),
    ],
}

L5 = {
    'id': 'dj5', 'num': '2.2', 'title': 'Testing with pytest', 'minutes': 60,
    'summaryHtml': '<p>Prove the invoice engine is right and keep it right: plain <code>assert</code>, fixtures, <code>@pytest.mark.parametrize</code> for edge cases, and <code>pytest.raises</code> for rules that must fail.</p>',
    'contentHtml': '\n'.join([
        '<h3>Why tests</h3>',
        '<p>Tax rules have edge cases: the last day of March, paise that round up, an interstate client. You will change this code later. Tests are how you know you did not break last month’s invoices.</p>',
        '<h3>A test is a function that asserts</h3>',
        code('''
def test_intra_state_splits_cgst_and_sgst(web_item):
    t = make_invoice("32").add(web_item).totals()
    assert t["cgst"] == t["sgst"] == Decimal("900.00")
    assert t["igst"] == Decimal("0.00")
    assert t["grand_total"] == Decimal("11800.00")
'''),
        '<p>Name tests after the rule they prove. When one fails, the name tells you which business rule broke.</p>',
        '<h3>Fixtures: shared setup</h3>',
        code('''
@pytest.fixture
def web_item() -> LineItem:
    return LineItem("Website development", "998314", 1, Decimal("10000"), Decimal("18"))
'''),
        '<p>A test that has a parameter named <code>web_item</code> receives a fresh one. Each test gets its own object, so tests never affect each other.</p>',
        '<h3>parametrize: one test, many cases</h3>',
        code('''
@pytest.mark.parametrize(
    "day, expected",
    [(date(2026, 3, 31), "2025-26"), (date(2026, 4, 1), "2026-27"), (date(2027, 1, 15), "2026-27")],
)
def test_financial_year(day, expected):
    assert financial_year(day) == expected
'''),
        '<p>Always test the boundary: 31 March and 1 April are where an off-by-one bug would hide.</p>',
        '<h3>Testing that bad input is rejected</h3>',
        code('''
@pytest.mark.parametrize("kwargs", [{"qty": 0}, {"gst_rate": Decimal("7")}, {"discount": Decimal("-1")}])
def test_invalid_line_items_rejected(kwargs):
    data = {"description": "x", "hsn_sac": "1", "qty": 1, "unit_price": Decimal("100"), "gst_rate": Decimal("18")}
    data.update(kwargs)
    with pytest.raises(ValueError):
        LineItem(**data)
'''),
        '<h3>Running</h3>',
        code('''
pip install pytest
pytest -q                 # all tests, quiet
pytest -k financial -v    # only tests whose name contains "financial"
pytest -x                 # stop at the first failure
'''),
        '<div class="callout">Write the test for a bug before you fix the bug. If the test fails first and passes after the fix, you know you fixed the right thing.</div>',
    ]),
    'terms': [
        {'term': 'pytest', 'definition': 'Python’s most used test runner. It finds test_*.py files and functions named test_*.'},
        {'term': 'Fixture', 'definition': 'A function decorated with @pytest.fixture that builds test data; tests receive it by naming it as a parameter.'},
        {'term': 'parametrize', 'definition': 'Runs one test function once per set of inputs.'},
        {'term': 'pytest.raises', 'definition': 'A context manager that passes only if the code inside raises the given exception.'},
        {'term': 'Edge case', 'definition': 'An input at the boundary of a rule, such as 31 March or a zero quantity.'},
        {'term': 'Regression test', 'definition': 'A test written for a bug that was fixed, so it can never come back unnoticed.'},
    ],
    'examTip': 'Good tests check behaviour (the totals a customer sees), not implementation details (which private helper was called). That is what lets you refactor safely.',
    'lab': {
        'files': f('day2/invoice.py', 'day2/test_invoice.py'),
        'steps': [
            'In the day2 folder run pip install pytest and then pytest -q. All tests should pass.',
            'Break the code on purpose: change ROUND_HALF_UP to ROUND_DOWN in money(). Run pytest and read which test fails and why. Undo the change.',
            'Add a test that an interstate invoice with two items sums the IGST of both lines.',
            'Add a parametrized test for Party GSTIN validation with one valid and two invalid GSTINs.',
            'Write a test for the amount_in_words() method you added in lesson 2.1.',
        ],
        'check': [
            'pytest -q reports 11 passed for the original file.',
            'With ROUND_DOWN, test_round_off_to_nearest_rupee fails.',
            'Your new tests pass, and pytest -q now reports more than 11 passed.',
        ],
    },
    'quiz': [
        q('How does a test function receive a fixture?',
          ['By importing it', 'By having a parameter with the fixture’s name', 'By calling fixture()', 'Through a global variable'], 1,
          'pytest looks at the test’s parameter names and injects the matching fixtures.'),
        q('Which dates best test financial_year()?',
          ['1 January only', '31 March and 1 April, the boundary', 'Any random date', 'Only today'], 1,
          'Bugs hide at boundaries. The FY changes between 31 March and 1 April.'),
        q('with pytest.raises(ValueError): LineItem(qty=0, ...) passes when…',
          ['LineItem is created', 'LineItem raises ValueError', 'Any exception is raised', 'qty is 0 in the result'], 1,
          'pytest.raises passes only if that exception type is raised inside the block.'),
        q('What does @pytest.mark.parametrize do?',
          ['Runs tests in parallel', 'Runs the same test once for each input set', 'Skips the test', 'Makes the test faster'], 1,
          'Each tuple of values becomes a separate test case with its own pass or fail.'),
    ],
}

L6 = {
    'id': 'dj6', 'num': '2.3', 'title': 'Calling real APIs safely', 'minutes': 60,
    'summaryHtml': '<p>Address autofill from a PIN code: a reusable <code>requests.Session</code>, automatic retries with backoff, timeouts on every call, a timing context manager, and a generator for files too big for memory.</p>',
    'contentHtml': '\n'.join([
        '<h3>The feature</h3>',
        '<p>On a booking or checkout form the customer types a 6-digit PIN code and the district and state fill in. Your code calls a public API, and public APIs are slow, flaky and sometimes down.</p>',
        '<h3>Validate before you call</h3>',
        code('''
if not (pin.isdigit() and len(pin) == 6):
    raise ValueError("PIN code must be 6 digits")
'''),
        '<p>Never send a request you already know is wrong. It wastes time and counts against rate limits.</p>',
        '<h3>A session with retries</h3>',
        code('''
def build_session() -> requests.Session:
    session = requests.Session()
    retry = Retry(total=3, backoff_factor=0.5, status_forcelist=(429, 500, 502, 503, 504), allowed_methods=("GET",))
    session.mount("https://", HTTPAdapter(max_retries=retry))
    session.headers.update({"Accept": "application/json", "User-Agent": "bookit/1.0"})
    return session
'''),
        '<p>A session reuses the TCP connection between calls. The retry policy handles “server busy” (429) and server errors (5xx) automatically, waiting longer each time. It only retries <code>GET</code>, because retrying a <code>POST</code> could charge a customer twice.</p>',
        '<h3>ALWAYS set a timeout</h3>',
        code('resp = session.get(API.format(pin=pin), timeout=(3, 10))  # (connect, read) seconds'),
        '<div class="warn">Without a timeout, <code>requests</code> can wait forever. One hung API call holds a web worker, and a few of them take your whole site down.</div>',
        '<h3>Check the answer, not just the status code</h3>',
        code('''
resp.raise_for_status()
payload = resp.json()[0]
if payload.get("Status") != "Success" or not payload.get("PostOffice"):
    raise PincodeNotFound(pin)
return [PostOffice(p["Name"], p["District"], p["State"]) for p in payload["PostOffice"]]
'''),
        '<p>This API returns HTTP 200 even for an unknown PIN, with <code>"Status": "Error"</code> in the body. Convert the raw JSON into your own small dataclass so the rest of the code does not depend on the API’s field names.</p>',
        '<h3>logging, not print</h3>',
        '<p>Use <code>logger = logging.getLogger(__name__)</code> and lazy formatting: <code>logger.info("pin=%s", pin)</code>, not an f-string. Logs carry a level and a source, can be switched off per module, and go to Railway’s log viewer in production. <code>print</code> does none of that.</p>',
        '<h3>Context managers and generators</h3>',
        '<p><code>@contextmanager</code> turns a function with one <code>yield</code> into a <code>with</code> block. The <code>timer</code> logs how long the block took, even if it raised.</p>',
        '<p>A generator function uses <code>yield</code> to hand back one batch at a time. <code>read_in_batches()</code> can process a 2 GB log file using the memory of 1,000 lines.</p>',
        code('''
def read_in_batches(path: str, size: int = 1000):
    batch = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            batch.append(line.rstrip("\\n"))
            if len(batch) == size:
                yield batch
                batch = []
    if batch:
        yield batch
'''),
    ]),
    'terms': [
        {'term': 'requests.Session', 'definition': 'Reuses connections and shared headers across many HTTP calls.'},
        {'term': 'Timeout', 'definition': 'The longest time to wait to connect and to read. Always pass one to requests.'},
        {'term': 'Retry / backoff', 'definition': 'urllib3’s Retry repeats failed requests, waiting longer each time.'},
        {'term': 'Idempotent', 'definition': 'Safe to repeat: GET is, a payment POST is not. Only retry idempotent requests automatically.'},
        {'term': 'raise_for_status()', 'definition': 'Raises an HTTPError for 4xx and 5xx responses.'},
        {'term': 'Context manager', 'definition': 'An object used with with that runs setup and guaranteed cleanup code.'},
        {'term': 'Generator', 'definition': 'A function that yields values lazily, one at a time, instead of returning a full list.'},
    ],
    'examTip': '“What happens if the third-party API is down?” is a standard design question. Answer with timeouts, limited retries with backoff for idempotent calls, a clear error to the user, and logging.',
    'lab': {
        'files': f('day2/pincode_client.py'),
        'steps': [
            'pip install requests, then run python pincode_client.py. It looks up PIN 679322 and logs how long it took.',
            'Call lookup("12345") and lookup("000000") in a Python shell. Note which raises ValueError and which raises PincodeNotFound.',
            'Add a simple cache: a dict in the module that returns the stored answer for a PIN already looked up. Log "cache hit" when it is used.',
            'Change the timeout to (0.001, 0.001) and run again. Read the exception, then put the timeout back.',
            'Write a function count_lines(path) that uses read_in_batches() to count lines in a large file without loading it.',
        ],
        'check': [
            'lookup("679322") returns post offices in Malappuram district, Kerala.',
            'A second lookup of the same PIN logs "cache hit" and takes under 1 ms.',
            'The tiny timeout raises a requests ConnectTimeout or ReadTimeout instead of hanging.',
        ],
    },
    'quiz': [
        q('What can happen if you call requests.get() without a timeout?',
          ['It raises an error immediately', 'The call can wait forever and block a web worker', 'It defaults to 5 seconds', 'Nothing, requests always has a timeout'], 1,
          'requests has no default timeout. A hung call ties up the worker until the server or the process gives up.'),
        q('Why does the Retry policy only allow GET?',
          ['POST is slower', 'GET is idempotent; retrying a POST could create a second order or payment', 'urllib3 cannot retry POST', 'The API only supports GET'], 1,
          'Only safe, repeatable requests should be retried automatically.'),
        q('The PIN API returns HTTP 200 for an unknown PIN. How does the client detect it?',
          ['raise_for_status()', 'By checking payload["Status"] and that PostOffice is not empty', 'By the response time', 'It cannot'], 1,
          'Some APIs report errors in the body, so the client checks the body as well as the status code.'),
        q('Why use a generator to read a 2 GB file?',
          ['It is the only way to open files', 'It keeps only one batch in memory at a time', 'It makes the file smaller', 'It sorts the lines'], 1,
          'A generator yields one batch at a time, so memory use stays small whatever the file size.'),
    ],
}

L7 = {
    'id': 'dj7', 'num': '3.1', 'title': 'A Django project laid out for production', 'minutes': 75,
    'summaryHtml': '<p>BookIt, a booking system for a car-wash business, set up the way Ralfiz projects are: split settings, secrets from <code>.env</code>, apps under <code>apps/</code>, a custom User model from day one, and a small middleware.</p>',
    'contentHtml': '\n'.join([
        '<h3>The project</h3>',
        '<p>For the rest of the course you work on <strong>BookIt</strong>: customers book services (Full Car Wash, Interior Detailing), staff manage bookings in a dashboard, and a mobile app talks to a REST API. Download the whole project from the course page (Course files).</p>',
        code('''
bookit/
  config/
    settings/base.py  dev.py  prod.py
    urls.py  wsgi.py
  apps/
    core/        TimeStampedModel, middleware
    accounts/    custom User with roles
    catalog/     Service
    bookings/    Booking, services.py (business rules)
    dashboard/   staff web pages
    api/         DRF API for the app
  templates/
  requirements/base.txt  dev.txt  prod.txt
  .env.example  manage.py  pytest.ini
'''),
        '<h3>How a request flows through Django</h3>',
        '<p><strong>Browser / Flutter app → Gunicorn → Middleware → URLconf → View → Service layer → Model / ORM → PostgreSQL</strong>, and the response travels back through the middleware in reverse order. When something breaks, ask which layer it broke in. That one question solves half of all debugging.</p>',
        '<p>Project = configuration (<code>config/</code>). App = one business area (<code>bookings</code>, <code>catalog</code>). MVT: Model (data), View (request → response logic), Template (HTML).</p>',
        '<h3>Split settings</h3>',
        '<p><code>base.py</code> holds everything shared. <code>dev.py</code> and <code>prod.py</code> start with <code>from .base import *</code> and change only what differs: DEBUG, allowed hosts, HTTPS, static storage.</p>',
        '<h3>Secrets come from the environment</h3>',
        code('''
env = environ.Env(DEBUG=(bool, False))
environ.Env.read_env(BASE_DIR / ".env")

SECRET_KEY = env("SECRET_KEY")
DEBUG = env("DEBUG")
DATABASES = {"default": env.db("DATABASE_URL")}
'''),
        '<p>The real <code>.env</code> is never committed; <code>.env.example</code> shows which variables exist. <code>DEBUG</code> defaults to <code>False</code>, so forgetting it in production is safe.</p>',
        '<ul>',
        '<li><code>USE_TZ = True</code> and <code>TIME_ZONE = "Asia/Kolkata"</code>: the database stores UTC and users see IST. Gulf and UK clients just change the display zone.</li>',
        '<li><code>django.contrib.admin</code> is not installed. Clients get a custom dashboard (Day 4).</li>',
        '</ul>',
        '<h3>A custom User from day one</h3>',
        code('''
class User(AbstractUser):
    """Custom user from day one — changing AUTH_USER_MODEL later is painful."""

    class Role(models.TextChoices):
        ADMIN = "admin", "Admin"
        STAFF = "staff", "Staff"
        CUSTOMER = "customer", "Customer"

    role = models.CharField(max_length=20, choices=Role.choices, default=Role.CUSTOMER)
    phone = models.CharField(max_length=15, unique=True, null=True, blank=True)

    @property
    def is_staff_member(self) -> bool:
        return self.role in {self.Role.ADMIN, self.Role.STAFF}
'''),
        '<p>Set <code>AUTH_USER_MODEL = "accounts.User"</code> before the first migration. Switching later means rewriting every foreign key to users. Note <code>phone</code> is <code>null=True</code> with <code>unique=True</code>: many users may have no phone, and NULLs do not clash, but empty strings would.</p>',
        '<h3>Middleware</h3>',
        '<p>Middleware wraps every request. <code>SlowRequestLogMiddleware</code> times the request, logs any slower than 500 ms and adds an <code>X-Response-Time-ms</code> header.</p>',
        code('''
class SlowRequestLogMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start = time.perf_counter()
        response = self.get_response(request)
        elapsed_ms = (time.perf_counter() - start) * 1000
        if elapsed_ms > SLOW_MS:
            logger.warning("SLOW %s %s took %.0f ms", request.method, request.path, elapsed_ms)
        response["X-Response-Time-ms"] = f"{elapsed_ms:.0f}"
        return response
'''),
        '<h3>Run it</h3>',
        code('''
python -m venv venv && source venv/bin/activate
pip install -r requirements/dev.txt
cp .env.example .env            # then edit DATABASE_URL and SECRET_KEY
export DJANGO_SETTINGS_MODULE=config.settings.dev
python manage.py migrate
python manage.py seed_demo
python manage.py createsuperuser   # then set role="admin" in the shell
python manage.py runserver
'''),
        '<div class="callout">No PostgreSQL on your laptop yet? Set <code>DATABASE_URL=sqlite:///db.sqlite3</code> in <code>.env</code> to start. The course uses PostgreSQL in production, like Ralfiz BMS on Railway.</div>',
    ]),
    'terms': [
        {'term': 'Split settings', 'definition': 'A settings package with base.py plus one file per environment that imports from base.'},
        {'term': 'django-environ', 'definition': 'Reads settings such as SECRET_KEY and DATABASE_URL from environment variables or a .env file.'},
        {'term': 'AUTH_USER_MODEL', 'definition': 'The setting that points Django at your custom User model. Set it before the first migrate.'},
        {'term': 'TextChoices', 'definition': 'A Django enum for a field’s allowed values and their human labels.'},
        {'term': 'Middleware', 'definition': 'A class that runs code before and after every request and response.'},
        {'term': 'App', 'definition': 'A Django package for one area of the business (catalog, bookings) with its own models and migrations.'},
    ],
    'examTip': 'If asked “why a custom user model?”, say: Django’s own docs recommend it for every new project, because adding fields like role or phone later requires a painful migration.',
    'lab': {
        'files': f('bookit/config/settings/base.py', 'bookit/config/settings/dev.py', 'bookit/config/settings/prod.py',
                   'bookit/.env.example', 'bookit/apps/accounts/models.py', 'bookit/apps/core/middleware.py',
                   'bookit/apps/core/models.py', 'bookit/requirements/base.txt', 'bookit/requirements/dev.txt'),
        'steps': [
            'Download the full BookIt project from Course files on the course page and unzip it.',
            'Create a virtual environment, install requirements/dev.txt, copy .env.example to .env and set DATABASE_URL (SQLite is fine to start).',
            'Run migrate, then seed_demo, then runserver with DJANGO_SETTINGS_MODULE=config.settings.dev.',
            'Create a superuser, then in python manage.py shell set its role to "admin" and save it. Log in at /accounts/login/.',
            'Open any page and find the X-Response-Time-ms header in the browser’s Network tab.',
            'Add a LOG_LEVEL=DEBUG line to .env and restart. Notice how much more is logged, then set it back to INFO.',
        ],
        'check': [
            'seed_demo prints Seeded 200 bookings, 10 customers.',
            'You can log in and see the Overview page with four numbers.',
            'Every response has an X-Response-Time-ms header.',
        ],
    },
    'quiz': [
        q('Why must AUTH_USER_MODEL be set before the first migration?',
          ['Django ignores it later', 'Every foreign key to users is created against it; changing it later means rewriting those tables', 'It makes login faster', 'It is required for the admin'], 1,
          'Migrations bake the user table into every relation. Changing the model after data exists is a hard, risky migration.'),
        q('Where should SECRET_KEY come from in production?',
          ['Hard-coded in settings.py', 'An environment variable', 'The database', 'A comment in urls.py'], 1,
          'Secrets live in the environment (Railway variables, a local .env) and are never committed to git.'),
        q('Why is phone defined with null=True as well as unique=True?',
          ['To save space', 'Many users have no phone; NULLs do not clash under a unique constraint but empty strings would', 'Django requires it for CharField', 'So phones can be duplicated'], 1,
          'Two empty strings are equal and would break uniqueness. Two NULLs are not considered equal.'),
        q('What does middleware wrap?',
          ['Only API requests', 'Every request and response passing through Django', 'Only database queries', 'Only templates'], 1,
          'Each middleware runs around every request, which is why it suits timing, security headers and confinement rules.'),
    ],
}

L8 = {
    'id': 'dj8', 'num': '3.2', 'title': 'Models that protect your data', 'minutes': 75,
    'summaryHtml': '<p>Service and Booking: a timestamp base class, <code>TextChoices</code>, a price snapshot, <code>on_delete</code> choices, indexes, a database <code>CheckConstraint</code> and a tiny status state machine.</p>',
    'contentHtml': '\n'.join([
        '<h3>A base class for every table</h3>',
        code('''
class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
'''),
        '<p><code>abstract = True</code> means no table of its own; every model that inherits gets the two columns.</p>',
        '<h3>The Booking model</h3>',
        code('''
class Booking(TimeStampedModel):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        CONFIRMED = "confirmed", "Confirmed"
        COMPLETED = "completed", "Completed"
        CANCELLED = "cancelled", "Cancelled"

    customer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="bookings")
    staff = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
                              related_name="assigned_bookings", limit_choices_to={"role": "staff"})
    service = models.ForeignKey(Service, on_delete=models.PROTECT, related_name="bookings")
    start_at = models.DateTimeField()
    end_at = models.DateTimeField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    # Snapshot of the price at booking time — later price changes must not rewrite history
    price = models.DecimalField(max_digits=10, decimal_places=2)
'''),
        '<h3>on_delete is a business decision</h3>',
        '<table><thead><tr><th>Choice</th><th>Meaning here</th></tr></thead><tbody>',
        '<tr><td><code>PROTECT</code></td><td>You cannot delete a customer or service that has bookings. Revenue history must survive.</td></tr>',
        '<tr><td><code>SET_NULL</code></td><td>If a staff member leaves, their bookings stay with no staff assigned.</td></tr>',
        '<tr><td><code>CASCADE</code></td><td>Delete the children too. Fine for things like a booking’s notes, dangerous for money.</td></tr>',
        '</tbody></table>',
        '<h3>Snapshot the price</h3>',
        '<p>The service price will go up next year. Last year’s bookings must still show what the customer actually paid, so the booking copies the price when it is created instead of reading <code>service.price</code> later.</p>',
        '<h3>Rules the database enforces</h3>',
        code('''
class Meta:
    ordering = ["-start_at"]
    indexes = [
        models.Index(fields=["status", "start_at"]),
        models.Index(fields=["service", "start_at"]),
    ]
    constraints = [
        models.CheckConstraint(condition=Q(end_at__gt=F("start_at")), name="booking_end_after_start"),
    ]
'''),
        '<p>Python validation can be skipped by a bulk update, a shell session or another program. A <code>CheckConstraint</code> cannot. The indexes match the dashboard’s most common filters: by status and date, and by service and date.</p>',
        '<h3>A status state machine</h3>',
        code('''
ALLOWED_TRANSITIONS = {
    Status.PENDING: {Status.CONFIRMED, Status.CANCELLED},
    Status.CONFIRMED: {Status.COMPLETED, Status.CANCELLED},
    Status.COMPLETED: set(),
    Status.CANCELLED: set(),
}

def can_transition_to(self, new_status: str) -> bool:
    return new_status in self.ALLOWED_TRANSITIONS[self.status]
'''),
        '<p>A completed booking can never be cancelled and a cancelled one can never be completed. The rule lives in one dictionary that anyone can read.</p>',
        '<div class="callout">The <code>Service</code> model has its own constraint: <code>CheckConstraint(condition=Q(price__gte=0), name="service_price_non_negative")</code>. Every rule that must never break belongs in the database.</div>',
        '<h3>Migrations: the rules</h3>',
        '<ul>',
        '<li>Commit migration files with the model change, in the same PR.</li>',
        '<li>Never edit a migration that has already run on a shared database or in production. Create a new one.</li>',
        '<li>Two people changing the same app at once causes migration conflicts. Talk before touching models.</li>',
        '<li>Adding a non-null column to a big table needs a default or a 3-step migration. Ask a senior first.</li>',
        '</ul>',
        '<h3>The brief: BookIt data layer</h3>',
        '<p>A car wash chain wants online bookings. Today you deliver the database design and the reports the owner asked for in the kickoff meeting. Acceptance: <code>python manage.py check</code> is clean and migrations are committed; saving a booking with <code>end_at</code> before <code>start_at</code> raises <code>IntegrityError</code>; deleting a booked service raises <code>ProtectedError</code>.</p>',
        '<p><strong>Stretch goal:</strong> use PostgreSQL’s <code>ExclusionConstraint</code> (from <code>django.contrib.postgres</code>) to make overlapping active bookings for the same service impossible at the database level.</p>',
    ]),
    'terms': [
        {'term': 'Abstract model', 'definition': 'A base model with Meta.abstract = True; it adds fields to subclasses but has no table.'},
        {'term': 'on_delete', 'definition': 'What happens to rows pointing at a deleted row: PROTECT, CASCADE, SET_NULL and others.'},
        {'term': 'related_name', 'definition': 'The name for the reverse relation, e.g. service.bookings.all().'},
        {'term': 'CheckConstraint', 'definition': 'A rule enforced by the database itself on every insert and update.'},
        {'term': 'Index', 'definition': 'A database structure that makes filtering and sorting on given columns fast.'},
        {'term': 'Price snapshot', 'definition': 'Copying a value at the time of a transaction so later changes do not rewrite history.'},
        {'term': 'State machine', 'definition': 'A fixed set of states and the allowed moves between them.'},
    ],
    'examTip': 'When asked about on_delete, give a reason per relation. Choosing CASCADE on a customer that has invoices is a classic way to lose financial data.',
    'lab': {
        'files': f('bookit/apps/core/models.py', 'bookit/apps/catalog/models.py', 'bookit/apps/bookings/models.py',
                   'bookit/apps/bookings/migrations/0001_initial.py'),
        'steps': [
            'Open apps/bookings/models.py and apps/catalog/models.py and match each field to a column in migrations/0001_initial.py.',
            'In python manage.py shell, try to delete a service that has bookings. Read the ProtectedError.',
            'Try Booking.objects.filter(pk=1).update(end_at=F("start_at")). Read the IntegrityError from the constraint.',
            'Add a NO_SHOW status that is allowed only from CONFIRMED. Update ALLOWED_TRANSITIONS and run makemigrations.',
            'Add a discount DecimalField to Booking with a CheckConstraint that it is between 0 and price. Run makemigrations and migrate.',
        ],
        'check': [
            'Deleting a booked service raises ProtectedError and the service still exists.',
            'The update that sets end_at equal to start_at fails with an IntegrityError naming booking_end_after_start.',
            'Your new migration applies cleanly and Booking.Status.NO_SHOW exists.',
        ],
    },
    'quiz': [
        q('Why does Booking store its own price instead of reading service.price?',
          ['To save a query', 'So a later price change does not rewrite what past customers paid', 'Django requires it', 'Because DecimalField cannot be a foreign key'], 1,
          'The booking keeps a snapshot of the agreed price. Reports and invoices for old bookings stay correct.'),
        q('Which on_delete stops you deleting a customer who has bookings?',
          ['CASCADE', 'SET_NULL', 'PROTECT', 'DO_NOTHING'], 2,
          'PROTECT raises ProtectedError while related rows exist.'),
        q('Why use a CheckConstraint when the form already validates end_at > start_at?',
          ['Forms are slow', 'The database enforces it for every write, including bulk updates and scripts that skip the form', 'Constraints replace forms', 'It is needed for indexes'], 1,
          'Code paths that bypass forms still cannot write invalid rows.'),
        q('With the ALLOWED_TRANSITIONS shown, which move is allowed?',
          ['completed → cancelled', 'cancelled → confirmed', 'pending → confirmed', 'completed → pending'], 2,
          'Pending can become confirmed or cancelled. Completed and cancelled are final.'),
        q('A migration has already run on production and has a mistake. What do you do?',
          ['Edit the migration file and redeploy', 'Write a new migration that fixes it', 'Delete the migration', 'Drop the table'], 1,
          'Production has recorded that migration as applied, so edits never run there. Fix forward with a new migration.'),
    ],
}

L9 = {
    'id': 'dj9', 'num': '3.3', 'title': 'ORM reports and the N+1 problem', 'minutes': 75,
    'summaryHtml': '<p>The queries behind every dashboard: <code>select_related</code>, <code>aggregate</code>, <code>annotate</code> with conditional counts, group-by-date, <code>Q</code> searches, <code>F</code> updates, and measuring the N+1 problem yourself.</p>',
    'contentHtml': '\n'.join([
        '<h3>Think in queries, not loops</h3>',
        '<p>The database is far better at filtering, counting and adding up than a Python loop. Every report below is a single SQL query. Paste them into <code>python manage.py shell</code> one by one and print <code>.query</code> to see the SQL.</p>',
        '<h3>Aggregate: one number</h3>',
        code('''
month = Booking.objects.filter(
    status=S.COMPLETED, start_at__year=today.year, start_at__month=today.month
).aggregate(revenue=Sum("price"), jobs=Count("id"))
# a dict: {'revenue': Decimal(...), 'jobs': ...}
'''),
        '<h3>Annotate: a number per row</h3>',
        code('''
popular = Service.objects.annotate(
    total=Count("bookings"),
    cancelled=Count("bookings", filter=Q(bookings__status=S.CANCELLED)),
).order_by("-total")
'''),
        '<p>The <code>filter=Q(...)</code> inside <code>Count</code> gives a conditional count in the same query.</p>',
        '<h3>Group by date for a chart</h3>',
        code('''
daily = (
    Booking.objects.filter(status=S.COMPLETED, start_at__date__gte=today - timedelta(days=30))
    .annotate(day=TruncDate("start_at"))
    .values("day")
    .annotate(revenue=Sum("price"))
    .order_by("day")
)
'''),
        '<p>The pattern <code>.values(&lt;group&gt;).annotate(&lt;aggregate&gt;)</code> is SQL’s GROUP BY.</p>',
        '<h3>Search across relations</h3>',
        code('''
found = Booking.objects.filter(
    Q(customer__first_name__icontains=q) | Q(customer__phone__icontains=q) | Q(service__name__icontains=q)
)
'''),
        '<h3>Update in the database with F()</h3>',
        code('Service.objects.filter(slug="bike-wash").update(price=F("price") + Decimal("20"))'),
        '<p>Reading the price into Python, adding 20 and saving would lose a change made by someone else at the same moment. <code>F()</code> does the arithmetic inside the database in one statement.</p>',
        '<h3>The N+1 problem, measured</h3>',
        code('''
reset_queries()
for b in Booking.objects.all()[:50]:
    _ = (b.customer.first_name, b.service.name)   # each access = a new query
print("without select_related:", len(connection.queries))  # 101

reset_queries()
for b in Booking.objects.select_related("customer", "service")[:50]:
    _ = (b.customer.first_name, b.service.name)
print("with select_related:", len(connection.queries))     # 1
'''),
        '<p>One query for the bookings plus one per booking for the customer and one for the service: 1 + 50 + 50 = 101. <code>select_related</code> joins them into a single query. Use it for foreign keys you will display; use <code>prefetch_related</code> for reverse and many-to-many relations.</p>',
        '<div class="warn">A page that is fast with 10 rows in development and slow with 5,000 in production is almost always N+1. Check with django-debug-toolbar (in requirements/dev.txt).</div>',
    ]),
    'terms': [
        {'term': 'QuerySet', 'definition': 'A lazy description of a query; it runs only when you iterate, slice with a step, count or print it.'},
        {'term': 'aggregate()', 'definition': 'Returns a dict of totals over the whole QuerySet.'},
        {'term': 'annotate()', 'definition': 'Adds a computed value to every row (or every group after values()).'},
        {'term': 'Q object', 'definition': 'A filter condition that can be combined with | (OR), & (AND) and ~ (NOT).'},
        {'term': 'F expression', 'definition': 'Refers to a column’s value inside the database, for updates and comparisons.'},
        {'term': 'N+1 problem', 'definition': 'One query for a list plus one more for each row’s related object.'},
        {'term': 'select_related', 'definition': 'Fetches foreign-key objects in the same query using a SQL JOIN.'},
    ],
    'examTip': 'Know the difference: select_related uses a JOIN and works for ForeignKey and OneToOne; prefetch_related runs a second query and joins in Python, for reverse FKs and ManyToMany.',
    'lab': {
        'files': f('snippets/orm_reports.py'),
        'steps': [
            'With the seeded BookIt database, open python manage.py shell and paste snippets/orm_reports.py section by section.',
            'Print todays.query and read the JOIN that select_related produced.',
            'Run the N+1 measurement and note both numbers.',
            'Write a query for revenue per staff member this month, highest first, using annotate and Sum with a filter.',
            'Write a query for the cancellation rate per service (cancelled / total) using two Count annotations.',
        ],
        'check': [
            'The N+1 test prints 101 without select_related and 1 with it.',
            'Your revenue-per-staff query is a single SQL query (check len(connection.queries) is 1).',
            'Your cancellation-rate query returns one row per service with both counts.',
        ],
    },
    'quiz': [
        q('A loop prints b.customer.first_name for 50 bookings with no select_related. Roughly how many queries run?',
          ['1', '2', '51', '500'], 2,
          'One for the bookings, then one per booking for its customer: 51. Adding service.name doubles the extra queries.'),
        q('Which gives one revenue total for the whole month?',
          ['annotate(revenue=Sum("price"))', 'aggregate(revenue=Sum("price"))', 'values("price")', 'select_related("price")'], 1,
          'aggregate returns a single dict over the whole QuerySet; annotate adds a value per row.'),
        q('Why is update(price=F("price") + 20) better than reading, adding and saving in Python?',
          ['It is shorter', 'The database does it in one statement, so a simultaneous change is not lost', 'F() validates the price', 'save() cannot change prices'], 1,
          'Read-modify-write in Python has a race: two requests read the old value and one overwrites the other.'),
        q('Why does Booking.customer use on_delete=PROTECT rather than CASCADE?',
          ['PROTECT is faster', 'Deleting a customer must not silently delete their financial history; deactivate the user instead', 'CASCADE is deprecated', 'PROTECT allows NULL'], 1,
          'Set is_active=False on a customer who leaves. Their bookings and revenue stay correct.'),
        q('How do you search bookings where the customer name OR the service name matches?',
          ['filter(customer__first_name=q, service__name=q)', 'filter(Q(customer__first_name__icontains=q) | Q(service__name__icontains=q))', 'exclude(...)', 'Two separate queries added together'], 1,
          'Keyword arguments in filter() are ANDed; Q objects joined with | give OR.'),
    ],
}

L10 = {
    'id': 'dj10', 'num': '4.1', 'title': 'Business rules in a service layer', 'minutes': 75,
    'summaryHtml': '<p>Where the booking rules live: <code>services.py</code> functions shared by the web dashboard and the API, <code>transaction.atomic</code>, <code>select_for_update</code> to stop double booking, and the overlap test.</p>',
    'contentHtml': '\n'.join([
        '<h3>Why a service layer</h3>',
        '<p>BookIt has two front doors: the staff dashboard and the mobile API. If the “no double booking” rule lived in a view, the API would not have it. Business rules go in plain functions in <code>services.py</code>. Views and serializers only call them.</p>',
        code('''
class BookingError(Exception):
    """A business rule was violated. The message is safe to show users."""
'''),
        '<h3>Creating a booking safely</h3>',
        code('''
@transaction.atomic
def create_booking(*, customer, service: Service, start_at: datetime, staff=None, notes: str = "") -> Booking:
    # Lock the service row: two people clicking "Book" for the same slot at the
    # same moment are now processed one after the other, never both accepted.
    service = Service.objects.select_for_update().get(pk=service.pk)

    if not service.is_active:
        raise BookingError("This service is not available right now.")
    if start_at <= timezone.now():
        raise BookingError("Please choose a time in the future.")

    end_at = start_at + timedelta(minutes=service.duration_minutes)
    clash = Booking.objects.filter(
        service=service,
        status__in=Booking.ACTIVE_STATUSES,
        start_at__lt=end_at,  # overlap test: A.start < B.end AND A.end > B.start
        end_at__gt=start_at,
    ).exists()
    if clash:
        raise BookingError("That slot was just taken. Please pick another time.")

    return Booking.objects.create(..., price=service.price, ...)
'''),
        '<h3>The race condition</h3>',
        '<p>Without a lock, two customers can both run the clash check at the same instant, both see “free”, and both get booked. <code>select_for_update()</code> locks the service row until the transaction ends, so the second request waits, then sees the first booking and is rejected.</p>',
        '<div class="warn"><code>select_for_update()</code> only works inside a transaction, which is why the function is wrapped in <code>@transaction.atomic</code>. On SQLite it does nothing; it needs PostgreSQL, which is what production uses.</div>',
        '<h3>The overlap test</h3>',
        '<p>Two time ranges overlap when <strong>A starts before B ends AND A ends after B starts</strong>. That one condition covers every case: partly before, partly after, inside, around. Back-to-back bookings (10:00–11:00 and 11:00–12:00) do not clash because the comparisons are strict.</p>',
        '<h3>Changing status</h3>',
        code('''
@transaction.atomic
def change_status(*, booking: Booking, new_status: str, by) -> Booking:
    booking = Booking.objects.select_for_update().get(pk=booking.pk)
    if not booking.can_transition_to(new_status):
        raise BookingError(f"A {booking.get_status_display().lower()} booking cannot become '{new_status}'.")
    if not by.is_staff_member and booking.customer_id != by.pk:
        raise BookingError("You can only change your own bookings.")
    booking.status = new_status
    booking.save(update_fields=["status", "updated_at"])
    return booking
'''),
        '<p><code>save(update_fields=[...])</code> writes only those columns, so it cannot overwrite a field another request just changed.</p>',
        '<h3>Free slots</h3>',
        '<p><code>available_slots()</code> fetches the taken ranges for the day in one query, then walks the opening hours in 30-minute steps and keeps slots in the future that overlap nothing. All times are timezone-aware (<code>USE_TZ = True</code>, <code>TIME_ZONE = "Asia/Kolkata"</code>).</p>',
    ]),
    'terms': [
        {'term': 'Service layer', 'definition': 'Plain functions holding business rules, called by both views and API code.'},
        {'term': 'transaction.atomic', 'definition': 'Runs a block in a database transaction: all of it is saved, or none of it.'},
        {'term': 'select_for_update', 'definition': 'Locks the selected rows until the transaction ends, so concurrent requests wait their turn.'},
        {'term': 'Race condition', 'definition': 'A bug where the result depends on the timing of two simultaneous operations.'},
        {'term': 'Overlap test', 'definition': 'A.start < B.end and A.end > B.start.'},
        {'term': 'update_fields', 'definition': 'save(update_fields=[...]) writes only the listed columns.'},
        {'term': 'Aware datetime', 'definition': 'A datetime with a timezone attached. Django stores UTC and shows local time.'},
    ],
    'examTip': '“How do you prevent double booking?” Answer: a transaction, a row lock with select_for_update (or a unique/exclusion constraint), and checking the overlap after the lock is taken.',
    'lab': {
        'files': f('bookit/apps/bookings/services.py', 'bookit/apps/bookings/models.py'),
        'steps': [
            'Read apps/bookings/services.py from top to bottom and find where each BookingError is raised.',
            'In the shell, create a booking for tomorrow 10:00 with create_booking, then try 10:30 for the same service. Read the error.',
            'Book 11:00 (right after a 60-minute 10:00 booking) and confirm it is accepted.',
            'Add a rule: a customer may have at most 3 active bookings. Raise BookingError with a clear message.',
            'Change available_slots so that slots on Sundays return an empty list.',
        ],
        'check': [
            'The 10:30 booking raises "That slot was just taken. Please pick another time."',
            'The back-to-back 11:00 booking succeeds.',
            'A fourth active booking for the same customer raises your new BookingError.',
        ],
    },
    'quiz': [
        q('Why are booking rules in services.py instead of the dashboard view?',
          ['Views cannot raise exceptions', 'The API and the dashboard both call the same function, so the rules are written and tested once', 'Django requires services.py', 'It makes templates faster'], 1,
          'One function, two callers. A rule in a view would be missing from the API.'),
        q('What does select_for_update() protect against in create_booking?',
          ['SQL injection', 'Two simultaneous requests both seeing the slot as free and both booking it', 'Slow queries', 'Invalid prices'], 1,
          'The lock makes the second request wait until the first commits, then its clash check sees the new booking.'),
        q('Booking A is 10:00–11:00. Which new booking clashes?',
          ['11:00–12:00', '09:00–10:00', '10:30–11:30', '12:00–13:00'], 2,
          '10:30 < 11:00 and 11:30 > 10:00, so it overlaps. Back-to-back slots do not.'),
        q('Why save(update_fields=["status", "updated_at"])?',
          ['It is required after select_for_update', 'Only those columns are written, so other fields changed elsewhere are not overwritten', 'It skips validation', 'It deletes the old row'], 1,
          'A plain save() writes every column from the in-memory object, which can undo someone else’s change.'),
    ],
}

L11 = {
    'id': 'dj11', 'num': '4.2', 'title': 'The staff dashboard', 'minutes': 75,
    'summaryHtml': '<p>Server-rendered pages with class-based views: a KPI home page, a searchable, filterable, paginated booking list, POST-only status changes with messages, and ModelForms with custom validation.</p>',
    'contentHtml': '\n'.join([
        '<h3>Why we don’t give clients the Django admin</h3>',
        '<table><thead><tr><th>Django admin</th><th>Custom dashboard</th></tr></thead><tbody>',
        '<tr><td>Generic look, hard to brand</td><td>Branded, modern UI</td></tr>',
        '<tr><td>Exposes every model</td><td>Shows only what that role needs</td></tr>',
        '<tr><td>Model-level permissions</td><td>Business-level permissions</td></tr>',
        '<tr><td>Workflows (approve, assign, refund) are awkward</td><td>Business actions are buttons that call service functions, with the same rules as the API</td></tr>',
        '</tbody></table>',
        '<p>The brief: the car wash manager opens the dashboard every morning on a laptop at the counter. They need today’s numbers at a glance, to find a customer by phone in two seconds, and to move bookings through their workflow without mistakes.</p>',
        '<h3>Who may see it</h3>',
        code('''
class StaffRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Logged-in AND role is admin/staff. Customers get 403, guests go to login."""

    def test_func(self):
        return self.request.user.is_staff_member
'''),
        '<p>Every dashboard view lists this mixin first. Login alone is not enough: a customer who logs in must get 403, not the business numbers.</p>',
        '<h3>KPIs in get_context_data</h3>',
        code('''
class DashboardHomeView(StaffRequiredMixin, TemplateView):
    template_name = "dashboard/home.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ...
        ctx["kpis"] = {
            "today": bookings.filter(start_at__date=today).count(),
            "pending": bookings.filter(status=Booking.Status.PENDING).count(),
            "month_revenue": completed_this_month.aggregate(total=Sum("price"))["total"] or 0,
            "month_completed": completed_this_month.count(),
        }
        ctx["upcoming"] = (...).select_related("customer", "service", "staff").order_by("start_at")[:8]
'''),
        '<p>Note <code>or 0</code>: <code>Sum</code> over no rows is <code>None</code>, not 0.</p>',
        '<h3>A list with search, filter and pagination</h3>',
        code('''
class BookingListView(StaffRequiredMixin, ListView):
    template_name = "dashboard/bookings/list.html"
    context_object_name = "bookings"
    paginate_by = 20

    def get_queryset(self):
        qs = Booking.objects.select_related("customer", "service", "staff")
        q = self.request.GET.get("q", "").strip()
        status = self.request.GET.get("status", "")
        if q:
            qs = qs.filter(Q(customer__first_name__icontains=q) | Q(customer__phone__icontains=q) | Q(service__name__icontains=q))
        if status in Booking.Status.values:
            qs = qs.filter(status=status)
        return qs
'''),
        '<p>Only known statuses are applied (<code>status in Booking.Status.values</code>), so a tampered URL cannot cause an error. In the template, keep <code>q</code> and <code>status</code> in the pagination links so page 2 keeps the filter.</p>',
        '<h3>Changes are POST only</h3>',
        code('''
@require_POST
@login_required
def booking_change_status(request, pk):
    if not request.user.is_staff_member:
        raise PermissionDenied
    booking = get_object_or_404(Booking, pk=pk)
    try:
        change_status(booking=booking, new_status=request.POST.get("status", ""), by=request.user)
        messages.success(request, "Booking status updated.")
    except BookingError as exc:
        messages.error(request, str(exc))
    return redirect("dashboard:booking-detail", pk=pk)
'''),
        '<p>A GET link that changes data can be triggered by a browser prefetch or an image tag on another site. POST plus <code>{% csrf_token %}</code> prevents that. After the POST, redirect (Post/Redirect/Get) so a refresh does not submit again.</p>',
        '<h3>ModelForm with a custom rule</h3>',
        code('''
class ServiceForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = Service
        fields = ["name", "slug", "description", "duration_minutes", "price", "gst_rate", "is_active"]

    def clean_duration_minutes(self):
        minutes = self.cleaned_data["duration_minutes"]
        if minutes % 15:
            raise forms.ValidationError("Duration must be in 15-minute steps.")
        return minutes
'''),
        '<p>Always list <code>fields</code> explicitly. <code>fields = "__all__"</code> silently exposes every new column you add later. <code>StyledFormMixin</code> adds CSS classes to every widget so templates stay clean.</p>',
        '<div class="callout">Django 5 only logs out on POST. That is why base.html has a small logout form with a button rather than a link.</div>',
        '<h3>Templates and URLs</h3>',
        '<ul>',
        '<li>Every URL file has an <code>app_name</code>; templates use <code>{% url \'dashboard:booking-list\' %}</code>. Never hard-code paths: if a prefix changes, reversed names keep working.</li>',
        '<li>One <code>base.html</code> with blocks; every page <code>{% extends %}</code> it.</li>',
        '<li>Django auto-escapes variables, so XSS is blocked by default. Never use <code>|safe</code> on user input.</li>',
        '<li><code>{% querystring page=... %}</code> (Django 5.1+) keeps the search and filter parameters when paging.</li>',
        '<li>The Tailwind CDN is fine for training. In production, build the CSS with the Tailwind CLI and serve the file.</li>',
        '</ul>',
        '<h3>Middleware and signals: use carefully</h3>',
        '<p>Middleware suits cross-cutting concerns: timing, audit logs, tenant detection in white-label SaaS. Signals (<code>post_save</code>) hide logic and make code hard to follow; prefer explicit calls in the service layer. If you do send an email or notification, do it in <code>transaction.on_commit(...)</code> so you never notify about a booking that was rolled back.</p>',
        '<h3>Acceptance criteria</h3>',
        '<ul>',
        '<li>No <code>django.contrib.admin</code> in <code>INSTALLED_APPS</code>.</li>',
        '<li>The bookings list runs at most 3 queries per page (check with django-debug-toolbar).</li>',
        '<li>Status changes go through <code>services.change_status</code> only.</li>',
        '<li>Works on a 13" laptop and at mobile width.</li>',
        '</ul>',
        '<p><strong>Stretch goals:</strong> a 14-day revenue bar chart (Chart.js); CSV export of the filtered bookings; assign staff from the detail page.</p>',
    ]),
    'terms': [
        {'term': 'Class-based view (CBV)', 'definition': 'A view written as a class (TemplateView, ListView, DetailView, CreateView, UpdateView).'},
        {'term': 'Mixin', 'definition': 'A small class that adds one behaviour, such as a permission check, to a view.'},
        {'term': 'get_context_data', 'definition': 'The CBV method that builds the dict passed to the template.'},
        {'term': 'Pagination', 'definition': 'Splitting a long list into pages; ListView does it with paginate_by.'},
        {'term': 'CSRF', 'definition': 'Cross-site request forgery: another site making your browser submit a form. The csrf_token blocks it.'},
        {'term': 'Post/Redirect/Get', 'definition': 'After a successful POST, redirect so refreshing the page does not repeat the action.'},
        {'term': 'ModelForm', 'definition': 'A form generated from a model’s fields, with clean_<field> methods for extra rules.'},
    ],
    'examTip': 'Permission checks belong on the server for every view, including POST handlers. Hiding a button in the template is not security.',
    'lab': {
        'files': f('bookit/apps/dashboard/views.py', 'bookit/apps/dashboard/mixins.py', 'bookit/apps/dashboard/urls.py',
                   'bookit/apps/catalog/forms.py', 'bookit/templates/base.html', 'bookit/templates/dashboard/home.html',
                   'bookit/templates/dashboard/bookings/list.html', 'bookit/templates/dashboard/bookings/detail.html'),
        'steps': [
            'Log in as your admin user and open /dashboard/, /dashboard/bookings/ and /dashboard/services/.',
            'Log in as the seeded customer anu (password demo12345) and open /dashboard/. Confirm you get 403.',
            'Search the booking list for "anu", filter by Completed, and move to page 2. Check the filter stays.',
            'Open a pending booking, confirm it, then try to complete a cancelled one and read the error message.',
            'Add a "Revenue last 7 days" KPI card to the home page.',
            'Add a CSV export button to the booking list that downloads the current filtered results.',
        ],
        'check': [
            'A customer login gets 403 on every /dashboard/ page.',
            'Creating a service with a 20-minute duration shows "Duration must be in 15-minute steps."',
            'Your CSV export respects the search and status filter.',
        ],
    },
    'quiz': [
        q('Why does StaffRequiredMixin check role as well as login?',
          ['Login is slow', 'A logged-in customer must not see business data', 'Django requires two mixins', 'To support pagination'], 1,
          'Authentication says who you are; authorisation says what you may do. The dashboard needs both.'),
        q('Why is changing a booking’s status a POST and not a GET link?',
          ['GET cannot carry data', 'GET requests can be triggered by prefetching or other sites; POST with CSRF protection cannot', 'POST is faster', 'Templates cannot make links'], 1,
          'State-changing actions must use POST so the CSRF token protects them.'),
        q('Sum("price") over a month with no completed bookings returns…',
          ['0', 'None', 'An error', 'An empty list'], 1,
          'SQL SUM over no rows is NULL, which Django returns as None. Hence the or 0.'),
        q('You need to email the customer when a booking is confirmed. Where do you send it?',
          ['In a post_save signal, immediately', 'From the service layer, inside transaction.on_commit()', 'In the template', 'In the middleware'], 1,
          'on_commit runs only after the transaction succeeds, so nobody is told about a booking that was rolled back. The service layer keeps the logic visible.'),
        q('Why avoid fields = "__all__" in a ModelForm?',
          ['It is slower', 'New model fields would become editable automatically, possibly sensitive ones', 'It does not work with ModelForm', 'It breaks clean methods'], 1,
          'Listing fields explicitly means a new column is never exposed by accident.'),
    ],
}

L12 = {
    'id': 'dj12', 'num': '5.1', 'title': 'A REST API with DRF and JWT', 'minutes': 90,
    'summaryHtml': '<p>The API the mobile app uses: register and JWT login, serializers that read nested and write by id, viewsets with a custom action, per-user querysets that prevent IDOR, one error shape, throttling and Swagger docs.</p>',
    'contentHtml': '\n'.join([
        '<h3>Endpoints</h3>',
        '<table><thead><tr><th>Method and path</th><th>What it does</th></tr></thead><tbody>',
        '<tr><td><code>POST /api/v1/auth/register/</code></td><td>Create a customer account</td></tr>',
        '<tr><td><code>POST /api/v1/auth/token/</code></td><td>Log in: returns <code>access</code> and <code>refresh</code> tokens</td></tr>',
        '<tr><td><code>POST /api/v1/auth/token/refresh/</code></td><td>New access token from a refresh token</td></tr>',
        '<tr><td><code>GET /api/v1/services/</code></td><td>Public list, with search and ordering</td></tr>',
        '<tr><td><code>GET /api/v1/services/&lt;slug&gt;/slots/?date=</code></td><td>Free slots for a day</td></tr>',
        '<tr><td><code>GET/POST /api/v1/bookings/</code></td><td>My bookings / book a slot</td></tr>',
        '<tr><td><code>POST /api/v1/bookings/&lt;id&gt;/cancel/</code></td><td>Cancel my booking</td></tr>',
        '<tr><td><code>GET /api/v1/docs/</code></td><td>Swagger UI generated by drf-spectacular</td></tr>',
        '</tbody></table>',
        '<h3>REST rules we follow</h3>',
        '<ul>',
        '<li>Version from day one (<code>/api/v1/</code>). Mobile apps in the Play Store cannot be force-updated.</li>',
        '<li>Plural nouns for resources; verbs only for actions (<code>/cancel/</code>).</li>',
        '<li>Status codes: 400 validation, 401 not logged in, 403 not allowed, 404 not found or not yours, 429 throttled.</li>',
        '<li>The default permission is <code>IsAuthenticated</code>, so every endpoint is private unless you open it on purpose.</li>',
        '<li>CORS allows only your own frontends (e.g. the Next.js app), never <code>*</code> in production.</li>',
        '</ul>',
        '<h3>JWT in one paragraph</h3>',
        '<p>The app sends username and password once and receives a short-lived <strong>access</strong> token (30 minutes) and a longer <strong>refresh</strong> token (7 days). Every request carries <code>Authorization: Bearer &lt;access&gt;</code>. When it expires, the app swaps the refresh token for a new pair; with rotation and blacklisting, an old refresh token cannot be reused.</p>',
        '<h3>Serializers: nested on read, id on write</h3>',
        code('''
class BookingSerializer(serializers.ModelSerializer):
    service = ServiceSerializer(read_only=True)  # nested on read
    service_id = serializers.PrimaryKeyRelatedField(  # plain id on write
        queryset=Service.objects.filter(is_active=True), source="service", write_only=True
    )
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = Booking
        fields = ["id", "service", "service_id", "start_at", "end_at",
                  "status", "status_display", "price", "notes", "created_at"]
        read_only_fields = ["end_at", "status", "price", "created_at"]

    def create(self, validated_data):
        try:
            return create_booking(customer=self.context["request"].user, **validated_data)
        except BookingError as exc:
            raise serializers.ValidationError({"start_at": [str(exc)]}) from exc
'''),
        '<p><code>price</code> and <code>status</code> are read-only: a client must never send its own price. The customer comes from the token, not the request body. The serializer calls the same <code>create_booking</code> as the dashboard.</p>',
        '<h3>Only your own rows: preventing IDOR</h3>',
        code('''
def get_queryset(self):
    qs = Booking.objects.select_related("service")
    user = self.request.user
    # Customers only ever see their own rows -> no IDOR (guessing /bookings/42/)
    return qs if user.is_staff_member else qs.filter(customer=user)
'''),
        '<p>Because retrieve, list and the cancel action all start from this queryset, another customer’s booking returns <strong>404</strong>, not 403. The API does not even confirm it exists.</p>',
        '<h3>A custom action</h3>',
        code('''
@action(detail=True, methods=["post"])
def cancel(self, request, pk=None):
    booking = self.get_object()
    try:
        booking = change_status(booking=booking, new_status=Booking.Status.CANCELLED, by=request.user)
    except BookingError as exc:
        return Response({"success": False, "errors": {"detail": str(exc)}}, status=status.HTTP_400_BAD_REQUEST)
    return Response(self.get_serializer(booking).data)
'''),
        '<h3>One error shape for every endpoint</h3>',
        code('''
def api_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is not None:
        response.data = {"success": False, "status_code": response.status_code, "errors": response.data}
    return response
'''),
        '<p>The Flutter app can always read <code>response["errors"]</code>, whatever went wrong. Settings also add default pagination (20 per page), filtering, and throttling (30/min anonymous, 120/min per user).</p>',
        '<div class="callout">The booking viewset deliberately has no update or delete mixins. Customers cancel through the <code>cancel</code> action so the state machine always runs.</div>',
        '<h3>The brief: mobile API for the Flutter app</h3>',
        '<p>Our Flutter developer starts the customer app on Monday. They need a stable, documented API and a Postman or Bruno collection today. Deliver: every endpoint above working with JWT; Swagger listing all of them; a <code>GET/PATCH /api/v1/me/</code> profile endpoint; an exported collection in <code>docs/</code> with variables for the base URL and token.</p>',
        '<p><strong>Stretch goals:</strong> <code>GET /bookings/{id}/invoice/</code> using Day 2’s <code>invoice.py</code> for the GST totals; a staff-only <code>/api/v1/staff/bookings/</code>; cursor pagination for an infinite-scroll list.</p>',
    ]),
    'terms': [
        {'term': 'Serializer', 'definition': 'Converts model instances to JSON and validates incoming JSON.'},
        {'term': 'ViewSet', 'definition': 'One class providing list, retrieve, create and other actions, wired to URLs by a router.'},
        {'term': 'JWT', 'definition': 'A signed token carrying the user id. Access tokens are short-lived; refresh tokens get new ones.'},
        {'term': 'IDOR', 'definition': 'Insecure Direct Object Reference: reading someone else’s data by changing an id in the URL.'},
        {'term': '@action', 'definition': 'Adds a custom endpoint such as /bookings/<id>/cancel/ to a ViewSet.'},
        {'term': 'Throttling', 'definition': 'Limiting how many requests a client can make per minute.'},
        {'term': 'OpenAPI / Swagger', 'definition': 'A machine-readable description of the API and an interactive page to try it.'},
    ],
    'examTip': 'For any API that returns user data, the first security question is “can user A read user B’s rows by changing the id?”. Filtering get_queryset by request.user is the standard answer.',
    'lab': {
        'files': f('bookit/apps/api/serializers.py', 'bookit/apps/api/views.py', 'bookit/apps/api/urls.py',
                   'bookit/apps/api/permissions.py', 'bookit/apps/api/exceptions.py'),
        'steps': [
            'Open /api/v1/docs/ and read the endpoints Swagger lists.',
            'Register a user, then POST to /api/v1/auth/token/ and copy the access token. Click Authorize in Swagger and paste it.',
            'Book a slot from /api/v1/services/<slug>/slots/, then list your bookings.',
            'Log in as a second customer and request the first customer’s booking id. Confirm the 404.',
            'Add GET /api/v1/bookings/upcoming/ (a list action) that returns only my future pending or confirmed bookings.',
            'Add a staff-only endpoint, using IsStaffMember, that returns today’s bookings for all customers.',
        ],
        'check': [
            'Sending a price in the booking POST body is ignored: the saved price is the service price.',
            'Another customer’s booking returns 404 with {"success": false, ...}.',
            'Your staff-only endpoint returns 403 for a customer token.',
        ],
    },
    'quiz': [
        q('A customer requests /api/v1/bookings/42/ which belongs to someone else. What does BookIt return?',
          ['200 with the booking', '403 Forbidden', '404 Not Found', '500'], 2,
          'get_queryset only contains the customer’s own bookings, so 42 is simply not found. This also hides whether it exists.'),
        q('Why are price and status read_only in BookingSerializer?',
          ['They are computed by the database', 'Clients must not set their own price or skip the status rules', 'DRF cannot write Decimals', 'To make responses smaller'], 1,
          'The server decides the price (snapshot of the service) and status changes go through the state machine.'),
        q('What is the refresh token for?',
          ['Logging every request', 'Getting a new access token without asking for the password again', 'Refreshing the page', 'Resetting the password'], 1,
          'Access tokens are short-lived for safety. The refresh token renews them; with rotation each refresh gives a new refresh token.'),
        q('Why not set CORS to allow * in production?',
          ['It is slower', 'Any website’s scripts could then call your API from your users’ browsers', 'Flutter apps need CORS', 'JWT does not work with *'], 1,
          'CORS is the browser rule for which sites may call your API from JavaScript. List only your own frontends.'),
        q('Why does the API start at /api/v1/?',
          ['Django requires it', 'Installed mobile apps cannot be force-updated, so old versions must keep working when the API changes', 'For SEO', 'JWT needs a version'], 1,
          'With a version in the path you can ship /api/v2/ without breaking phones still running the old app.'),
        q('Why does the serializer’s create() call create_booking() instead of Booking.objects.create()?',
          ['It is shorter', 'So the API gets the same locking, overlap and price rules as the dashboard', 'DRF requires it', 'create() is deprecated'], 1,
          'The service layer is the single home of the booking rules.'),
    ],
}

L0 = {
    'id': 'dj0', 'num': '0.1', 'title': 'Welcome, setup and how the week works', 'minutes': 45,
    'summaryHtml': '<p>Six days from “I know some Python” to a deployed Django product with a custom dashboard and a REST API a Flutter app can use. Get your machine ready, learn the ground rules, and see the week at a glance.</p>',
    'contentHtml': '\n'.join([
        '<h3>Welcome to the team</h3>',
        '<p>You are joining as a Junior Python Developer. Our clients in India, the GCC, the UK and Canada run on systems we build: ERPs, booking apps, LMS platforms, POS systems and SaaS dashboards. This week builds the habits those projects need, not memorised syntax:</p>',
        '<ul>',
        '<li><strong>Correctness first.</strong> Money in <code>Decimal</code>, time zones handled, no double bookings.</li>',
        '<li><strong>Thin views, fat services.</strong> Business rules live in one place and get tested.</li>',
        '<li><strong>No Django default admin in production.</strong> We build custom, modern dashboards for clients.</li>',
        '<li><strong>Ship it.</strong> Code isn’t done until it is on Git, tested and deployed.</li>',
        '</ul>',
        '<h3>What you will build: BookIt</h3>',
        '<p>From Day 3 every lesson adds a piece to one product: <strong>BookIt</strong>, a booking platform for a service business (car wash, clinic, salon, gym). We have built this pattern for real clients many times.</p>',
        '<p><strong>Customer (Flutter app) → REST API with JWT → Service layer (rules) → PostgreSQL ← Staff dashboard (Django + Tailwind)</strong></p>',
        '<h3>The six days</h3>',
        '<table><thead><tr><th>Day</th><th>Morning: concepts</th><th>Afternoon: real-world task</th><th>Deliverable</th></tr></thead><tbody>',
        '<tr><td>1 · Python core</td><td>venv and Git, mutability, comprehensions, closures, decorators, exceptions, files</td><td>Daily Sales Report CLI for a retail POS export</td><td><code>sales_report.py</code> + <code>errors.csv</code></td></tr>',
        '<tr><td>2 · Professional Python</td><td>OOP, dataclasses, typing, Enum, Decimal, generators, context managers, logging, requests, pytest</td><td>GST Invoice Engine with a full test suite</td><td><code>invoice.py</code> + passing tests</td></tr>',
        '<tr><td>3 · Django foundations</td><td>Request lifecycle, layout, split settings, PostgreSQL, custom User, models, constraints, migrations, ORM</td><td>BookIt data layer: models, seed command, 8 report queries</td><td>Migrations + seed + reports</td></tr>',
        '<tr><td>4 · Web layer and dashboard</td><td>URLs, CBVs, templates, forms, auth and roles, service layer, middleware</td><td>Staff dashboard with KPIs, search, status workflow, service CRUD</td><td>Working dashboard</td></tr>',
        '<tr><td>5 · REST APIs</td><td>DRF serializers, viewsets, JWT, permissions, throttling, CORS, OpenAPI, API tests</td><td>Mobile API for the Flutter app</td><td>Swagger docs + green tests</td></tr>',
        '<tr><td>6 · Production and demo</td><td>Prod settings, security checklist, WhiteNoise, Gunicorn, Railway, performance, Git workflow</td><td>Deploy BookIt, then demo it to the team at 3:00 PM</td><td>Live URL + demo</td></tr>',
        '</tbody></table>',
        '<h3>A typical day</h3>',
        '<table><tbody>',
        '<tr><td>9:30 – 9:45</td><td>Stand-up: what I finished, what I’m doing today, what’s blocking me</td></tr>',
        '<tr><td>9:45 – 11:15</td><td>Concept block 1: the mentor walks through lessons, you type along (no copy-paste)</td></tr>',
        '<tr><td>11:30 – 1:00</td><td>Concept block 2 + quiz questions in pairs</td></tr>',
        '<tr><td>2:00 – 4:30</td><td>Real-world task: work independently, commit small and often</td></tr>',
        '<tr><td>4:30 – 5:15</td><td>Demo and review: 5 minutes each, one mentor comment, one peer comment</td></tr>',
        '<tr><td>5:15 – 5:30</td><td>Push + daily log: three bullets in <code>LOG.md</code> (learned, built, still unclear)</td></tr>',
        '</tbody></table>',
        '<h3>Ground rules</h3>',
        '<ul>',
        '<li><strong>The 20-minute rule.</strong> Stuck for 20 minutes? Ask. Bring what you tried, the exact error, and what you expected to happen.</li>',
        '<li><strong>Commit every day.</strong> Push before 5:30 PM with clear messages (<code>feat: add booking model</code>). Mentors review your PR the next morning.</li>',
        '<li><strong>AI tools (Claude Code, Copilot).</strong> We use them every day, so you will too. On Days 1–2, write it yourself first, then compare with AI. From Day 3 use AI freely, but you must be able to explain every line in review.</li>',
        '</ul>',
        '<div class="callout">Also post your daily update in the staff portal (Daily updates). It is how your mentor follows your week.</div>',
    ]),
    'terms': [
        {'term': 'BookIt', 'definition': 'The service-booking product you build from Day 3: a staff dashboard plus a REST API for a Flutter app.'},
        {'term': 'Service layer', 'definition': 'Plain functions in services.py that hold the business rules, called by both the dashboard and the API.'},
        {'term': 'LOG.md', 'definition': 'Your daily log in the repo: what you learned, what you built, what is still unclear.'},
        {'term': 'PR (pull request)', 'definition': 'A request to merge your branch; mentors review it the next morning.'},
        {'term': 'Railway', 'definition': 'The hosting platform Ralfiz deploys Django apps and PostgreSQL to.'},
    ],
    'examTip': 'When you ask for help, lead with the exact error and what you already tried. You will get a useful answer in half the time.',
    'lab': {
        'files': [],
        'steps': [
            'Install Python 3.12 or newer and check it with python3 --version.',
            'Install VS Code with the Python, Pylance and Ruff extensions (or PyCharm).',
            'Install Git and set git config --global user.name and user.email.',
            'Make sure your GitHub account is in the Ralfiz organisation, then create the repo bookit-<yourname>.',
            'Get PostgreSQL 16 running locally (native install, or docker run -e POSTGRES_PASSWORD=bookit -p 5432:5432 postgres:16).',
            'Install Postman or Bruno for API testing.',
            'Create a Railway account (you need it on Day 6).',
            'Create LOG.md in your repo with today’s date, commit it and push.',
        ],
        'check': [
            'python3 --version prints 3.12 or newer.',
            'git log in bookit-<yourname> shows your first commit with your name.',
            'psql or a database client connects to your local PostgreSQL.',
        ],
    },
    'quiz': [
        q('You have been stuck on an error for 20 minutes. What should you do?',
          ['Keep trying until it works', 'Ask, bringing what you tried, the exact error and what you expected', 'Skip the task', 'Ask AI to rewrite the whole file'], 1,
          'The 20-minute rule: ask, and bring the evidence so the answer is quick.'),
        q('On Days 1–2, how should you use AI tools?',
          ['Not at all', 'Write it yourself first, then compare with AI', 'Let AI write everything', 'Only for tests'], 1,
          'Writing it first builds the habit; comparing shows you better ways. From Day 3 use AI freely, but explain every line.'),
        q('When must your code be pushed each day?',
          ['Only on Saturday', 'Before 5:30 PM, with clear commit messages', 'Once a week', 'Only when it is perfect'], 1,
          'Daily pushes let mentors review your PR the next morning.'),
    ],
}

L13 = {
    'id': 'dj13', 'num': '5.2', 'title': 'API tests and seed data', 'minutes': 60,
    'summaryHtml': '<p>pytest-django tests that prove the business rules through the real API, and a <code>seed_demo</code> management command that fills the database with realistic demo data in one fast query.</p>',
    'contentHtml': '\n'.join([
        '<h3>Testing through the API</h3>',
        '<p>These tests use the real URLs, real serializers and a real test database. They prove what the mobile app will see.</p>',
        code('''
def test_booking_snapshots_price_and_blocks_double_booking(api, customer, other_customer, service):
    payload = {"service_id": service.id, "start_at": tomorrow_at(10).isoformat()}

    api.force_authenticate(customer)
    r = api.post("/api/v1/bookings/", payload, format="json")
    assert r.status_code == 201, r.data
    assert r.data["price"] == "499.00"
    assert r.data["status"] == "pending"

    api.force_authenticate(other_customer)
    r = api.post("/api/v1/bookings/", payload, format="json")
    assert r.status_code == 400
    assert r.data["success"] is False
'''),
        '<ul>',
        '<li>The <code>db</code> fixture (pulled in by <code>customer</code> and <code>service</code>) gives each test a clean database.</li>',
        '<li><code>force_authenticate</code> skips the token dance when the test is not about login.</li>',
        '<li><code>assert r.status_code == 201, r.data</code> prints the error body when it fails.</li>',
        '<li>Test what the business cares about: the price snapshot, double booking blocked, privacy (404), state rules.</li>',
        '</ul>',
        code('pip install -r requirements/dev.txt\npytest -q      # pytest.ini sets DJANGO_SETTINGS_MODULE=config.settings.dev\n# expected: 5 passed'),
        '<h3>Try it like the Flutter developer will</h3>',
        code('''
curl -X POST http://127.0.0.1:8000/api/v1/auth/token/ \\
     -H "Content-Type: application/json" -d '{"username": "anu", "password": "demo12345"}'
# copy "access" from the answer, then:
curl http://127.0.0.1:8000/api/v1/bookings/ -H "Authorization: Bearer <access>"
'''),
        '<h3>Seed data with a management command</h3>',
        '<p>Every project needs realistic demo data for client demos and for testing the dashboard. Write a command; don’t click data in by hand.</p>',
        code('''
class Command(BaseCommand):
    help = "Create demo services, staff, customers and bookings"

    def add_arguments(self, parser):
        parser.add_argument("--bookings", type=int, default=200)

    @transaction.atomic
    def handle(self, *args, **options):
        services = [Service.objects.get_or_create(slug=slugify(name), defaults={...})[0] for ...]
        ...
        # bulk_create = one INSERT instead of hundreds (seed data only; skips overlap rules)
        Booking.objects.bulk_create(bookings, batch_size=500)
'''),
        '<p><code>get_or_create</code> makes the command safe to run twice. <code>bulk_create</code> is fast because it skips <code>save()</code> and your service-layer rules, so use it only for demo or migration data.</p>',
    ]),
    'terms': [
        {'term': 'pytest-django', 'definition': 'pytest plugin that sets up Django and provides fixtures such as db and client.'},
        {'term': 'APIClient', 'definition': 'DRF’s test client for calling API endpoints with JSON and authentication.'},
        {'term': 'force_authenticate', 'definition': 'Makes APIClient act as a given user without a real token.'},
        {'term': 'Management command', 'definition': 'A custom python manage.py <name> command in an app’s management/commands folder.'},
        {'term': 'bulk_create', 'definition': 'Inserts many rows in few queries, skipping save() and signals.'},
        {'term': 'Idempotent', 'definition': 'Safe to run more than once with the same result.'},
    ],
    'examTip': 'A good API test reads like a user story: who calls, what they send, what they must get back. Name it after the rule it proves.',
    'lab': {
        'files': f('bookit/apps/api/tests.py', 'bookit/pytest.ini', 'bookit/apps/bookings/management/commands/seed_demo.py'),
        'steps': [
            'Run pytest -q in the bookit folder. All 5 tests should pass (use PostgreSQL for the locking test to be meaningful).',
            'Write a test that a customer cannot cancel a completed booking through the API (expects 400).',
            'Write a test that a client cannot set price or status when creating a booking.',
            'Write a test for your /bookings/upcoming/ endpoint from lesson 5.1.',
            'Run python manage.py seed_demo --bookings 1000 and time it. Then try the same with a loop of Booking.objects.create and compare.',
            'Export a Postman or Bruno collection of every endpoint into docs/ and commit it.',
        ],
        'check': [
            'pytest -q reports all tests passed, including your new ones.',
            'Running seed_demo twice does not duplicate services or customers.',
            'seed_demo with bulk_create is many times faster than the create() loop.',
        ],
    },
    'quiz': [
        q('Why does seed_demo use get_or_create for services?',
          ['It is faster than create', 'So running the command twice does not create duplicates', 'bulk_create requires it', 'To skip validation'], 1,
          'Idempotent seed commands can be run again safely.'),
        q('What does bulk_create skip?',
          ['The database', 'Each model’s save() method and signals', 'Foreign keys', 'Transactions'], 1,
          'bulk_create inserts directly, so custom save logic and signals do not run. Fine for seed data, not for real bookings.'),
        q('In an API test, why use force_authenticate(customer)?',
          ['It tests the login endpoint', 'It skips getting a token when the test is about something else', 'It creates the user', 'It is required for every request'], 1,
          'Keep each test about one thing. Login has its own test.'),
        q('Which of these is most worth testing?',
          ['That a getter returns its field', 'That another customer’s booking returns 404', 'That Django imports', 'That the settings file exists'], 1,
          'Test the business and security rules, not trivial getters.'),
    ],
}

L14 = {
    'id': 'dj14', 'num': '6.1', 'title': 'Production, security and deploying on Railway', 'minutes': 90,
    'summaryHtml': '<p>Code on a laptop has no value to a client. Harden BookIt with production settings and the security checklist, deploy it on Railway with PostgreSQL, and learn the Ralfiz Git workflow.</p>',
    'contentHtml': '\n'.join([
        '<h3>Production settings</h3>',
        code('''
DEBUG = False
CSRF_TRUSTED_ORIGINS = env.list("CSRF_TRUSTED_ORIGINS", default=[])

# Railway terminates TLS at its proxy and forwards X-Forwarded-Proto
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = env.bool("SECURE_SSL_REDIRECT", default=True)
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = env.int("SECURE_HSTS_SECONDS", default=3600)  # raise to 31536000 once stable
X_FRAME_OPTIONS = "DENY"
'''),
        '<p>Railway handles HTTPS at its proxy and talks plain HTTP to your app. <code>SECURE_PROXY_SSL_HEADER</code> tells Django to trust the proxy’s header; without it <code>SECURE_SSL_REDIRECT</code> redirects forever. Start HSTS small and raise it once HTTPS works everywhere, because browsers remember it.</p>',
        '<h3>Security checklist (every project, every time)</h3>',
        '<ul>',
        '<li><code>DEBUG=False</code>, with a long random <code>SECRET_KEY</code> from env vars (never in Git).</li>',
        '<li><code>ALLOWED_HOSTS</code> and <code>CSRF_TRUSTED_ORIGINS</code> set to the real domains.</li>',
        '<li>HTTPS redirect, secure cookies, HSTS.</li>',
        '<li>Every queryset scoped to the user (IDOR); every endpoint has explicit permissions.</li>',
        '<li>Login and register throttled.</li>',
        '<li>Uploads validated for extension and size, and never served from the code directory.</li>',
        '<li>No <code>|safe</code> on user content; no raw SQL built with string formatting.</li>',
        '<li>CORS restricted to known frontends.</li>',
        '<li>Dependencies pinned; <code>pip-audit</code> run before release.</li>',
        '</ul>',
        '<h3>Deploy on Railway</h3>',
        '<ol>',
        '<li>Add <code>requirements.txt</code> at the root containing <code>-r requirements/prod.txt</code>, and pin Python with a <code>.python-version</code> file (e.g. <code>3.12</code>).</li>',
        '<li>Push to GitHub. In Railway: New Project → Deploy from GitHub repo.</li>',
        '<li>Add a PostgreSQL database to the project.</li>',
        '<li>In the web service’s Variables add <code>DJANGO_SETTINGS_MODULE=config.settings.prod</code>, <code>SECRET_KEY</code>, <code>DATABASE_URL</code> (a reference to the Postgres service), <code>ALLOWED_HOSTS</code> and <code>CSRF_TRUSTED_ORIGINS</code>.</li>',
        '<li>In Settings → Deploy set the pre-deploy command <code>python manage.py migrate</code> and the start command <code>python manage.py collectstatic --noinput &amp;&amp; gunicorn config.wsgi</code>.</li>',
        '<li>Generate a public domain under Settings → Networking, then create the first admin with <code>railway run python manage.py createsuperuser</code> and set their role to admin.</li>',
        '</ol>',
        '<div class="warn"><strong>Common deploy errors.</strong> 400 Bad Request → <code>ALLOWED_HOSTS</code>. CSRF failed on login → <code>CSRF_TRUSTED_ORIGINS</code> needs <code>https://</code>. Static files 404 → WhiteNoise middleware order or collectstatic. Redirect loop → <code>SECURE_PROXY_SSL_HEADER</code>. Always read the deploy logs first.</div>',
        '<p>For client projects the domain is bought on Namecheap and pointed to Railway with a CNAME record from the service’s custom-domain settings. Add the new domain to <code>ALLOWED_HOSTS</code> and <code>CSRF_TRUSTED_ORIGINS</code>. Railway’s disk is wiped on every deploy, so uploaded media needs a volume or object storage.</p>',
        '<h3>Performance and observability basics</h3>',
        '<ul>',
        '<li>Measure before optimising: django-debug-toolbar in dev, the slow-request middleware in prod.</li>',
        '<li>Queries: <code>select_related</code>/<code>prefetch_related</code>, indexes on filtered columns, <code>.only()</code> for heavy tables, and always paginate.</li>',
        '<li>Caching: cache expensive, rarely-changing data (the service list, dashboard KPIs for 60 seconds) with Redis via Django’s cache framework.</li>',
        '<li>Background work: emails, SMS, WhatsApp messages and PDF invoices should not run inside the request. Use a task queue (Celery or RQ with Redis) once a project needs it.</li>',
        '<li>Errors: connect an error tracker (e.g. Sentry) so you hear about crashes before the client does.</li>',
        '</ul>',
        '<h3>The Ralfiz Git workflow</h3>',
        '<table><thead><tr><th>Branches</th><th>Commit messages</th></tr></thead><tbody>',
        '<tr><td><code>main</code>: production, deploys automatically</td><td><code>feat: add cancel action to bookings API</code></td></tr>',
        '<tr><td><code>develop</code>: staging</td><td><code>fix: use local date for slot lookup</code></td></tr>',
        '<tr><td><code>feat/BK-12-booking-cancel</code>, <code>fix/BK-19-slot-timezone</code></td><td><code>refactor:</code>, <code>test:</code>, <code>docs:</code>, <code>chore:</code></td></tr>',
        '</tbody></table>',
        '<p><strong>Pull request checklist:</strong> small PR (under about 400 lines, one purpose); tests added and green; migrations included and reviewed; no secrets, prints or commented-out code; screenshots for UI changes.</p>',
    ]),
    'terms': [
        {'term': 'HSTS', 'definition': 'A header telling browsers to use HTTPS only for this site for a set time.'},
        {'term': 'SECURE_PROXY_SSL_HEADER', 'definition': 'Tells Django to trust the proxy’s X-Forwarded-Proto header to know a request was HTTPS.'},
        {'term': 'gunicorn', 'definition': 'The production WSGI server that runs Django with several worker processes.'},
        {'term': 'WhiteNoise', 'definition': 'Serves static files straight from Django with caching headers, no separate web server needed.'},
        {'term': 'Pre-deploy command', 'definition': 'A command Railway runs before switching traffic to the new version, used for migrations.'},
        {'term': 'pip-audit', 'definition': 'Checks your installed packages against known security vulnerabilities.'},
        {'term': 'Conventional Commits', 'definition': 'Commit messages starting with a type such as feat:, fix: or docs:.'},
    ],
    'examTip': 'Run python manage.py check --deploy before every first release. It lists the security settings you forgot.',
    'lab': {
        'files': f('bookit/config/settings/prod.py', 'bookit/config/settings/base.py', 'bookit/requirements/prod.txt',
                   'bookit/.env.example'),
        'steps': [
            'Run DJANGO_SETTINGS_MODULE=config.settings.prod python manage.py check --deploy with test values in .env and fix or explain each warning.',
            'Go through the security checklist line by line against your BookIt code and note anything missing in LOG.md.',
            'Add requirements.txt (-r requirements/prod.txt) and .python-version at the repo root.',
            'Create the Railway project with PostgreSQL, set the variables, the pre-deploy and the start commands.',
            'Deploy, then open the public URL. Fix whatever breaks by reading the deploy logs first.',
            'Run seed_demo on Railway and create your admin user.',
            'Write the README: setup, environment variables, how to run tests, how to deploy.',
        ],
        'check': [
            'The live URL works over HTTPS and http:// redirects to https://.',
            'check --deploy shows no critical warnings.',
            'Staff login works on the live site and the dashboard shows seeded data.',
            '/api/v1/docs/ loads on the live site.',
        ],
    },
    'quiz': [
        q('Why is SECURE_PROXY_SSL_HEADER needed on Railway?',
          ['To enable gzip', 'The proxy handles HTTPS and forwards plain HTTP, so Django must trust X-Forwarded-Proto', 'To allow CORS', 'To speed up the database'], 1,
          'Without it Django thinks every request is HTTP and SECURE_SSL_REDIRECT loops.'),
        q('After deploying, logging in fails with “CSRF verification failed”. What is the likely fix?',
          ['Turn off CSRF', 'Add https://your-domain to CSRF_TRUSTED_ORIGINS', 'Set DEBUG=True', 'Clear the database'], 1,
          'Django 4+ checks the Origin header against CSRF_TRUSTED_ORIGINS, which must include the scheme.'),
        q('Why start SECURE_HSTS_SECONDS small?',
          ['It saves bandwidth', 'Browsers remember HSTS; a mistake with a long value locks users out of any HTTP-only part of the site for that long', 'Django requires it', 'It makes cookies secure'], 1,
          'Raise it to a year only once HTTPS is confirmed working everywhere.'),
        q('Where should sending a WhatsApp confirmation run in a busy app?',
          ['Inside the request, before responding', 'In a background task queue', 'In the template', 'In a migration'], 1,
          'Slow outside calls in the request make every user wait and can time out. A task queue sends them separately.'),
    ],
}

L15 = {
    'id': 'dj15', 'num': '6.2', 'title': 'Demo day: the BookIt brief and how you are scored', 'minutes': 60,
    'summaryHtml': '<p>The client brief and user stories you built against all week, the demo format, the evaluation rubric, and what comes next.</p>',
    'contentHtml': '\n'.join([
        '<h3>The client brief</h3>',
        '<div class="example">“We run a car wash in Perinthalmanna and plan to open two more branches. Customers call to book and we lose track. We want an app where customers book a service and time slot, and a dashboard where our manager sees the day’s bookings and revenue. No double bookings. Prices change sometimes, but old bills must stay the same.”</div>',
        '<h3>User stories</h3>',
        '<table><thead><tr><th>As a…</th><th>I want to…</th><th>Built on</th></tr></thead><tbody>',
        '<tr><td>Customer</td><td>register and log in from the app</td><td>Day 5</td></tr>',
        '<tr><td>Customer</td><td>see services with price and duration, and free slots for a date</td><td>Day 5</td></tr>',
        '<tr><td>Customer</td><td>book a slot and get a clear error if it was just taken</td><td>Days 4–5</td></tr>',
        '<tr><td>Customer</td><td>see and cancel my upcoming bookings, and nobody else’s</td><td>Day 5</td></tr>',
        '<tr><td>Manager</td><td>see today’s bookings, pending count and monthly revenue at a glance</td><td>Day 4</td></tr>',
        '<tr><td>Manager</td><td>find a booking by customer name or phone in seconds</td><td>Day 4</td></tr>',
        '<tr><td>Manager</td><td>confirm, complete or cancel bookings, never out of order</td><td>Days 3–4</td></tr>',
        '<tr><td>Manager</td><td>add and edit services and prices without changing old bookings</td><td>Days 3–4</td></tr>',
        '<tr><td>Owner</td><td>open it from anywhere on a secure link</td><td>Day 6</td></tr>',
        '</tbody></table>',
        '<h3>Non-functional requirements</h3>',
        '<ul>',
        '<li>PostgreSQL; money as Decimal; times stored in UTC and shown in IST.</li>',
        '<li>No Django admin; a role-based custom dashboard.</li>',
        '<li>API versioned, JWT-secured, documented with OpenAPI, with consistent errors.</li>',
        '<li>Concurrency-safe booking (row lock + overlap check).</li>',
        '<li>Automated tests for every business rule; deployed on Railway over HTTPS.</li>',
        '</ul>',
        '<h3>Demo format (15 minutes each)</h3>',
        '<p>Treat it as a handover to the car wash owner, then a technical review with the team.</p>',
        '<ol>',
        '<li><strong>Live demo (5 min):</strong> on the deployed URL, staff login → KPIs → find a customer by phone → confirm and complete a booking.</li>',
        '<li><strong>API demo (3 min):</strong> register → login → book a slot → try to double-book → cancel, in Swagger or Postman against production.</li>',
        '<li><strong>Code walkthrough (4 min):</strong> explain <code>create_booking</code> line by line, including why the row lock exists.</li>',
        '<li><strong>Q&amp;A (3 min):</strong> mentors pick any file and ask “why is it written this way?”</li>',
        '</ol>',
        '<h3>Evaluation rubric</h3>',
        '<p>Mentors score at the demo. You fill in a self-assessment first, and the gap between the two scores is part of the conversation.</p>',
        '<table><thead><tr><th>Area</th><th>Weight</th><th>Excellent</th><th>Needs work</th></tr></thead><tbody>',
        '<tr><td>Python fundamentals (Days 1–2)</td><td>20</td><td>Clean functions, correct Decimal maths, meaningful exceptions, tests green</td><td>Floats for money, bare except, one giant function</td></tr>',
        '<tr><td>Data modelling and ORM</td><td>15</td><td>Constraints, PROTECT, snapshots, indexes; no N+1</td><td>Free-text statuses, CASCADE everywhere, N+1 in lists</td></tr>',
        '<tr><td>Dashboard (views, forms, templates)</td><td>15</td><td>Thin views, role-protected, validated forms, filters keep state</td><td>Logic in templates or views, GET for state changes</td></tr>',
        '<tr><td>API and security</td><td>20</td><td>JWT, scoped querysets, read-only server fields, consistent errors, docs</td><td>IDOR possible, client can set price, no docs</td></tr>',
        '<tr><td>Testing</td><td>10</td><td>Business rules covered; tests readable and green</td><td>No tests, or tests of trivial getters only</td></tr>',
        '<tr><td>Deployment</td><td>10</td><td>Live on Railway over HTTPS, prod settings, README</td><td>Not deployed, DEBUG on, secrets in Git</td></tr>',
        '<tr><td>Git and communication</td><td>10</td><td>Daily commits, clear messages, good LOG.md, asks good questions</td><td>One huge commit on Saturday, silent when stuck</td></tr>',
        '</tbody></table>',
        '<table><thead><tr><th>Score</th><th>What happens next</th></tr></thead><tbody>',
        '<tr><td>85–100 · Ready</td><td>Join a live client project next week with a senior buddy.</td></tr>',
        '<tr><td>65–84 · Almost</td><td>One more week on BookIt extensions, then a live project.</td></tr>',
        '<tr><td>Below 65 · Rebuild</td><td>A targeted plan on the weak areas, with a re-demo in one week.</td></tr>',
        '</tbody></table>',
        '<h3>Next week</h3>',
        '<p>Strong finishers extend BookIt with multi-branch support (a Branch model, with staff and bookings scoped per branch), GST invoices from Day 2’s engine rendered as PDFs, and WhatsApp booking confirmations in a background task. That is the same architecture as our multi-branch clinic, gym and laundry products.</p>',
        '<h3>Keep learning</h3>',
        '<p>Official documentation first, then blogs and videos. When the docs and a blog disagree, the docs win.</p>',
        '<ul>',
        '<li><strong>Python:</strong> the official tutorial; the dataclasses, decimal and logging HOWTO pages; pytest; requests.</li>',
        '<li><strong>Django:</strong> Django 5.2 docs; Database access optimisation; Deployment checklist; Customising authentication.</li>',
        '<li><strong>APIs:</strong> Django REST Framework; Simple JWT; drf-spectacular; OWASP API Security Top 10.</li>',
        '<li><strong>Deployment and tools:</strong> Railway docs; WhiteNoise; Tailwind CSS; Conventional Commits.</li>',
        '</ul>',
    ]),
    'terms': [
        {'term': 'User story', 'definition': '“As a <role> I want to <goal>”: one need of one kind of user.'},
        {'term': 'Non-functional requirement', 'definition': 'A quality the system must have (secure, fast, correct money) rather than a feature.'},
        {'term': 'Rubric', 'definition': 'The scoring table mentors use at the demo, with a weight per area.'},
        {'term': 'Handover', 'definition': 'Showing a finished system to the client so they can use and own it.'},
        {'term': 'Self-assessment', 'definition': 'Your own rubric score, compared with the mentors’ score.'},
    ],
    'examTip': 'At the demo, “why is it written this way?” is the real test. If you can explain the row lock in create_booking and the 404 in get_queryset, you understood the week.',
    'lab': {
        'files': [],
        'steps': [
            'Read the user stories and tick each one you can show working on your live URL.',
            'Rehearse the 5-minute live demo on the deployed site, start to finish, with a timer.',
            'Rehearse the API demo: register, login, book, double-book, cancel, against production.',
            'Practise explaining create_booking line by line to a teammate.',
            'Fill in the rubric self-assessment with a score and one sentence of evidence per area.',
            'Write a week retro in LOG.md: 3 strengths and 3 gaps.',
            'Take the practice test for this course and aim for 700 or more.',
        ],
        'check': [
            'Every user story is demonstrable on the live URL.',
            'All tests are green in your final commit and the README is complete.',
            'Your self-assessment and week retro are committed.',
        ],
    },
    'quiz': [
        q('The brief says “prices change sometimes, but old bills must stay the same”. Which design handles it?',
          ['Reading service.price on every report', 'Snapshotting the price on each booking', 'Never changing prices', 'Storing prices as floats'], 1,
          'Booking.price copies the service price at booking time, so history never changes.'),
        q('Which rubric area is worth the most, together with Python fundamentals?',
          ['Testing', 'Deployment', 'API and security', 'Git and communication'], 2,
          'Python fundamentals and API and security are each worth 20.'),
        q('“No double bookings” in the brief is met by…',
          ['A message on the booking page', 'A row lock plus an overlap check in create_booking', 'Checking in the Flutter app', 'Sorting bookings by time'], 1,
          'Only the server can guarantee it, and only with a lock taken before the overlap check.'),
    ],
}


DOMAINS = [
    {'id': 'djd0', 'name': 'Start here', 'weight': 'Day 0',
     'blurb': 'Welcome, machine setup, ground rules and the week at a glance.',
     'lessons': [L0]},
    {'id': 'djd1', 'name': 'Day 1 · Python core', 'weight': 'Day 1',
     'blurb': 'The Python habits that separate working code from code that ships bugs, then a real CSV tool.',
     'lessons': [L1, L2, L3]},
    {'id': 'djd2', 'name': 'Day 2 · Professional Python', 'weight': 'Day 2',
     'blurb': 'A GST invoice engine, its tests, and calling an outside API without taking your site down.',
     'lessons': [L4, L5, L6]},
    {'id': 'djd3', 'name': 'Day 3 · Django foundations', 'weight': 'Day 3',
     'blurb': 'BookIt set up for production, models that protect the data, and the queries behind every report.',
     'lessons': [L7, L8, L9]},
    {'id': 'djd4', 'name': 'Day 4 · Custom staff dashboard', 'weight': 'Day 4',
     'blurb': 'Booking rules in a service layer, safe under load, and the staff web dashboard.',
     'lessons': [L10, L11]},
    {'id': 'djd5', 'name': 'Day 5 · REST APIs', 'weight': 'Day 5',
     'blurb': 'The REST API for the mobile app and the tests that prove it.',
     'lessons': [L12, L13]},
    {'id': 'djd6', 'name': 'Day 6 · Production and demo', 'weight': 'Day 6',
     'blurb': 'Harden and deploy BookIt on Railway, then demo it like a client handover.',
     'lessons': [L14, L15]},
]


def kit_files():
    return sorted(p for p in KIT.rglob('*') if p.is_file() and p.name != '.DS_Store'
                  and '__pycache__' not in p.parts)


def build():
    lessons = [l for d in DOMAINS for l in d['lessons']]
    for lesson in lessons:
        lesson.setdefault('widget', None)
        lesson.setdefault('sorter', None)
    bookit = [f'django/{p.relative_to(KIT).as_posix()}' for p in kit_files()
              if p.relative_to(KIT).parts[0] == 'bookit']
    track = {
        'id': 'django',
        'code': 'Django',
        'name': 'Python & Django Backend Bootcamp',
        'level': 'Intern bootcamp',
        'status': 'Live',
        'outline': 'Nov 2026',
        'order': 'Six days, Monday to Saturday',
        'blurb': ('Six days from “I know some Python” to a deployed Django product. You build a GST invoice engine and '
                  'BookIt, a booking platform with a custom staff dashboard and a JWT REST API for a Flutter app, '
                  'then deploy it on Railway and demo it like a client handover.'),
        'facts': [[str(len(lessons)), 'lessons over six days'],
                  [str(sum(len(l['lab']['steps']) for l in lessons)), 'hands-on lab steps'],
                  [str(sum(len(l['quiz']) for l in lessons)), 'quiz questions with explanations'],
                  ['1', 'complete Django project to download and extend']],
        'tool': 'Python 3.12+, VS Code, PostgreSQL (SQLite is fine to start)',
        'guide': 'https://docs.djangoproject.com/en/5.2/',
        'note': ('Written for Django 5.2 and Django REST Framework 3.16 (November 2026). GST rates and rules in the '
                 'examples are for teaching; confirm current slabs with an accountant before using them in a client project.'),
        'data': bookit,
        'category': 'development',
        'domains': DOMAINS,
        'questionBank': [],
    }
    (CONTENT / 'django.json').write_text(json.dumps(track, indent=1, ensure_ascii=False) + '\n', encoding='utf-8')

    index_path = CONTENT / 'files-index.json'
    index = json.loads(index_path.read_text(encoding='utf-8'))
    index = {k: v for k, v in index.items() if not k.startswith('django/')}
    for p in kit_files():
        rel = p.relative_to(KIT).as_posix()
        desc = DESCRIPTIONS.get(rel) or f'BookIt project file: {rel.removeprefix("bookit/")}'
        index[f'django/{rel}'] = {'path': rel, 'description': desc}
    index_path.write_text(json.dumps(index, indent=1, ensure_ascii=False) + '\n', encoding='utf-8')

    used = {fid for l in lessons for fid in l['lab']['files']}
    missing = sorted(used - set(index))
    if missing:
        raise SystemExit(f'Lab files not in the kit: {missing}')
    print(f'django.json: {len(DOMAINS)} domains, {len(lessons)} lessons, '
          f'{sum(len(l["quiz"]) for l in lessons)} questions; {len(kit_files())} kit files indexed.')


if __name__ == '__main__':
    build()
