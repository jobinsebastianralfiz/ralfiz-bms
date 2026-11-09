"""Type hints: the runnable examples from lesson 5.4 of the Complete Python Tutorial.

Run it with:  python3 24_typing.py
Then change the code and run it again."""

# ----------------------------------------------------------------------
# type_hints.py
# ----------------------------------------------------------------------
from typing import Optional, Callable, TypedDict, Literal, Protocol

def add_gst(amount: float, rate: float = 18.0) -> float:
    return round(amount * (1 + rate / 100), 2)

def find_user(user_id: int) -> Optional[dict]:      # dict or None (also written: dict | None)
    return {"id": 1, "name": "Anu"} if user_id == 1 else None

def total(prices: list[float]) -> float:
    return sum(prices)

stock: dict[str, int] = {"watch": 12}
point: tuple[float, float] = (10.97, 76.22)
tags: set[str] = {"new", "sale"}

class OrderDict(TypedDict):                          # shape of a dict (great for API data)
    id: int
    status: Literal["pending", "paid"]
    amount: float

order: OrderDict = {"id": 7, "status": "paid", "amount": 499.0}

def apply(func: Callable[[float], float], value: float) -> float:
    return func(value)

class Notifier(Protocol):                            # structural typing: "anything with send()"
    def send(self, to: str, msg: str) -> str: ...

class SMS:
    def send(self, to: str, msg: str) -> str:
        return f"SMS {to}: {msg}"

def alert(n: Notifier) -> None:
    print(n.send("9895663498", "Server down"))

print(add_gst(1000), find_user(2), total([1.5, 2.5]), apply(add_gst, 100))
alert(SMS())
print(add_gst.__annotations__)

# Hints are NOT enforced at runtime — Python runs this happily:
def repeat(word: str) -> str:
    return str(word) * 2
print(repeat(21))        # passed an int, got "2121"; a type checker would flag it
