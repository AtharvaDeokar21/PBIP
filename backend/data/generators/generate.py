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
import logging
logging.getLogger("passlib").setLevel(logging.ERROR)

import argparse

from sqlalchemy import func, select, text, delete

from app.core.config import settings
from app.core.database import AsyncSessionLocal, create_async_engine, async_sessionmaker, AsyncSession
from app.models.identity import User, Customer
from app.models.banking import Account, Transaction
from app.models.intelligence import BehaviourEvent
from app.models.fraud import FraudEvent, FraudAlert

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

async def run(is_reset: bool) -> None:
    print("\n" + "=" * 60)
    print("  PBIP Synthetic Data Generator")
    print(f"  SEED={SEED}  NUM_CUSTOMERS={NUM_CUSTOMERS}")
    print("=" * 60 + "\n")

    t_start = time.perf_counter()

    # Create engine with echo=False as requested
    engine = create_async_engine(
        settings.database_url,
        pool_pre_ping=True,
        pool_recycle=1800,
        echo=False,
    )
    SessionLocal = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with SessionLocal() as session:
        async with session.begin():
            # Generate customer records in memory to get the deterministically generated IDs
            in_memory_records = await generate_customers(session, NUM_CUSTOMERS, SEED, write_to_db=False)
            if not in_memory_records:
                return
            
            first_user_id = in_memory_records[0].user_id
            customer_ids = [r.customer_id for r in in_memory_records]
            user_ids = [r.user_id for r in in_memory_records]
            
            exists = await session.execute(select(User.id).where(User.id == first_user_id))
            if exists.scalar():
                if not is_reset:
                    print("Data already exists. Run with --reset to regenerate.")
                    sys.exit(0)
                
                print("Resetting existing generated data...")
                await session.execute(delete(FraudAlert).where(FraudAlert.customer_id.in_(customer_ids)))
                await session.execute(delete(FraudEvent).where(FraudEvent.customer_id.in_(customer_ids)))
                await session.execute(delete(BehaviourEvent).where(BehaviourEvent.customer_id.in_(customer_ids)))
                
                account_id_subq = select(Account.id).where(Account.customer_id.in_(customer_ids)).scalar_subquery()
                await session.execute(delete(Transaction).where(Transaction.account_id.in_(account_id_subq)))
                
                await session.execute(delete(Account).where(Account.customer_id.in_(customer_ids)))
                await session.execute(delete(Customer).where(Customer.id.in_(customer_ids)))
                await session.execute(delete(User).where(User.id.in_(user_ids)))
                print("Reset complete. Generating new data...")

            # 1. Customers (users + customers tables)
            print("[1/4] Generating customers …")
            customer_records = await generate_customers(session, NUM_CUSTOMERS, SEED, write_to_db=True)

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
    parser = argparse.ArgumentParser(description="Synthetic data generator")
    parser.add_argument("--reset", action="store_true", help="Reset existing generated data before running")
    args = parser.parse_args()
    asyncio.run(run(args.reset))


if __name__ == "__main__":
    main()
