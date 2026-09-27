"""
Account + Transaction generator.

Writes rows to:
  - accounts
  - transactions

Account balances are correlated to annual income and customer segment.
Transaction amounts, categories, and merchant names are derived from the
customer's income, occupation, and segment — not independently random.
"""

from __future__ import annotations

import random
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from faker import Faker
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.banking import Account, Transaction
from data.generators.config import (
    ACCOUNTS_PER_CUSTOMER_MAX,
    ACCOUNTS_PER_CUSTOMER_MIN,
    HISTORY_DAYS,
    SEED,
    TRANSACTION_CATEGORIES,
    TRANSACTIONS_PER_ACCOUNT_BASE,
)
from data.generators.customer_generator import CustomerRecord

# ---------------------------------------------------------------------------
# Account type pools per segment
# ---------------------------------------------------------------------------

ACCOUNT_TYPE_POOLS: dict[str, list[str]] = {
    "MASS_MARKET":    ["SAVINGS", "CURRENT"],
    "MASS_AFFLUENT":  ["SAVINGS", "CURRENT", "CREDIT"],
    "AFFLUENT":       ["SAVINGS", "CURRENT", "CREDIT", "INVESTMENT"],
    "HIGH_NET_WORTH": ["SAVINGS", "CURRENT", "CREDIT", "INVESTMENT"],
}

# ---------------------------------------------------------------------------
# Balance multipliers (fraction of annual monthly income per account type)
# ---------------------------------------------------------------------------

BALANCE_MULTIPLIERS: dict[str, tuple[float, float]] = {
    "SAVINGS":    (1.0, 6.0),    # 1–6 months of monthly income
    "CURRENT":    (0.5, 3.0),
    "CREDIT":     (0.1, 1.0),    # credit utilisation as balance
    "INVESTMENT": (3.0, 24.0),   # larger corpus
}

# ---------------------------------------------------------------------------
# Category weights per segment (higher weight → more likely)
# ---------------------------------------------------------------------------
#
# Each row is (category, debit_weight, credit_weight).
# SALARY and INVESTMENT are credits; everything else is a debit.
#
_CATEGORY_CONFIG: list[tuple[str, dict[str, float]]] = [
    # category              MASS_MARKET  MASS_AFFLUENT  AFFLUENT  HIGH_NET_WORTH
    ("SALARY",       {"MASS_MARKET": 8,  "MASS_AFFLUENT": 8,  "AFFLUENT": 8,  "HIGH_NET_WORTH": 8}),
    ("RENT",         {"MASS_MARKET": 12, "MASS_AFFLUENT": 10, "AFFLUENT": 8,  "HIGH_NET_WORTH": 4}),
    ("GROCERIES",    {"MASS_MARKET": 15, "MASS_AFFLUENT": 12, "AFFLUENT": 8,  "HIGH_NET_WORTH": 4}),
    ("FUEL",         {"MASS_MARKET": 8,  "MASS_AFFLUENT": 8,  "AFFLUENT": 6,  "HIGH_NET_WORTH": 4}),
    ("DINING",       {"MASS_MARKET": 5,  "MASS_AFFLUENT": 8,  "AFFLUENT": 10, "HIGH_NET_WORTH": 10}),
    ("UTILITIES",    {"MASS_MARKET": 10, "MASS_AFFLUENT": 8,  "AFFLUENT": 6,  "HIGH_NET_WORTH": 4}),
    ("SHOPPING",     {"MASS_MARKET": 8,  "MASS_AFFLUENT": 10, "AFFLUENT": 12, "HIGH_NET_WORTH": 10}),
    ("TRAVEL",       {"MASS_MARKET": 2,  "MASS_AFFLUENT": 5,  "AFFLUENT": 8,  "HIGH_NET_WORTH": 12}),
    ("SUBSCRIPTIONS",{"MASS_MARKET": 4,  "MASS_AFFLUENT": 5,  "AFFLUENT": 5,  "HIGH_NET_WORTH": 4}),
    ("LOAN_EMI",     {"MASS_MARKET": 10, "MASS_AFFLUENT": 8,  "AFFLUENT": 6,  "HIGH_NET_WORTH": 2}),
    ("INVESTMENT",   {"MASS_MARKET": 2,  "MASS_AFFLUENT": 6,  "AFFLUENT": 10, "HIGH_NET_WORTH": 14}),
]

# Amount ranges (INR) per category per segment
AMOUNT_RANGES: dict[str, dict[str, tuple[float, float]]] = {
    "SALARY":        {"MASS_MARKET": (15_000, 50_000),   "MASS_AFFLUENT": (50_000, 125_000),  "AFFLUENT": (125_000, 333_000),   "HIGH_NET_WORTH": (333_000, 1_666_000)},
    "RENT":          {"MASS_MARKET": (3_000, 12_000),    "MASS_AFFLUENT": (12_000, 35_000),   "AFFLUENT": (35_000, 100_000),    "HIGH_NET_WORTH": (80_000, 300_000)},
    "GROCERIES":     {"MASS_MARKET": (500, 3_000),       "MASS_AFFLUENT": (1_500, 8_000),     "AFFLUENT": (3_000, 20_000),      "HIGH_NET_WORTH": (5_000, 40_000)},
    "FUEL":          {"MASS_MARKET": (500, 3_000),       "MASS_AFFLUENT": (1_500, 6_000),     "AFFLUENT": (3_000, 12_000),      "HIGH_NET_WORTH": (5_000, 20_000)},
    "DINING":        {"MASS_MARKET": (200, 1_500),       "MASS_AFFLUENT": (500, 5_000),       "AFFLUENT": (1_500, 15_000),      "HIGH_NET_WORTH": (5_000, 50_000)},
    "UTILITIES":     {"MASS_MARKET": (500, 3_000),       "MASS_AFFLUENT": (1_000, 6_000),     "AFFLUENT": (2_000, 15_000),      "HIGH_NET_WORTH": (5_000, 30_000)},
    "SHOPPING":      {"MASS_MARKET": (200, 5_000),       "MASS_AFFLUENT": (1_000, 20_000),    "AFFLUENT": (5_000, 80_000),      "HIGH_NET_WORTH": (20_000, 300_000)},
    "TRAVEL":        {"MASS_MARKET": (500, 5_000),       "MASS_AFFLUENT": (3_000, 30_000),    "AFFLUENT": (10_000, 150_000),    "HIGH_NET_WORTH": (50_000, 500_000)},
    "SUBSCRIPTIONS": {"MASS_MARKET": (100, 500),         "MASS_AFFLUENT": (200, 2_000),       "AFFLUENT": (500, 5_000),         "HIGH_NET_WORTH": (1_000, 10_000)},
    "LOAN_EMI":      {"MASS_MARKET": (2_000, 15_000),   "MASS_AFFLUENT": (10_000, 50_000),   "AFFLUENT": (30_000, 150_000),    "HIGH_NET_WORTH": (50_000, 500_000)},
    "INVESTMENT":    {"MASS_MARKET": (500, 5_000),       "MASS_AFFLUENT": (5_000, 50_000),    "AFFLUENT": (20_000, 200_000),    "HIGH_NET_WORTH": (100_000, 2_000_000)},
}

MERCHANT_NAMES: dict[str, list[str]] = {
    "SALARY":        ["Employer Direct", "PayRoll NEFT", "Salary Credit"],
    "RENT":          ["Property Owner", "Housing Society", "Rent Payment"],
    "GROCERIES":     ["DMart", "Reliance Fresh", "Big Bazaar", "Spencer's", "Nature's Basket"],
    "FUEL":          ["Indian Oil", "HPCL", "BPCL", "Shell", "Reliance Petrol"],
    "DINING":        ["Swiggy", "Zomato", "McDonald's", "Domino's", "KFC", "Cafe Coffee Day"],
    "UTILITIES":     ["BSES Electricity", "MTNL", "Airtel", "Jio", "MCGM Water"],
    "SHOPPING":      ["Amazon", "Flipkart", "Myntra", "Meesho", "Nykaa", "Tata CLiQ"],
    "TRAVEL":        ["MakeMyTrip", "Yatra", "IndiGo Airlines", "IRCTC", "Ola Cabs", "Uber"],
    "SUBSCRIPTIONS": ["Netflix", "Amazon Prime", "Spotify", "Hotstar", "Zee5"],
    "LOAN_EMI":      ["HDFC Home Loan", "SBI Car Loan", "ICICI Personal Loan", "Bajaj Finance"],
    "INVESTMENT":    ["Zerodha", "Groww", "ICICI Direct", "HDFC MF", "SBI Mutual Fund"],
}

CHANNELS: list[str] = ["MOBILE", "WEB", "ATM", "CARD", "NETBANKING", "UPI"]
CHANNEL_WEIGHTS: dict[str, list[float]] = {
    "MASS_MARKET":    [0.30, 0.10, 0.25, 0.20, 0.10, 0.05],
    "MASS_AFFLUENT":  [0.35, 0.15, 0.15, 0.20, 0.10, 0.05],
    "AFFLUENT":       [0.40, 0.20, 0.10, 0.15, 0.05, 0.10],
    "HIGH_NET_WORTH": [0.30, 0.30, 0.05, 0.15, 0.05, 0.15],
}


# ---------------------------------------------------------------------------
# Public dataclass returned for use by fraud / behaviour generators
# ---------------------------------------------------------------------------

@dataclass
class AccountRecord:
    account_id: uuid.UUID
    customer_id: uuid.UUID
    account_type: str
    balance: float
    segment: str


@dataclass
class TransactionRecord:
    transaction_id: uuid.UUID
    account_id: uuid.UUID
    customer_id: uuid.UUID
    amount: float
    category: str
    transaction_date: datetime
    is_fraud: bool = False
    channel: str = "MOBILE"


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _category_weights(segment: str) -> tuple[list[str], list[float]]:
    cats = [row[0] for row in _CATEGORY_CONFIG]
    weights = [row[1][segment] for row in _CATEGORY_CONFIG]
    return cats, weights


def _pick_category(rng: random.Random, segment: str) -> str:
    cats, weights = _category_weights(segment)
    return rng.choices(cats, weights=weights, k=1)[0]


def _make_transaction(
    rng: random.Random,
    account_id: uuid.UUID,
    customer_id: uuid.UUID,
    segment: str,
    category: str,
    txn_date: datetime,
) -> tuple[Transaction, TransactionRecord]:
    lo, hi = AMOUNT_RANGES[category][segment]
    amount = round(rng.uniform(lo, hi), 2)
    merchant = rng.choice(MERCHANT_NAMES[category])
    txn_type = "CREDIT" if category in ("SALARY", "INVESTMENT") else "DEBIT"
    channel = rng.choices(CHANNELS, weights=CHANNEL_WEIGHTS[segment], k=1)[0]
    txn_id = uuid.UUID(int=rng.getrandbits(128))

    txn = Transaction(
        id=txn_id,
        account_id=account_id,
        transaction_reference=f"TXN{txn_id.hex[:12].upper()}",
        transaction_type=txn_type,
        amount=Decimal(str(amount)),
        currency="INR",
        category=category,
        description=f"{category.title()} – {merchant}",
        merchant_name=merchant,
        merchant_category=category,
        transaction_status="COMPLETED",
        transaction_date=txn_date,
        channel=channel,
        is_fraud=False,
    )
    record = TransactionRecord(
        transaction_id=txn_id,
        account_id=account_id,
        customer_id=customer_id,
        amount=amount,
        category=category,
        transaction_date=txn_date,
        channel=channel,
    )
    return txn, record


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

async def generate_accounts_and_transactions(
    session: AsyncSession,
    customer_records: list[CustomerRecord],
    seed: int = SEED,
) -> tuple[list[AccountRecord], list[TransactionRecord]]:
    """
    For each customer, generate 1-3 accounts then populate transactions.

    Returns:
        account_records  – used by fraud / behaviour generators
        txn_records      – used by fraud generator
    """
    rng = random.Random(seed + 1)  # offset so account seed ≠ customer seed
    now = datetime.now(timezone.utc)

    all_accounts: list[Account] = []
    all_txns: list[Transaction] = []
    account_records: list[AccountRecord] = []
    txn_records: list[TransactionRecord] = []

    for cust in customer_records:
        monthly_income = cust.annual_income / 12
        num_accounts = rng.randint(ACCOUNTS_PER_CUSTOMER_MIN, ACCOUNTS_PER_CUSTOMER_MAX)

        # Restrict account type pool based on segment
        pool = ACCOUNT_TYPE_POOLS[cust.segment]
        account_types = rng.sample(pool, k=min(num_accounts, len(pool)))

        for acc_type in account_types:
            lo_mul, hi_mul = BALANCE_MULTIPLIERS[acc_type]
            balance = round(monthly_income * rng.uniform(lo_mul, hi_mul), 2)
            acc_id = uuid.UUID(int=rng.getrandbits(128))

            account = Account(
                id=acc_id,
                customer_id=cust.customer_id,
                account_number=f"ACC{acc_id.hex[:12].upper()}",
                account_type=acc_type,
                currency="INR",
                balance=Decimal(str(balance)),
                available_balance=Decimal(str(balance * 0.95)),
                status="ACTIVE",
                opened_at=now - timedelta(days=rng.randint(30, HISTORY_DAYS)),
            )
            all_accounts.append(account)
            account_records.append(
                AccountRecord(
                    account_id=acc_id,
                    customer_id=cust.customer_id,
                    account_type=acc_type,
                    balance=balance,
                    segment=cust.segment,
                )
            )

            # Scale transaction count with segment
            scale = {"MASS_MARKET": 0.7, "MASS_AFFLUENT": 1.0, "AFFLUENT": 1.3, "HIGH_NET_WORTH": 1.6}
            num_txns = int(TRANSACTIONS_PER_ACCOUNT_BASE * scale[cust.segment])

            for _ in range(num_txns):
                txn_days_ago = rng.randint(0, HISTORY_DAYS)
                txn_date = now - timedelta(
                    days=txn_days_ago,
                    hours=rng.randint(0, 23),
                    minutes=rng.randint(0, 59),
                )
                category = _pick_category(rng, cust.segment)
                txn, rec = _make_transaction(
                    rng, acc_id, cust.customer_id, cust.segment, category, txn_date
                )
                all_txns.append(txn)
                txn_records.append(rec)

    session.add_all(all_accounts)
    await session.flush()
    session.add_all(all_txns)
    await session.flush()

    print(f"  [transactions] inserted {len(all_accounts)} accounts + {len(all_txns)} transactions")
    return account_records, txn_records
