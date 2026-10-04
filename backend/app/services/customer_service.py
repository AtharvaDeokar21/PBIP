from decimal import Decimal

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import RequestContext
from app.models.banking import Account, Payee, Transaction
from app.models.identity import Customer, User
from app.models.products import CustomerInvestment, LoanApplication
from app.schemas.customer import (
    AccountTypeBalance,
    CustomerResponse,
    CustomerSummary,
    CustomerUpdate,
)
from app.services.common import to_money, utcnow, write_audit
from app.services.loan_service import OPEN_APPLICATION_STATUSES


async def get_profile(db: AsyncSession, customer: Customer) -> CustomerResponse:
    # Email is owned by the user record, not the customer record.
    email = await db.scalar(select(User.email).where(User.id == customer.user_id))
    return CustomerResponse(
        id=customer.id,
        customer_number=customer.customer_number,
        first_name=customer.first_name,
        last_name=customer.last_name,
        email=email,
        phone=customer.phone,
        address=customer.address,
        city=customer.city,
        state=customer.state,
        postal_code=customer.postal_code,
        occupation=customer.occupation,
        employment_type=customer.employment_type,
        annual_income=customer.annual_income,
        risk_profile=customer.risk_profile,
        customer_segment=customer.customer_segment,
    )


async def update_profile(
    db: AsyncSession,
    customer: Customer,
    payload: CustomerUpdate,
    ctx: RequestContext,
) -> CustomerResponse:
    changes = payload.model_dump(exclude_unset=True)
    old_value = {field: getattr(customer, field) for field in changes}
    changed = {k: v for k, v in changes.items() if old_value[k] != v}

    if changed:
        for field, value in changed.items():
            setattr(customer, field, value)
        write_audit(
            db,
            user_id=customer.user_id,
            action="CUSTOMER_PROFILE_UPDATED",
            entity_type="CUSTOMER",
            entity_id=customer.id,
            ctx=ctx,
            old_value={k: old_value[k] for k in changed},
            new_value=changed,
        )
        await db.commit()
        await db.refresh(customer)

    return await get_profile(db, customer)


async def get_financial_summary(db: AsyncSession, customer: Customer) -> CustomerSummary:
    accounts = list(
        await db.scalars(select(Account).where(Account.customer_id == customer.id))
    )

    by_type: dict[str, AccountTypeBalance] = {}
    for account in accounts:
        entry = by_type.setdefault(
            account.account_type,
            AccountTypeBalance(account_type=account.account_type, balance=Decimal("0"), account_count=0),
        )
        entry.balance += to_money(account.balance)
        entry.account_count += 1

    month_start = utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    credits, debits = (
        await db.execute(
            select(
                func.coalesce(
                    func.sum(case((Transaction.transaction_type == "CREDIT", Transaction.amount))), 0
                ),
                func.coalesce(
                    func.sum(case((Transaction.transaction_type == "DEBIT", Transaction.amount))), 0
                ),
            )
            .join(Account, Account.id == Transaction.account_id)
            .where(
                Account.customer_id == customer.id,
                Transaction.transaction_date >= month_start,
                Transaction.transaction_status == "COMPLETED",
            )
        )
    ).one()

    active_payees = await db.scalar(
        select(func.count(Payee.id)).where(Payee.customer_id == customer.id, Payee.is_active.is_(True))
    )
    open_loans = await db.scalar(
        select(func.count(LoanApplication.id)).where(
            LoanApplication.customer_id == customer.id,
            LoanApplication.status.in_(OPEN_APPLICATION_STATUSES),
        )
    )
    total_invested = await db.scalar(
        select(func.coalesce(func.sum(CustomerInvestment.amount_invested), 0)).where(
            CustomerInvestment.customer_id == customer.id,
            CustomerInvestment.status == "ACTIVE",
        )
    )

    return CustomerSummary(
        total_balance=sum((to_money(a.balance) for a in accounts), Decimal("0")),
        total_available_balance=sum((to_money(a.available_balance) for a in accounts), Decimal("0")),
        total_accounts=len(accounts),
        active_accounts=sum(1 for a in accounts if a.status == "ACTIVE"),
        balances_by_type=list(by_type.values()),
        month_to_date_credits=to_money(credits),
        month_to_date_debits=to_money(debits),
        active_payees=active_payees or 0,
        open_loan_applications=open_loans or 0,
        total_invested=to_money(total_invested),
    )
