from __future__ import annotations

import math
import uuid
from collections import defaultdict
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.banking import Account, Transaction
from app.models.identity import Customer
from app.models.intelligence import CustomerRiskProfile


def _clamp(value: float, lower: float = 0.0, upper: float = 100.0) -> float:
    return max(lower, min(upper, value))


def _months_for(transactions: list[tuple[Transaction, str]]) -> int:
    months = {month for _, month in transactions}
    return max(1, len(months))


def _stddev(values: list[float]) -> float:
    if len(values) < 2:
        return 0.0
    mean = sum(values) / len(values)
    return math.sqrt(sum((value - mean) ** 2 for value in values) / len(values))


async def recalculate_risk_profiles(
    db: AsyncSession,
    customer_ids: list[uuid.UUID] | None = None,
) -> int:
    customer_query = select(Customer)
    if customer_ids:
        customer_query = customer_query.where(Customer.id.in_(customer_ids))
    customers = list((await db.execute(customer_query)).scalars().all())
    if not customers:
        return 0

    transaction_query = (
        select(Account.customer_id, Transaction, )
        .join(Transaction, Transaction.account_id == Account.id)
        .where(Account.customer_id.in_([customer.id for customer in customers]))
    )
    transaction_rows = (await db.execute(transaction_query)).all()
    transactions_by_customer: dict[uuid.UUID, list[tuple[Transaction, str]]] = defaultdict(list)
    for row in transaction_rows:
        transaction = row[1]
        transactions_by_customer[row[0]].append(
            (transaction, transaction.transaction_date.strftime("%Y-%m"))
        )

    existing = {
        profile.customer_id: profile
        for profile in (
            await db.execute(
                select(CustomerRiskProfile).where(
                    CustomerRiskProfile.customer_id.in_(
                        [customer.id for customer in customers]
                    )
                )
            )
        ).scalars()
    }
    calculated_at = datetime.now(timezone.utc)

    for customer in customers:
        customer_transactions = transactions_by_customer.get(customer.id, [])
        months = _months_for(customer_transactions)
        salary_credits = sum(
            float(transaction.amount)
            for transaction, _ in customer_transactions
            if transaction.transaction_type == "CREDIT"
            and transaction.category == "SALARY"
        )
        monthly_income = (
            salary_credits / months
            if salary_credits
            else float(customer.annual_income or 0) / 12
        )
        monthly_spending = sum(
            float(transaction.amount)
            for transaction, _ in customer_transactions
            if transaction.transaction_type == "DEBIT"
        ) / months
        monthly_debt = sum(
            float(transaction.amount)
            for transaction, _ in customer_transactions
            if transaction.transaction_type == "DEBIT"
            and transaction.category == "LOAN_EMI"
        ) / months

        monthly_spending_by_month: dict[str, float] = defaultdict(float)
        for transaction, month in customer_transactions:
            if transaction.transaction_type == "DEBIT":
                monthly_spending_by_month[month] += float(transaction.amount)
        volatility = (
            _stddev(list(monthly_spending_by_month.values()))
            / monthly_spending
            if monthly_spending
            else 0.0
        )
        savings_ratio = (
            (monthly_income - monthly_spending) / monthly_income
            if monthly_income
            else 0.0
        )
        debt_to_income_ratio = (
            monthly_debt / monthly_income if monthly_income else 0.0
        )

        financial_health_score = _clamp(
            70
            + savings_ratio * 35
            - min(debt_to_income_ratio, 2.0) * 20
            - min(volatility, 2.0) * 10
        )
        overall_risk_score = _clamp(
            (100 - financial_health_score) * 0.42
            + min(debt_to_income_ratio, 1.5) * 12
            + min(volatility, 2.0) * 5
        )

        profile = existing.get(customer.id)
        if profile is None:
            profile = CustomerRiskProfile(customer_id=customer.id)
            db.add(profile)
        profile.overall_risk_score = round(overall_risk_score, 4)
        profile.financial_health_score = round(financial_health_score, 4)
        profile.savings_ratio = round(savings_ratio, 4)
        profile.debt_to_income_ratio = round(debt_to_income_ratio, 4)
        profile.last_calculated_at = calculated_at

    await db.flush()
    return len(customers)


async def recalculate_risk_profile(
    db: AsyncSession, customer_id: uuid.UUID
) -> CustomerRiskProfile:
    await recalculate_risk_profiles(db, [customer_id])
    profile = await db.scalar(
        select(CustomerRiskProfile).where(
            CustomerRiskProfile.customer_id == customer_id
        )
    )
    if profile is None:
        raise RuntimeError(f"Risk profile was not created for customer {customer_id}")
    return profile
