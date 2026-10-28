from datetime import date

from app.intelligence.analytics.financial import (
    calculate_financial_insights,
    display_category,
)


def test_display_category_mapping():
    assert display_category("GROCERIES") == "Food"
    assert display_category("DINING") == "Food"
    assert display_category("FUEL") == "Travel"
    assert display_category("LOAN_EMI") == "Other"


def test_month_buckets_include_empty_month():
    categories, monthly = calculate_financial_insights(
        date(2026, 10, 5),
        [("DEBIT", "GROCERIES", date(2026, 7, 2), 100)],
    )
    assert [entry.label for entry in monthly] == ["Jul", "Aug", "Sep", "Oct"]
    assert [entry.spending for entry in monthly] == [100, 0, 0, 0]
    assert categories["Food"] == 100


def test_credits_are_excluded_and_categories_add_to_spending():
    categories, monthly = calculate_financial_insights(
        date(2026, 10, 5),
        [
            ("CREDIT", "SALARY", date(2026, 10, 1), 10_000),
            ("DEBIT", "GROCERIES", date(2026, 10, 2), 100),
            ("DEBIT", "RENT", date(2026, 10, 3), 250),
        ],
    )
    assert sum(categories.values()) == 350
    assert sum(entry.spending for entry in monthly) == 350
    assert sum(entry.income for entry in monthly) == 10_000
