from uuid import uuid4

from app.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)


def test_password_hash_round_trip():
    password = "StrongPassword123!"
    password_hash = hash_password(password)

    assert password_hash != password
    assert verify_password(password, password_hash)
    assert not verify_password("WrongPassword123!", password_hash)


def test_jwt_round_trip():
    user_id = uuid4()
    token = create_access_token(user_id, "CUSTOMER")

    payload = decode_access_token(token)

    assert payload["sub"] == str(user_id)
    assert payload["role"] == "CUSTOMER"
    assert "exp" in payload
