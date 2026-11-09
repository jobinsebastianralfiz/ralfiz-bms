"""Dataclasses & enums: the runnable examples from lesson 4.4 of the Complete Python Tutorial.

Run it with:  python3 20_dataclasses.py
Then change the code and run it again."""

# ----------------------------------------------------------------------
# dataclass_demo.py
# ----------------------------------------------------------------------
from dataclasses import dataclass, field, asdict

@dataclass
class LineItem:
    name: str
    qty: int
    unit_price: float

    @property
    def total(self) -> float:
        return self.qty * self.unit_price

@dataclass
class Invoice:
    number: str
    customer: str
    items: list[LineItem] = field(default_factory=list)   # safe mutable default
    paid: bool = False

    def __post_init__(self):                               # runs after the generated __init__
        if not self.number.startswith("INV-"):
            raise ValueError("Invoice number must start with INV-")

    def add(self, item: LineItem) -> "Invoice":
        self.items.append(item)
        return self

    @property
    def grand_total(self) -> float:
        return sum(i.total for i in self.items)

inv = Invoice("INV-0007", "4Z Watches")
inv.add(LineItem("Website", 1, 25000)).add(LineItem("Hosting", 1, 3499))
print(inv)
print(inv.grand_total)
print(asdict(inv)["items"][0])            # convert to dict (e.g. for JSON)
print(LineItem("A", 1, 10) == LineItem("A", 1, 10))   # True: compares fields

# ----------------------------------------------------------------------
# frozen.py
# ----------------------------------------------------------------------
from dataclasses import dataclass, FrozenInstanceError

@dataclass(frozen=True, order=True)        # immutable + sortable by fields in order
class Version:
    major: int
    minor: int
    patch: int = 0

v = Version(5, 2, 1)
print(sorted([Version(5, 2, 1), Version(4, 2), Version(5, 0, 9)]))
try:
    v.major = 6
except FrozenInstanceError as e:
    print("Cannot modify:", e)
print({v: "current"})                      # frozen → hashable → usable as a dict key

# ----------------------------------------------------------------------
# enum_demo.py
# ----------------------------------------------------------------------
from enum import Enum, IntEnum, auto

class OrderStatus(str, Enum):              # str mix-in → easy JSON/DB storage
    PENDING = "pending"
    PAID = "paid"
    SHIPPED = "shipped"
    CANCELLED = "cancelled"

class Priority(IntEnum):
    LOW = auto()
    MEDIUM = auto()
    HIGH = auto()

status = OrderStatus.PAID
print(status, status.value, status.name)
print(status == "paid")                     # True thanks to the str mix-in
print(OrderStatus("shipped"))               # look up by value
print([s.value for s in OrderStatus])
print(Priority.HIGH > Priority.LOW)

ALLOWED = {
    OrderStatus.PENDING: {OrderStatus.PAID, OrderStatus.CANCELLED},
    OrderStatus.PAID: {OrderStatus.SHIPPED, OrderStatus.CANCELLED},
}
print(OrderStatus.SHIPPED in ALLOWED[OrderStatus.PAID])
