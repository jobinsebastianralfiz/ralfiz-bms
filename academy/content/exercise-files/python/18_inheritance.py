"""Inheritance & polymorphism: the runnable examples from lesson 4.2 of the Complete Python Tutorial.

Run it with:  python3 18_inheritance.py
Then change the code and run it again."""

# ----------------------------------------------------------------------
# inheritance.py
# ----------------------------------------------------------------------
class Employee:
    def __init__(self, name, base_salary):
        self.name = name
        self.base_salary = base_salary

    def monthly_pay(self):
        return self.base_salary

    def describe(self):
        return f"{self.name} ({type(self).__name__}) earns ₹{self.monthly_pay():,}"

class Developer(Employee):                       # Developer IS-AN Employee
    def __init__(self, name, base_salary, tech_allowance):
        super().__init__(name, base_salary)      # reuse the parent's setup
        self.tech_allowance = tech_allowance

    def monthly_pay(self):                       # OVERRIDE
        return self.base_salary + self.tech_allowance

class SalesExecutive(Employee):
    def __init__(self, name, base_salary, sales, commission_rate=0.05):
        super().__init__(name, base_salary)
        self.sales = sales
        self.commission_rate = commission_rate

    def monthly_pay(self):
        return self.base_salary + round(self.sales * self.commission_rate)

team = [
    Employee("Joel", 22000),
    Developer("Anu", 35000, 5000),
    SalesExecutive("Rahul", 20000, sales=400000),
]
for person in team:
    print(person.describe())                     # same call, different behaviour = POLYMORPHISM

print(issubclass(Developer, Employee), isinstance(team[1], Employee))
print("Payroll total: ₹", sum(p.monthly_pay() for p in team))

# ----------------------------------------------------------------------
# duck_typing.py
# ----------------------------------------------------------------------
class SMSNotifier:
    def send(self, to, msg):
        return f"SMS to {to}: {msg}"

class EmailNotifier:
    def send(self, to, msg):
        return f"Email to {to}: {msg}"

class WhatsAppNotifier:
    def send(self, to, msg):
        return f"WhatsApp to {to}: {msg}"

def notify_all(notifiers, to, msg):
    for n in notifiers:
        print(n.send(to, msg))

notify_all([SMSNotifier(), EmailNotifier(), WhatsAppNotifier()], "Anu", "Booking confirmed")

# ----------------------------------------------------------------------
# abc_demo.py
# ----------------------------------------------------------------------
from abc import ABC, abstractmethod

class PaymentGateway(ABC):
    @abstractmethod
    def charge(self, amount: float) -> str:
        """Every gateway MUST implement this."""

    def receipt(self, amount):                 # shared, concrete method
        return f"Paid ₹{amount} via {type(self).__name__}: {self.charge(amount)}"

class Razorpay(PaymentGateway):
    def charge(self, amount):
        return "rzp_txn_001"

class Stripe(PaymentGateway):
    def charge(self, amount):
        return "pi_3Nx..."

for gateway in [Razorpay(), Stripe()]:
    print(gateway.receipt(499))

class Broken(PaymentGateway):
    pass

try:
    Broken()
except TypeError as e:
    print("Error:", e)

# ----------------------------------------------------------------------
# composition.py
# ----------------------------------------------------------------------
class Address:
    def __init__(self, city, pin):
        self.city, self.pin = city, pin
    def __str__(self):
        return f"{self.city} - {self.pin}"

class Customer:
    def __init__(self, name, address):
        self.name = name
        self.address = address                  # Customer HAS-AN Address

c = Customer("Diya", Address("Perinthalmanna", "679322"))
print(c.name, "lives in", c.address)

# ----------------------------------------------------------------------
# mro.py
# ----------------------------------------------------------------------
class TimestampMixin:
    def stamp(self):
        return "created 2026-11-09"

class JsonMixin:
    def to_json(self):
        import json
        return json.dumps(self.__dict__)

class Booking(TimestampMixin, JsonMixin):
    def __init__(self, service):
        self.service = service

b = Booking("Car Wash")
print(b.stamp(), b.to_json())
print([cls.__name__ for cls in Booking.__mro__])   # Method Resolution Order
