"""GST invoice engine — pure Python, no framework.

Rules implemented
  * Money is always Decimal, rounded HALF_UP to 2 places (never float).
  * Same state (seller.state_code == buyer.state_code) -> CGST + SGST (half each).
  * Different state -> IGST (full rate).
  * Grand total rounded to the nearest rupee; difference shown as round_off.
  * Invoice numbers follow the Indian financial year: RLZ/2026-27/0001.

This module is reused on Day 5 inside the BookIt Django project.
"""
from __future__ import annotations

import itertools
import re
from dataclasses import dataclass, field
from datetime import date
from decimal import ROUND_HALF_UP, Decimal
from enum import Enum

PAISA = Decimal("0.01")
RUPEE = Decimal("1")
ZERO = Decimal("0.00")

# Allowed GST slabs. Rates change by government notification — keep this in
# settings/DB in real projects and confirm current slabs with the accountant.
VALID_RATES = frozenset(Decimal(r) for r in ("0", "3", "5", "18", "40"))

GSTIN_RE = re.compile(r"^\d{2}[A-Z]{5}\d{4}[A-Z][1-9A-Z]Z[0-9A-Z]$")


def money(value: Decimal) -> Decimal:
    return value.quantize(PAISA, rounding=ROUND_HALF_UP)


class SupplyType(str, Enum):
    INTRA = "intra"  # CGST + SGST
    INTER = "inter"  # IGST


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


@dataclass
class LineItem:
    description: str
    hsn_sac: str
    qty: int
    unit_price: Decimal
    gst_rate: Decimal
    discount: Decimal = ZERO

    def __post_init__(self) -> None:
        if self.qty <= 0:
            raise ValueError("qty must be positive")
        if self.gst_rate not in VALID_RATES:
            raise ValueError(f"Unsupported GST rate {self.gst_rate}%")
        if self.discount < 0 or self.discount > self.qty * self.unit_price:
            raise ValueError("discount out of range")

    @property
    def taxable_value(self) -> Decimal:
        return money(self.qty * self.unit_price - self.discount)

    def tax(self, supply: SupplyType) -> dict[str, Decimal]:
        total_tax = self.taxable_value * self.gst_rate / 100
        if supply is SupplyType.INTER:
            return {"cgst": ZERO, "sgst": ZERO, "igst": money(total_tax)}
        half = money(total_tax / 2)
        return {"cgst": half, "sgst": half, "igst": ZERO}


def financial_year(d: date) -> str:
    """Indian FY runs April -> March. 9 Nov 2026 -> '2026-27'."""
    start = d.year if d.month >= 4 else d.year - 1
    return f"{start}-{str(start + 1)[-2:]}"


class InvoiceNumberGenerator:
    """In-memory sequence. In Django we replace this with a DB row
    locked by select_for_update() so two users never get the same number."""

    def __init__(self, prefix: str = "RLZ", start: int = 1) -> None:
        self.prefix = prefix
        self._counter = itertools.count(start)

    def next(self, on: date) -> str:
        return f"{self.prefix}/{financial_year(on)}/{next(self._counter):04d}"


@dataclass
class Invoice:
    number: str
    issue_date: date
    seller: Party
    buyer: Party
    items: list[LineItem] = field(default_factory=list)

    @property
    def supply_type(self) -> SupplyType:
        same_state = self.seller.state_code == self.buyer.state_code
        return SupplyType.INTRA if same_state else SupplyType.INTER

    def add(self, item: LineItem) -> "Invoice":
        self.items.append(item)
        return self  # allows chaining: inv.add(a).add(b)

    def totals(self) -> dict[str, Decimal]:
        taxable = sum((i.taxable_value for i in self.items), ZERO)
        tax = {"cgst": ZERO, "sgst": ZERO, "igst": ZERO}
        for item in self.items:
            for key, value in item.tax(self.supply_type).items():
                tax[key] += value
        gross = taxable + sum(tax.values())
        grand = gross.quantize(RUPEE, rounding=ROUND_HALF_UP)
        return {
            "taxable": money(taxable),
            **{k: money(v) for k, v in tax.items()},
            "round_off": money(grand - gross),
            "grand_total": money(grand),
        }

    def __str__(self) -> str:
        t = self.totals()
        return f"{self.number} | {self.buyer.name} | Rs {t['grand_total']}"


if __name__ == "__main__":
    seller = Party("Ralfiz Technologies", "32")
    gen = InvoiceNumberGenerator()
    inv = Invoice(gen.next(date.today()), date.today(), seller, Party("4Z Watches", "32"))
    inv.add(LineItem("Website development", "998314", 1, Decimal("25000"), Decimal("18")))
    inv.add(LineItem("Domain + hosting (1 yr)", "998315", 1, Decimal("3499"), Decimal("18")))
    print(inv)
    for key, value in inv.totals().items():
        print(f"{key:>12}: {value}")
