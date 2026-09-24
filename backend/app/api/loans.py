from fastapi import APIRouter, Depends

from app.core.dependencies import get_current_user
from app.models.identity import User
from app.schemas.loan import (
    LoanApplicationCreate,
    LoanEligibilityRequest,
)


router = APIRouter(
    prefix="/loans",
    tags=["Loans"],
)


@router.get("/products")
async def get_loan_products(
    current_user: User = Depends(get_current_user),
):
    return {
        "message": "Loan products will be implemented here"
    }


@router.post("/eligibility")
async def check_eligibility(
    payload: LoanEligibilityRequest,
    current_user: User = Depends(get_current_user),
):
    return {
        "message": "Loan eligibility will be implemented here",
        "data": payload,
    }


@router.post("/applications")
async def apply_for_loan(
    payload: LoanApplicationCreate,
    current_user: User = Depends(get_current_user),
):
    return {
        "message": "Loan application will be implemented here",
        "data": payload,
    }


@router.get("/applications")
async def get_loan_applications(
    current_user: User = Depends(get_current_user),
):
    return {
        "message": "Loan applications will be implemented here"
    }