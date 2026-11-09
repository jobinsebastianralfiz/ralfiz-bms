"""Daily sales report generator.

Reads a POS sales export (CSV), validates every row, and produces:
  * a JSON summary (grand total, by payment mode, top products)
  * an errors.csv with every rejected row and the reason

Usage:
    python sales_report.py data/sales.csv --out report.json --top 5
"""
from __future__ import annotations

import argparse
import csv
import json
import logging
import sys
from collections import defaultdict
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
logger = logging.getLogger("sales_report")

REQUIRED = ("invoice_no", "date", "product", "qty", "unit_price", "payment_mode")


class RowError(ValueError):
    """Raised when a CSV row cannot be turned into a Sale."""


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
    return Sale(
        invoice_no=row["invoice_no"].strip(),
        date=row["date"].strip(),
        product=row["product"].strip(),
        qty=qty,
        unit_price=price,
        payment_mode=row["payment_mode"].strip().upper(),
    )


def load_sales(path: Path) -> tuple[list[Sale], list[dict]]:
    sales: list[Sale] = []
    errors: list[dict] = []
    with path.open(newline="", encoding="utf-8") as f:
        # start=2 because line 1 is the header
        for line_no, row in enumerate(csv.DictReader(f), start=2):
            try:
                sales.append(parse_row(row))
            except RowError as exc:
                errors.append({"line": line_no, "error": str(exc), **row})
    return sales, errors


def summarise(sales: list[Sale], top: int = 5) -> dict:
    revenue_by_product: dict[str, Decimal] = defaultdict(Decimal)
    qty_by_product: dict[str, int] = defaultdict(int)
    revenue_by_mode: dict[str, Decimal] = defaultdict(Decimal)

    for sale in sales:
        revenue_by_product[sale.product] += sale.total
        qty_by_product[sale.product] += sale.qty
        revenue_by_mode[sale.payment_mode] += sale.total

    ranked = sorted(revenue_by_product.items(), key=lambda kv: kv[1], reverse=True)
    return {
        "grand_total": str(sum((s.total for s in sales), Decimal("0"))),
        "invoices": len({s.invoice_no for s in sales}),
        "by_payment_mode": {mode: str(v) for mode, v in sorted(revenue_by_mode.items())},
        "top_products": [
            {"product": name, "qty": qty_by_product[name], "revenue": str(value)}
            for name, value in ranked[:top]
        ],
    }


def write_errors(errors: list[dict], path: Path) -> None:
    if not errors:
        return
    fieldnames = ["line", "error", *REQUIRED]
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(errors)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate a daily sales summary")
    parser.add_argument("csv_file", type=Path)
    parser.add_argument("--out", type=Path, default=Path("report.json"))
    parser.add_argument("--top", type=int, default=5)
    args = parser.parse_args(argv)

    if not args.csv_file.exists():
        logger.error("File not found: %s", args.csv_file)
        return 1

    sales, errors = load_sales(args.csv_file)
    report = summarise(sales, top=args.top)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    write_errors(errors, args.out.with_name("errors.csv"))

    logger.info("Valid rows: %d | Rejected: %d", len(sales), len(errors))
    logger.info("Grand total: Rs %s -> %s", report["grand_total"], args.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
