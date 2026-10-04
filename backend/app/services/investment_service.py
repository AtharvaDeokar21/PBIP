from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import RequestContext
from app.core.exceptions import BusinessRuleError, NotFoundError
from app.models.identity import Customer
from app.models.products import CustomerInvestment, InvestmentProduct
from app.schemas.investment import InvestmentCreate
from app.services.common import (
    create_notification,
    debit_account,
    ensure_account_active,
    ensure_sufficient_funds,
    get_owned_account,
    mask_account_number,
    to_money,
    utcnow,
    write_audit,
)


async def list_products(
    db: AsyncSession, *, product_type: str | None = None, risk_level: str | None = None
) -> list[InvestmentProduct]:
    query = select(InvestmentProduct).where(InvestmentProduct.is_active.is_(True))
    if product_type:
        query = query.where(InvestmentProduct.product_type == product_type.upper())
    if risk_level:
        query = query.where(InvestmentProduct.risk_level == risk_level.upper())
    result = await db.scalars(query.order_by(InvestmentProduct.name))
    return list(result)


async def get_product(db: AsyncSession, product_id: UUID) -> InvestmentProduct:
    product = await db.scalar(
        select(InvestmentProduct).where(
            InvestmentProduct.id == product_id, InvestmentProduct.is_active.is_(True)
        )
    )
    if product is None:
        raise NotFoundError("Investment product not found")
    return product


async def list_holdings(db: AsyncSession, customer: Customer) -> list[CustomerInvestment]:
    result = await db.scalars(
        select(CustomerInvestment)
        .where(CustomerInvestment.customer_id == customer.id)
        .order_by(CustomerInvestment.purchase_date.desc(), CustomerInvestment.id)
    )
    return list(result)


async def purchase(
    db: AsyncSession, customer: Customer, payload: InvestmentCreate, ctx: RequestContext
) -> CustomerInvestment:
    """Simulated purchase: no market execution, value starts at the invested amount."""
    amount = to_money(payload.amount_invested)
    product = await get_product(db, payload.investment_product_id)
    if amount < to_money(product.minimum_investment):
        raise BusinessRuleError(
            f"Minimum investment for this product is {to_money(product.minimum_investment)}"
        )

    source_label = None
    if payload.source_account_id:
        account = await get_owned_account(db, customer.id, payload.source_account_id, lock=True)
        ensure_account_active(account)
        ensure_sufficient_funds(account, amount)
        debit_account(
            db,
            account,
            amount,
            category="INVESTMENT",
            description=f"Investment in {product.name}",
            prefix="TXN",
            merchant_name=product.name,
        )
        source_label = mask_account_number(account.account_number)

    investment = CustomerInvestment(
        customer_id=customer.id,
        investment_product_id=product.id,
        amount_invested=amount,
        current_value=amount,
        purchase_date=utcnow().date(),
        status="ACTIVE",
    )
    db.add(investment)
    await db.flush()

    write_audit(
        db,
        user_id=customer.user_id,
        action="INVESTMENT_PURCHASED",
        entity_type="CUSTOMER_INVESTMENT",
        entity_id=investment.id,
        ctx=ctx,
        new_value={
            "investment_product_id": product.id,
            "amount_invested": amount,
            "source_account": source_label,
        },
    )
    create_notification(
        db,
        user_id=customer.user_id,
        type="INVESTMENT_PURCHASED",
        title="Investment recorded",
        message=f"INR {amount} invested in {product.name}.",
    )
    await db.commit()
    await db.refresh(investment)
    return investment
