import asyncio
import sys
import uuid
from decimal import Decimal
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.core.security import hash_password

from app.models.identity import User, Customer
from app.models.banking import Account, Transaction, Payee, Biller
from app.models.intelligence import Recommendation
from app.models.products import (
    LoanProduct,
    InvestmentProduct,
    InsuranceProduct,
)


DEMO_PASSWORD = "PBIP@Demo123"


async def get_or_create_user(
    db: AsyncSession,
    email: str,
    role: str,
    first_name: str,
    last_name: str,
):
    result = await db.execute(
        select(User).where(User.email == email)
    )

    user = result.scalar_one_or_none()

    if user:
        return user

    user = User(
        id=uuid.uuid4(),
        email=email,
        password_hash=hash_password(DEMO_PASSWORD),
        role=role,
        is_active=True,
        mfa_enabled=False,
    )

    db.add(user)
    await db.flush()

    customer = None

    if role == "CUSTOMER":
        customer = Customer(
            id=uuid.uuid4(),
            user_id=user.id,
            customer_number=f"CUST{uuid.uuid4().hex[:8].upper()}",
            first_name=first_name,
            last_name=last_name,
            phone="+919999999999",
            city="Mumbai",
            state="Maharashtra",
            occupation="Software Engineer",
            employment_type="FULL_TIME",
            annual_income=Decimal("1200000"),
            risk_profile="MODERATE",
            customer_segment="MASS_AFFLUENT",
        )

        db.add(customer)
        await db.flush()

    return user


async def seed_users(db: AsyncSession):
    print("Creating demo users...")

    users = [
        (
            "customer@pbip.demo",
            "CUSTOMER",
            "Atharva",
            "Customer",
        ),
        (
            "manager@pbip.demo",
            "RELATIONSHIP_MANAGER",
            "Rahul",
            "Manager",
        ),
        (
            "fraud@pbip.demo",
            "FRAUD_ANALYST",
            "Priya",
            "Fraud",
        ),
        (
            "compliance@pbip.demo",
            "COMPLIANCE_OFFICER",
            "Neha",
            "Compliance",
        ),
        (
            "admin@pbip.demo",
            "ADMIN",
            "Admin",
            "User",
        ),
    ]

    created_users = []

    for email, role, first_name, last_name in users:
        user = await get_or_create_user(
            db,
            email,
            role,
            first_name,
            last_name,
        )

        created_users.append(user)

    return created_users


async def seed_accounts(db: AsyncSession):
    print("Creating demo accounts...")

    result = await db.execute(
        select(Customer).where(
            Customer.customer_number.is_not(None)
        )
    )

    customers = result.scalars().all()

    for customer in customers:

        existing = await db.execute(
            select(Account).where(
                Account.customer_id == customer.id
            )
        )

        if existing.scalars().first():
            continue

        savings = Account(
            id=uuid.uuid4(),
            customer_id=customer.id,
            account_number=f"1000{uuid.uuid4().hex[:8]}",
            account_type="SAVINGS",
            currency="INR",
            balance=Decimal("150000.00"),
            available_balance=Decimal("150000.00"),
            status="ACTIVE",
        )

        current = Account(
            id=uuid.uuid4(),
            customer_id=customer.id,
            account_number=f"2000{uuid.uuid4().hex[:8]}",
            account_type="CURRENT",
            currency="INR",
            balance=Decimal("85000.00"),
            available_balance=Decimal("85000.00"),
            status="ACTIVE",
        )

        db.add_all([savings, current])

    await db.flush()


async def seed_transactions(db: AsyncSession):
    print("Creating demo transactions...")

    result = await db.execute(
        select(Account)
    )

    accounts = result.scalars().all()

    categories = [
        ("GROCERIES", "Fresh Mart", 2500),
        ("DINING", "Food Corner", 850),
        ("TRANSPORT", "Uber", 450),
        ("SHOPPING", "Amazon", 3200),
        ("UTILITIES", "Electricity Board", 1800),
        ("ENTERTAINMENT", "Netflix", 649),
        ("SALARY", "Employer", 95000),
    ]

    for account in accounts:

        existing = await db.execute(
            select(Transaction).where(
                Transaction.account_id == account.id
            )
        )

        if existing.scalars().first():
            continue

        for i in range(20):

            category, merchant, amount = categories[
                i % len(categories)
            ]

            if category == "SALARY":
                transaction_type = "CREDIT"
            else:
                transaction_type = "DEBIT"

            transaction = Transaction(
                id=uuid.uuid4(),
                account_id=account.id,
                transaction_reference=f"TXN{uuid.uuid4().hex[:12].upper()}",
                transaction_type=transaction_type,
                amount=Decimal(str(amount)),
                currency="INR",
                category=category,
                description=f"{category.title()} transaction",
                merchant_name=merchant,
                merchant_category=category,
                transaction_status="COMPLETED",
                transaction_date=datetime.now(timezone.utc)
                - timedelta(days=i),
                channel="MOBILE",
                is_fraud=False,
            )

            db.add(transaction)

    await db.flush()


async def seed_products(db: AsyncSession):
    print("Creating financial products...")

    loan_result = await db.execute(
        select(LoanProduct)
    )

    if not loan_result.scalars().first():

        loans = [
            LoanProduct(
                id=uuid.uuid4(),
                name="Personal Loan",
                loan_type="PERSONAL",
                min_amount=50000,
                max_amount=2000000,
                interest_rate=10.5,
                min_tenure_months=12,
                max_tenure_months=60,
                description="Flexible personal loan for customers.",
                is_active=True,
            ),
            LoanProduct(
                id=uuid.uuid4(),
                name="Home Loan",
                loan_type="HOME",
                min_amount=500000,
                max_amount=10000000,
                interest_rate=8.25,
                min_tenure_months=60,
                max_tenure_months=240,
                description="Home financing solution.",
                is_active=True,
            ),
            LoanProduct(
                id=uuid.uuid4(),
                name="Education Loan",
                loan_type="EDUCATION",
                min_amount=100000,
                max_amount=5000000,
                interest_rate=9.0,
                min_tenure_months=24,
                max_tenure_months=120,
                description="Education financing.",
                is_active=True,
            ),
        ]

        db.add_all(loans)

    investment_result = await db.execute(
        select(InvestmentProduct)
    )

    if not investment_result.scalars().first():

        investments = [
            InvestmentProduct(
                id=uuid.uuid4(),
                name="Balanced Growth Fund",
                product_type="MUTUAL_FUND",
                risk_level="MODERATE",
                expected_return=12.0,
                minimum_investment=1000,
                description="Diversified balanced mutual fund.",
                is_active=True,
            ),
            InvestmentProduct(
                id=uuid.uuid4(),
                name="Government Bond",
                product_type="BOND",
                risk_level="LOW",
                expected_return=7.2,
                minimum_investment=5000,
                description="Low-risk government bond.",
                is_active=True,
            ),
            InvestmentProduct(
                id=uuid.uuid4(),
                name="Equity Growth Fund",
                product_type="MUTUAL_FUND",
                risk_level="HIGH",
                expected_return=15.0,
                minimum_investment=1000,
                description="High-growth equity mutual fund.",
                is_active=True,
            ),
        ]

        db.add_all(investments)

    insurance_result = await db.execute(
        select(InsuranceProduct)
    )

    if not insurance_result.scalars().first():

        insurance = [
            InsuranceProduct(
                id=uuid.uuid4(),
                name="Life Secure",
                insurance_type="LIFE",
                premium=12000,
                coverage_amount=10000000,
                term_years=20,
                risk_level="LOW",
                description="Term life insurance.",
                is_active=True,
            ),
            InsuranceProduct(
                id=uuid.uuid4(),
                name="Health Protect",
                insurance_type="HEALTH",
                premium=8500,
                coverage_amount=500000,
                term_years=1,
                risk_level="LOW",
                description="Health insurance coverage.",
                is_active=True,
            ),
        ]

        db.add_all(insurance)

    await db.flush()


async def seed_billers(db: AsyncSession):
    print("Creating billers...")

    billers = [
        ("BSES Electricity", "ELECTRICITY", "BSES001"),
        ("Mahanagar Gas", "GAS", "MGL001"),
        ("Airtel Postpaid", "MOBILE", "AIRTEL001"),
        ("Jio Fiber", "BROADBAND", "JIOFIBER001"),
        ("MCGM Water", "WATER", "MCGM001"),
    ]

    for name, category, provider_code in billers:
        existing = await db.execute(
            select(Biller).where(Biller.provider_code == provider_code)
        )

        if existing.scalars().first():
            continue

        db.add(
            Biller(
                id=uuid.uuid4(),
                name=name,
                category=category,
                provider_code=provider_code,
                is_active=True,
            )
        )

    await db.flush()


async def seed_recommendations(db: AsyncSession):
    """Demo recommendations for the demo customer.

    Real recommendations are produced by the Internal/Analytics team; these
    only exist so the customer-facing endpoint has data to show.
    """
    print("Creating demo recommendations...")

    result = await db.execute(
        select(Customer)
        .join(User, User.id == Customer.user_id)
        .where(User.email == "customer@pbip.demo")
    )

    customer = result.scalar_one_or_none()

    if customer is None:
        return

    existing = await db.execute(
        select(Recommendation).where(
            Recommendation.customer_id == customer.id,
            Recommendation.status == "ACTIVE",
        )
    )

    if existing.scalars().first():
        return

    investment = (
        await db.execute(
            select(InvestmentProduct).where(
                InvestmentProduct.name == "Balanced Growth Fund"
            )
        )
    ).scalar_one_or_none()

    insurance = (
        await db.execute(
            select(InsuranceProduct).where(
                InsuranceProduct.name == "Health Protect"
            )
        )
    ).scalar_one_or_none()

    now = datetime.now(timezone.utc)

    recommendations = [
        ("INVESTMENT", investment, "0.8500", "Regular surplus balance suits a balanced fund."),
        ("INSURANCE", insurance, "0.7200", "No health cover found on your profile."),
    ]

    for product_type, product, score, reason in recommendations:
        if product is None:
            continue

        db.add(
            Recommendation(
                id=uuid.uuid4(),
                customer_id=customer.id,
                product_type=product_type,
                product_id=product.id,
                recommendation_type="CROSS_SELL",
                score=Decimal(score),
                reason=reason,
                status="ACTIVE",
                created_at=now,
                expires_at=now + timedelta(days=30),
            )
        )

    await db.flush()


async def seed():
    print("=" * 60)
    print("PBIP DATABASE SEED")
    print("=" * 60)

    async with AsyncSessionLocal() as db:

        try:
            await seed_users(db)
            await seed_accounts(db)
            await seed_transactions(db)
            await seed_products(db)
            await seed_billers(db)
            await seed_recommendations(db)

            await db.commit()

            print()
            print("✅ Database seeding completed successfully.")
            print()
            print("Demo password:")
            print(DEMO_PASSWORD)

        except Exception:
            await db.rollback()
            raise


if __name__ == "__main__":
    asyncio.run(seed())