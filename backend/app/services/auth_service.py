from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password, verify_password
from app.models.identity import Customer, User
from app.models.system import AuditLog, SecurityEvent


class AuthenticationError(Exception):
    """Raised when authentication or registration cannot be completed."""


async def register_customer(
    db: AsyncSession,
    *,
    email: str,
    password: str,
    first_name: str,
    last_name: str,
    phone: str | None = None,
) -> tuple[User, Customer]:
    normalized_email = email.strip().lower()

    existing = await db.scalar(
        select(User).where(User.email == normalized_email)
    )
    if existing:
        raise AuthenticationError("An account with this email already exists")

    user = User(
        email=normalized_email,
        password_hash=hash_password(password),
        role="CUSTOMER",
        is_active=True,
        mfa_enabled=False,
    )
    db.add(user)
    await db.flush()

    customer = Customer(
        user_id=user.id,
        customer_number=f"PBIP-{uuid4().hex[:10].upper()}",
        first_name=first_name.strip(),
        last_name=last_name.strip(),
        phone=phone,
    )
    db.add(customer)

    db.add(
        AuditLog(
            user_id=user.id,
            action="CUSTOMER_REGISTERED",
            entity_type="USER",
            entity_id=user.id,
            new_value={"email": normalized_email, "role": "CUSTOMER"},
            created_at=datetime.now(timezone.utc),
        )
    )

    await db.commit()
    await db.refresh(user)
    await db.refresh(customer)

    return user, customer


async def authenticate_user(
    db: AsyncSession,
    *,
    email: str,
    password: str,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> User:
    normalized_email = email.strip().lower()

    user = await db.scalar(
        select(User).where(User.email == normalized_email)
    )

    if user is None:
        db.add(
            SecurityEvent(
                event_type="LOGIN_FAILED",
                ip_address=ip_address,
                device_info=user_agent,
                severity="WARNING",
                event_metadata={"reason": "unknown_email", "email": normalized_email},
                created_at=datetime.now(timezone.utc),
            )
        )
        await db.commit()
        raise AuthenticationError("Invalid credentials")

    if not user.is_active:
        db.add(
            SecurityEvent(
                user_id=user.id,
                event_type="LOGIN_FAILED",
                ip_address=ip_address,
                device_info=user_agent,
                severity="WARNING",
                event_metadata={"reason": "inactive_account"},
                created_at=datetime.now(timezone.utc),
            )
        )
        await db.commit()
        raise AuthenticationError("Account is inactive")

    if not verify_password(password, user.password_hash):
        db.add(
            SecurityEvent(
                user_id=user.id,
                event_type="LOGIN_FAILED",
                ip_address=ip_address,
                device_info=user_agent,
                severity="WARNING",
                event_metadata={"reason": "invalid_password"},
                created_at=datetime.now(timezone.utc),
            )
        )
        await db.commit()
        raise AuthenticationError("Invalid credentials")

    user.last_login_at = datetime.now(timezone.utc)

    db.add(
        SecurityEvent(
            user_id=user.id,
            event_type="LOGIN_SUCCESS",
            ip_address=ip_address,
            device_info=user_agent,
            severity="INFO",
            event_metadata={},
            created_at=datetime.now(timezone.utc),
        )
    )

    db.add(
        AuditLog(
            user_id=user.id,
            action="USER_LOGIN",
            entity_type="USER",
            entity_id=user.id,
            created_at=datetime.now(timezone.utc),
            ip_address=ip_address,
            user_agent=user_agent,
        )
    )

    await db.commit()
    await db.refresh(user)

    return user
