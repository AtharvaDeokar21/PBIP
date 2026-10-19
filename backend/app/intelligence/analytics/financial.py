from __future__ import annotations

from calendar import monthrange
from dataclasses import dataclass
from datetime import date


CATEGORY_LABELS = {
    "GROCERIES": "Food",
    "DINING": "Food",
    "SHOPPING": "Shopping",
    "TRAVEL": "Travel",
    "FUEL": "Travel",
    "UTILITIES": "Utilities",
    "SUBSCRIPTIONS": "Entertainment",
}

DISPLAY_CATEGORIES = ("Food", "Shopping", "Travel", "Utilities", "Entertainment", "Other")


def display_category(category: str | None) -> str:
    return CATEGORY_LABELS.get(category or "", "Other")


def add_months(value: date, months: int) -> date:
    month_index = value.year * 12 + value.month - 1 + months
    year, month = divmod(month_index, 12)
    return date(year, month + 1, min(value.day, monthrange(year, month + 1)[1]))


def month_buckets(latest_date: date, count: int = 4) -> list[date]:
    latest_month = latest_date.replace(day=1)
    return [add_months(latest_month, offset) for offset in range(-(count - 1), 1)]


@dataclass(frozen=True)
class MonthlyTotals:
    label: str
    income: float
    spending: float


def calculate_financial_insights(
    latest_date: date | None,
    rows: list[tuple[str, str | None, date, float]],
) -> tuple[dict[str, float], list[MonthlyTotals]]:
    categories = {label: 0.0 for label in DISPLAY_CATEGORIES}
    buckets = month_buckets(latest_date or date.today())
    bucket_index = {month: index for index, month in enumerate(buckets)}
    monthly_income = [0.0] * len(buckets)
    monthly_spending = [0.0] * len(buckets)

    for transaction_type, category, transaction_date, amount in rows:
        index = bucket_index.get(transaction_date.replace(day=1))
        if index is None:
            continue
        value = float(amount)
        if transaction_type == "DEBIT":
            categories[display_category(category)] += value
            monthly_spending[index] += value
        elif transaction_type == "CREDIT":
            monthly_income[index] += value

    return categories, [
        MonthlyTotals(
            label=month.strftime("%b"),
            income=monthly_income[index],
            spending=monthly_spending[index],
        )
        for index, month in enumerate(buckets)
    ]
