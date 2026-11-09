from datetime import date
from decimal import Decimal

import pytest

from invoice import Invoice, InvoiceNumberGenerator, LineItem, Party, financial_year

KERALA_SELLER = Party("Ralfiz Technologies", "32")


@pytest.fixture
def web_item() -> LineItem:
    return LineItem("Website development", "998314", 1, Decimal("10000"), Decimal("18"))


def make_invoice(buyer_state: str) -> Invoice:
    return Invoice("T/1", date(2026, 11, 9), KERALA_SELLER, Party("Client", buyer_state))


def test_intra_state_splits_cgst_and_sgst(web_item):
    t = make_invoice("32").add(web_item).totals()
    assert t["cgst"] == t["sgst"] == Decimal("900.00")
    assert t["igst"] == Decimal("0.00")
    assert t["grand_total"] == Decimal("11800.00")


def test_inter_state_uses_igst(web_item):
    t = make_invoice("29").add(web_item).totals()
    assert t["igst"] == Decimal("1800.00")
    assert t["cgst"] == Decimal("0.00")


def test_round_off_to_nearest_rupee():
    item = LineItem("Strap", "9113", 1, Decimal("99.99"), Decimal("18"))
    t = make_invoice("32").add(item).totals()
    assert t["grand_total"] == Decimal("118.00")
    assert t["round_off"] == Decimal("0.01")


@pytest.mark.parametrize(
    "day, expected",
    [(date(2026, 3, 31), "2025-26"), (date(2026, 4, 1), "2026-27"), (date(2027, 1, 15), "2026-27")],
)
def test_financial_year(day, expected):
    assert financial_year(day) == expected


def test_invoice_numbers_are_sequential():
    gen = InvoiceNumberGenerator(prefix="RLZ")
    assert gen.next(date(2026, 11, 9)) == "RLZ/2026-27/0001"
    assert gen.next(date(2026, 11, 9)) == "RLZ/2026-27/0002"


@pytest.mark.parametrize("kwargs", [{"qty": 0}, {"gst_rate": Decimal("7")}, {"discount": Decimal("-1")}])
def test_invalid_line_items_rejected(kwargs):
    data = {"description": "x", "hsn_sac": "1", "qty": 1, "unit_price": Decimal("100"), "gst_rate": Decimal("18")}
    data.update(kwargs)
    with pytest.raises(ValueError):
        LineItem(**data)


def test_gstin_must_match_state():
    with pytest.raises(ValueError):
        Party("Wrong", "29", gstin="32ABCDE1234F1Z5")
