from dataclasses import dataclass
from uuid import UUID

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import decode_access_token
from app.models.identity import Customer, User

bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = decode_access_token(credentials.credentials)
        user_id = UUID(payload["sub"])
    except (ValueError, KeyError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = await db.scalar(select(User).where(User.id == user_id))

    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is unavailable",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


def require_roles(*allowed_roles: str):
    normalized_roles = {role.upper() for role in allowed_roles}

    async def dependency(
        current_user: User = Depends(get_current_user),
    ) -> User:
        if current_user.role.upper() not in normalized_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        return current_user

    return dependency


@dataclass(frozen=True)
class RequestContext:
    """Client metadata captured for audit logging."""

    ip_address: str | None
    user_agent: str | None


def get_request_context(request: Request) -> RequestContext:
    user_agent = request.headers.get("user-agent")
    return RequestContext(
        ip_address=request.client.host if request.client else None,
        user_agent=user_agent[:500] if user_agent else None,
    )


async def get_current_customer(
    current_user: User = Depends(require_roles("CUSTOMER")),
    db: AsyncSession = Depends(get_db),
) -> Customer:
    """Resolve the customer profile from the authenticated JWT.

    This is the only way customer-facing endpoints obtain a customer identity;
    a customer_id is never accepted from the client.
    """
    customer = await db.scalar(
        select(Customer).where(Customer.user_id == current_user.id)
    )
    if customer is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer profile not found",
        )
    return customer
