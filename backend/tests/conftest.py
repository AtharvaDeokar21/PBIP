"""Shared fixtures for API tests.

Tests NEVER use the shared Supabase database. They run against:
  * an in-memory SQLite database by default (zero setup), or
  * a dedicated Postgres database if ``TEST_DATABASE_URL`` is set,
    e.g. postgresql+asyncpg://postgres:postgres@localhost:5432/pbip_test
    (all tables are dropped and recreated for every test).

Test data is produced with the project's own synthetic data generators
(``data/generators``) and the product catalogue from ``scripts/seed.py``.
"""

import logging
import os
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.pool import StaticPool

from app.core.database import get_db
from app.main import app
from app.models import Base
from app.models.banking import Account, Biller
from app.models.identity import Customer, User
from app.models.intelligence import Recommendation
from app.models.products import InsuranceProduct, InvestmentProduct, LoanProduct
from data.generators.customer_generator import generate_customers
from data.generators.transaction_generator import generate_accounts_and_transactions
from scripts.seed import seed_products

logging.getLogger("passlib").setLevel(logging.ERROR)

TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL", "sqlite+aiosqlite://")
# Password the customer generator assigns to every synthetic user.
GENERATED_PASSWORD = "Password@123"
NUM_TEST_CUSTOMERS = 3


@compiles(JSONB, "sqlite")
def _jsonb_on_sqlite(type_, compiler, **kw):
    return "JSON"


@dataclass
class SeedData:
    user: User
    customer: Customer
    accounts: list[Account]
    loan_product: LoanProduct
    investment_product: InvestmentProduct
    insurance_product: InsuranceProduct
    biller: Biller

    @property
    def funded_account(self) -> Account:
        """The customer's account with the most available balance."""
        return max(self.accounts, key=lambda a: a.available_balance)

    @property
    def other_account(self) -> Account:
        return next(a for a in self.accounts if a.id != self.funded_account.id)


@pytest.fixture
async def session_factory():
    if "supabase" in TEST_DATABASE_URL:
        pytest.exit("Refusing to run tests against the shared Supabase database")

    kwargs = (
        {"poolclass": StaticPool, "connect_args": {"check_same_thread": False}}
        if TEST_DATABASE_URL.startswith("sqlite")
        else {}
    )
    engine = create_async_engine(TEST_DATABASE_URL, **kwargs)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    yield async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    await engine.dispose()


@pytest.fixture
async def seed(session_factory) -> SeedData:
    async with session_factory() as db:
        records = await generate_customers(db, num_customers=NUM_TEST_CUSTOMERS)
        await generate_accounts_and_transactions(db, records)
        await seed_products(db)

        # Pick the generated customer with the most accounts.
        accounts_by_customer: dict[uuid.UUID, list[Account]] = {}
        for account in await db.scalars(select(Account)):
            accounts_by_customer.setdefault(account.customer_id, []).append(account)
        customer_id = max(accounts_by_customer, key=lambda cid: len(accounts_by_customer[cid]))
        accounts = accounts_by_customer[customer_id]
        customer = await db.get(Customer, customer_id)
        user = await db.get(User, customer.user_id)

        # Own-account transfers need a second account.
        if len(accounts) < 2:
            extra = Account(
                customer_id=customer.id,
                account_number=f"ACC{uuid.uuid4().hex[:12].upper()}",
                account_type="CURRENT",
                currency="INR",
                balance=Decimal("50000.00"),
                available_balance=Decimal("50000.00"),
                status="ACTIVE",
                opened_at=datetime.now(timezone.utc),
            )
            db.add(extra)
            accounts.append(extra)

        # Neither generators nor seed.py create billers/recommendations yet.
        biller = Biller(name="BSES Electricity", category="ELECTRICITY", provider_code="BSES001")
        db.add(biller)

        loan_product = await db.scalar(select(LoanProduct).where(LoanProduct.loan_type == "PERSONAL"))
        investment_product = await db.scalar(
            select(InvestmentProduct).order_by(InvestmentProduct.minimum_investment)
        )
        insurance_product = await db.scalar(select(InsuranceProduct))

        db.add(
            Recommendation(
                customer_id=customer.id,
                product_type="INVESTMENT",
                product_id=investment_product.id,
                recommendation_type="CROSS_SELL",
                score=Decimal("0.8500"),
                reason="Regular surplus balance",
                status="ACTIVE",
                created_at=datetime.now(timezone.utc),
                expires_at=datetime.now(timezone.utc) + timedelta(days=30),
            )
        )
        await db.commit()

        return SeedData(
            user=user,
            customer=customer,
            accounts=accounts,
            loan_product=loan_product,
            investment_product=investment_product,
            insurance_product=insurance_product,
            biller=biller,
        )


@pytest.fixture
async def client(session_factory, seed: SeedData):
    """HTTP client logged in (via the real /auth/login) as the seeded customer."""

    async def _get_test_db():
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = _get_test_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post(
            "/api/v1/auth/login",
            json={"email": seed.user.email, "password": GENERATED_PASSWORD},
        )
        assert response.status_code == 200, response.text
        ac.headers["Authorization"] = f"Bearer {response.json()['access_token']}"
        yield ac
    app.dependency_overrides.clear()
