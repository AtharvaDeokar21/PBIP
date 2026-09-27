"""
Synthetic data orchestrator.

Run with:
    python -m data.generators.generate

Dependency order:
    customers → accounts + transactions → behaviour events → fraud scenarios

All generators share the same AsyncSession and commit once at the end,
so the dataset is either fully written or fully rolled back.
"""

from __future__ import annotations

import asyncio
import sys
import time
from pathlib import Path

# ---------------------------------------------------------------------------
# Ensure the backend package is importable when running from the repo root.
# ---------------------------------------------------------------------------
_REPO_ROOT = Path(__file__).resolve().parents[2]
_BACKEND_DIR = _REPO_ROOT / "backend"
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))

from sqlalchemy import func, select, text

from app.core.database import AsyncSessionLocal
from data.generators.behaviour_generator import generate_behaviour_events
from data.generators.config import NUM_CUSTOMERS, SEED
from data.generators.customer_generator import generate_customers
from data.generators.fraud_generator import inject_fraud_scenarios
from data.generators.transaction_generator import generate_accounts_and_transactions


# ---------------------------------------------------------------------------
# Row-count helper
# ---------------------------------------------------------------------------

async def _count(session, table_name: str) -> int:
    result = await session.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
    return result.scalar_one()


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------

async def run() -> None:
    print("\n" + "=" * 60)
    print("  PBIP Synthetic Data Generator")
    print(f"  SEED={SEED}  NUM_CUSTOMERS={NUM_CUSTOMERS}")
    print("=" * 60 + "\n")

    t_start = time.perf_counter()

    async with AsyncSessionLocal() as session:
        async with session.begin():

            # 1. Customers (users + customers tables)
            print("[1/4] Generating customers …")
            customer_records = await generate_customers(session, NUM_CUSTOMERS, SEED)

            # 2. Accounts + transactions
            print("[2/4] Generating accounts and transactions …")
            account_records, txn_records = await generate_accounts_and_transactions(
                session, customer_records, SEED
            )

            # 3. Behaviour events
            print("[3/4] Generating behaviour events …")
            await generate_behaviour_events(session, customer_records, SEED)

            # 4. Fraud scenario injection
            print("[4/4] Injecting fraud scenarios …")
            await inject_fraud_scenarios(
                session, customer_records, account_records, txn_records, SEED
            )

        # ----------------------------------------------------------------
        # Final row counts (outside the transaction so we see committed data)
        # ----------------------------------------------------------------
        elapsed = time.perf_counter() - t_start
        print("\n" + "-" * 60)
        print("  Final row counts")
        print("-" * 60)
        tables = [
            "users", "customers", "accounts", "transactions",
            "behaviour_events", "fraud_events", "fraud_alerts",
        ]
        for tbl in tables:
            n = await _count(session, tbl)
            print(f"  {tbl:<25} {n:>8,}")
        print("-" * 60)
        print(f"  Total time: {elapsed:.1f}s")
        print("=" * 60 + "\n")


def main() -> None:
    asyncio.run(run())


if __name__ == "__main__":
    main()
