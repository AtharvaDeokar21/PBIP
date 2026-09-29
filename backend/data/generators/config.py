"""
Synthetic data generator configuration.

All generator modules import from this file.  Changing SEED guarantees
a different-but-still-deterministic dataset; changing NUM_CUSTOMERS
scales the whole pipeline proportionally.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Reproducibility
# ---------------------------------------------------------------------------
SEED: int = 42  # Change to get a different-but-repeatable dataset.

# ---------------------------------------------------------------------------
# Volume
# ---------------------------------------------------------------------------
NUM_CUSTOMERS: int = 1000

# Min/max accounts a single customer can have (savings/current/credit/investment)
ACCOUNTS_PER_CUSTOMER_MIN: int = 1
ACCOUNTS_PER_CUSTOMER_MAX: int = 3

# Transactions generated per account (baseline; scaled by segment below)
TRANSACTIONS_PER_ACCOUNT_BASE: int = 40

# Behaviour events generated per customer
BEHAVIOUR_EVENTS_PER_CUSTOMER: int = 25

# Fraction of customers who receive at least one injected fraud scenario
FRAUD_CUSTOMER_FRACTION: float = 0.05  # 5 %

# ---------------------------------------------------------------------------
# Segmentation thresholds
# ---------------------------------------------------------------------------
#
#  Customer segments are derived from a weighted composite score:
#
#      score = (annual_income / 1_000_000)          # income in millions
#            + (total_balance / 500_000)             # checking+savings balance
#            + (investment_holdings / 2_000_000)     # investment portfolio
#
#  Thresholds (score):
#      score < 1.5  →  MASS_MARKET     (income < ₹4.5 L/yr, minimal savings)
#      1.5 ≤ score < 4 →  MASS_AFFLUENT (₹4.5 – ₹15 L/yr, some savings)
#      4   ≤ score < 10 → AFFLUENT      (₹15 – ₹40 L/yr, meaningful portfolio)
#      score ≥ 10        → HIGH_NET_WORTH (₹40 L+/yr, large portfolio)
#
SEGMENT_MASS_MARKET_MAX: float = 1.5
SEGMENT_MASS_AFFLUENT_MAX: float = 4.0
SEGMENT_AFFLUENT_MAX: float = 10.0

# ---------------------------------------------------------------------------
# Income bands (annual, INR) used when creating customers
# ---------------------------------------------------------------------------
INCOME_BANDS: dict[str, tuple[int, int]] = {
    "MASS_MARKET":    (180_000,  600_000),
    "MASS_AFFLUENT":  (600_001, 1_500_000),
    "AFFLUENT":       (1_500_001, 4_000_000),
    "HIGH_NET_WORTH": (4_000_001, 20_000_000),
}

# Probability weight for each segment when bootstrapping customers
SEGMENT_WEIGHTS: dict[str, float] = {
    "MASS_MARKET":    0.55,
    "MASS_AFFLUENT":  0.28,
    "AFFLUENT":       0.12,
    "HIGH_NET_WORTH": 0.05,
}

# ---------------------------------------------------------------------------
# Date range for synthetic history (past N days from "now")
# ---------------------------------------------------------------------------
HISTORY_DAYS: int = 365

# ---------------------------------------------------------------------------
# Transaction categories
# ---------------------------------------------------------------------------
TRANSACTION_CATEGORIES: list[str] = [
    "SALARY",
    "RENT",
    "GROCERIES",
    "FUEL",
    "DINING",
    "UTILITIES",
    "SHOPPING",
    "TRAVEL",
    "SUBSCRIPTIONS",
    "LOAN_EMI",
    "INVESTMENT",
]
