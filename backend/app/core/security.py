from datetime import datetime, timedelta, timezone
from uuid import UUID

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return pwd_context.verify(password, password_hash)


def create_access_token(subject: UUID | str, role: str) -> str:
    expires = datetime.now(timezone.utc) + timedelta(
        minutes=settings.access_token_expire_minutes
    )
    payload = {
        "sub": str(subject),
        "role": role,
        "exp": expires,
    }
    return jwt.encode(
        payload,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )


def decode_access_token(token: str) -> dict:
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )

        subject = payload.get("sub")
        role = payload.get("role")

        if not subject or not role:
            raise ValueError("Invalid token payload")

        return payload

    except JWTError as exc:
        raise ValueError("Invalid or expired token") from exc


def mask_account_number(account_number: str | None) -> str | None:
    """Show only the last 4 digits of an account number, e.g. XXXX1234."""
    if not account_number:
        return account_number
    return f"XXXX{account_number[-4:]}"
