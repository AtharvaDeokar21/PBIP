from fastapi import APIRouter, Depends

from app.core.dependencies import get_current_user
from app.core.dependencies import require_roles
from app.models.identity import User


router = APIRouter(
    prefix="/analytics",
    tags=["Analytics"],
)


@router.get(
    "/customers",
    dependencies=[
        Depends(
            require_roles(
                "RELATIONSHIP_MANAGER",
                "ADMIN",
            )
        )
    ],
)
async def customer_analytics(
    current_user: User = Depends(get_current_user),
):
    return {
        "message": "Customer analytics will be implemented here"
    }


@router.get(
    "/transactions",
    dependencies=[
        Depends(
            require_roles(
                "RELATIONSHIP_MANAGER",
                "ADMIN",
            )
        )
    ],
)
async def transaction_analytics(
    current_user: User = Depends(get_current_user),
):
    return {
        "message": "Transaction analytics will be implemented here"
    }