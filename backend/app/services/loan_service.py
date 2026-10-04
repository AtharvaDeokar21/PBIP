from dataclasses import dataclass, field
from decimal import ROUND_HALF_UP, Decimal
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import RequestContext
from app.core.exceptions import BusinessRuleError, ConflictError, NotFoundError
from app.models.identity import Customer
from app.models.intelligence import CustomerRiskProfile
from app.models.products import LoanApplication, LoanProduct
from app.schemas.loan import LoanApplicationCreate, LoanEligibilityRequest, LoanEligibilityResponse
from app.services.common import create_notification, to_money, utcnow, write_audit

OPEN_APPLICATION_STATUSES = ("SUBMITTED", "UNDER_REVIEW")
ACTIVE_LOAN_STATUSES = ("APPROVED",)

# Internal scoring parameters. Only the outcome and generic reasons are exposed.
_MAX_FOIR = Decimal("0.50")  # max share of monthly income going to EMIs
_MIN_SCORE_TO_QUALIFY = Decimal("0.40")
_CREDIT_SCORE_FLOOR, _CREDIT_SCORE_CEIL = 300, 900


def calculate_emi(principal: Decimal, annual_rate_percent: Decimal, months: int) -> Decimal:
    """Reducing-balance EMI: P * r * (1+r)^n / ((1+r)^n - 1), r = monthly rate."""
    if months <= 0:
        raise ValueError("months must be positive")
    principal = Decimal(principal)
    if principal <= 0:
        return Decimal("0.00")

    monthly_rate = Decimal(annual_rate_percent) / Decimal(1200)
    if monthly_rate == 0:
        emi = principal / months
    else:
        growth = (1 + monthly_rate) ** months
        emi = principal * monthly_rate * growth / (growth - 1)
    return emi.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


@dataclass
class EligibilityResult:
    eligible: bool
    score: Decimal
    emi: Decimal
    reasons: list[str] = field(default_factory=list)
    within_product_limits: bool = True


def _clamp(value: Decimal) -> Decimal:
    return max(Decimal(0), min(Decimal(1), value))


def assess_eligibility(
    *,
    product: LoanProduct,
    amount: Decimal,
    tenure_months: int,
    annual_income: Decimal | None,
    credit_score: int | None,
    existing_emi: Decimal,
) -> EligibilityResult:
    """Pure eligibility assessment, kept free of I/O so it is easy to unit test."""
    amount = Decimal(amount)
    emi = calculate_emi(amount, Decimal(product.interest_rate), tenure_months)
    reasons: list[str] = []
    within_limits = True

    if not (Decimal(product.min_amount) <= amount <= Decimal(product.max_amount)):
        within_limits = False
        reasons.append("Requested amount is outside the product's allowed range")
    if not (product.min_tenure_months <= tenure_months <= product.max_tenure_months):
        within_limits = False
        reasons.append("Requested tenure is outside the product's allowed range")

    rules = product.eligibility_rules or {}
    income = Decimal(annual_income) if annual_income else None

    if income is None or income <= 0:
        reasons.append("Income information is required for assessment")
        return EligibilityResult(False, Decimal("0.0000"), emi, reasons, within_limits)

    if "min_income" in rules and income < Decimal(str(rules["min_income"])):
        reasons.append("Income is below the product requirement")
    if "min_credit_score" in rules and (
        credit_score is None or credit_score < int(rules["min_credit_score"])
    ):
        reasons.append("Credit profile does not meet the product requirement")

    monthly_income = income / 12
    foir = (existing_emi + emi) / monthly_income
    max_foir = Decimal(str(rules.get("max_dti", _MAX_FOIR)))
    if foir > max_foir:
        reasons.append("Total repayment obligations exceed the affordable limit")

    # Score: credit quality (50%) + repayment headroom (50%).
    credit_component = (
        _clamp(Decimal(credit_score - _CREDIT_SCORE_FLOOR) / (_CREDIT_SCORE_CEIL - _CREDIT_SCORE_FLOOR))
        if credit_score is not None
        else Decimal("0.5")
    )
    headroom_component = _clamp(1 - foir / max_foir) if max_foir > 0 else Decimal(0)
    score = (credit_component * Decimal("0.5") + headroom_component * Decimal("0.5")).quantize(
        Decimal("0.0001"), rounding=ROUND_HALF_UP
    )

    if score < _MIN_SCORE_TO_QUALIFY and not reasons:
        reasons.append("Overall credit assessment is below the required level")

    eligible = not reasons
    if eligible:
        reasons.append("Meets eligibility criteria")
    return EligibilityResult(eligible, score, emi, reasons, within_limits)


async def list_products(db: AsyncSession, *, loan_type: str | None = None) -> list[LoanProduct]:
    query = select(LoanProduct).where(LoanProduct.is_active.is_(True))
    if loan_type:
        query = query.where(LoanProduct.loan_type == loan_type.upper())
    result = await db.scalars(query.order_by(LoanProduct.name))
    return list(result)


async def get_product(db: AsyncSession, product_id: UUID) -> LoanProduct:
    product = await db.scalar(
        select(LoanProduct).where(LoanProduct.id == product_id, LoanProduct.is_active.is_(True))
    )
    if product is None:
        raise NotFoundError("Loan product not found")
    return product


async def _evaluate(
    db: AsyncSession, customer: Customer, payload: LoanEligibilityRequest
) -> tuple[LoanProduct, EligibilityResult]:
    product = await get_product(db, payload.loan_product_id)
    credit_score = await db.scalar(
        select(CustomerRiskProfile.credit_score).where(
            CustomerRiskProfile.customer_id == customer.id
        )
    )
    existing_emi = await db.scalar(
        select(func.coalesce(func.sum(LoanApplication.emi_amount), 0)).where(
            LoanApplication.customer_id == customer.id,
            LoanApplication.status.in_(ACTIVE_LOAN_STATUSES),
        )
    )
    result = assess_eligibility(
        product=product,
        amount=payload.requested_amount,
        tenure_months=payload.tenure_months,
        annual_income=customer.annual_income,
        credit_score=credit_score,
        existing_emi=to_money(existing_emi),
    )
    return product, result


async def check_eligibility(
    db: AsyncSession, customer: Customer, payload: LoanEligibilityRequest
) -> LoanEligibilityResponse:
    product, result = await _evaluate(db, customer, payload)
    return LoanEligibilityResponse(
        loan_product_id=product.id,
        eligible=result.eligible,
        eligibility_score=result.score,
        interest_rate=product.interest_rate,
        estimated_emi=result.emi,
        reasons=result.reasons,
    )


async def apply(
    db: AsyncSession, customer: Customer, payload: LoanApplicationCreate, ctx: RequestContext
) -> LoanApplication:
    product, result = await _evaluate(db, customer, payload)
    if not result.within_product_limits:
        raise BusinessRuleError("; ".join(result.reasons))

    duplicate = await db.scalar(
        select(LoanApplication.id).where(
            LoanApplication.customer_id == customer.id,
            LoanApplication.loan_product_id == product.id,
            LoanApplication.status.in_(OPEN_APPLICATION_STATUSES),
        )
    )
    if duplicate:
        raise ConflictError("An application for this product is already in progress")

    application = LoanApplication(
        customer_id=customer.id,
        loan_product_id=product.id,
        requested_amount=to_money(payload.requested_amount),
        tenure_months=payload.tenure_months,
        interest_rate=product.interest_rate,
        emi_amount=result.emi,
        eligibility_score=result.score,
        status="SUBMITTED",
        application_date=utcnow(),
    )
    db.add(application)
    await db.flush()

    write_audit(
        db,
        user_id=customer.user_id,
        action="LOAN_APPLICATION_SUBMITTED",
        entity_type="LOAN_APPLICATION",
        entity_id=application.id,
        ctx=ctx,
        new_value={
            "loan_product_id": product.id,
            "requested_amount": application.requested_amount,
            "tenure_months": application.tenure_months,
            "status": application.status,
        },
    )
    create_notification(
        db,
        user_id=customer.user_id,
        type="LOAN_APPLICATION_SUBMITTED",
        title="Loan application submitted",
        message=f"Your {product.name} application for INR {application.requested_amount} has been submitted.",
    )
    await db.commit()
    await db.refresh(application)
    return application


async def list_applications(db: AsyncSession, customer: Customer) -> list[LoanApplication]:
    result = await db.scalars(
        select(LoanApplication)
        .where(LoanApplication.customer_id == customer.id)
        .order_by(LoanApplication.application_date.desc())
    )
    return list(result)


async def get_application(
    db: AsyncSession, customer: Customer, application_id: UUID
) -> LoanApplication:
    application = await db.scalar(
        select(LoanApplication).where(
            LoanApplication.id == application_id,
            LoanApplication.customer_id == customer.id,
        )
    )
    if application is None:
        raise NotFoundError("Loan application not found")
    return application
