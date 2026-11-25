"""Unit tests for pure domain logic: EMI, loan eligibility, security-event presentation, masking."""

from decimal import Decimal
from types import SimpleNamespace
from uuid import uuid4

import pytest
from jose import jwt

from app.core.config import settings
from app.core.security import decode_access_token, mask_account_number
from app.services.loan_service import assess_eligibility, calculate_emi
from app.services.security_service import (
    derive_channel,
    derive_severity,
    derive_status,
    format_description,
    format_event_type,
)


def _product(**overrides):
    values = dict(
        interest_rate=Decimal("12"),
        min_amount=Decimal("50000"),
        max_amount=Decimal("1000000"),
        min_tenure_months=12,
        max_tenure_months=60,
        eligibility_rules={"min_income": 300000, "min_credit_score": 650},
    )
    values.update(overrides)
    return SimpleNamespace(**values)


# --- EMI -------------------------------------------------------------------


def test_emi_reducing_balance_formula():
    assert calculate_emi(Decimal("100000"), Decimal("12"), 12) == Decimal("8884.88")


def test_emi_zero_interest_splits_principal_evenly():
    assert calculate_emi(Decimal("120000"), Decimal("0"), 12) == Decimal("10000.00")


def test_emi_zero_principal_is_zero():
    assert calculate_emi(Decimal("0"), Decimal("10"), 12) == Decimal("0.00")


def test_emi_requires_positive_tenure():
    with pytest.raises(ValueError):
        calculate_emi(Decimal("1000"), Decimal("10"), 0)


# --- Eligibility --------------------------------------------------------------


def _assess(**kwargs):
    args = dict(
        product=_product(),
        amount=Decimal("200000"),
        tenure_months=36,
        annual_income=Decimal("1200000"),
        credit_score=780,
        existing_emi=Decimal("0"),
    )
    args.update(kwargs)
    return assess_eligibility(**args)


def test_strong_applicant_is_eligible():
    result = _assess()

    assert result.eligible
    assert result.within_product_limits
    assert result.reasons == ["Meets eligibility criteria"]
    assert Decimal("0.5") < result.score <= Decimal("1")


def test_missing_income_is_not_assessed():
    result = _assess(annual_income=None)

    assert not result.eligible
    assert result.score == Decimal("0.0000")
    assert "Income information is required for assessment" in result.reasons


@pytest.mark.parametrize(
    ("kwargs", "reason"),
    [
        ({"amount": Decimal("10000")}, "amount is outside"),
        ({"tenure_months": 120}, "tenure is outside"),
        ({"annual_income": Decimal("200000")}, "Income is below"),
        ({"credit_score": 600}, "Credit profile does not meet"),
        ({"credit_score": None}, "Credit profile does not meet"),
        ({"existing_emi": Decimal("60000")}, "exceed the affordable limit"),
    ],
)
def test_ineligibility_reasons(kwargs, reason):
    result = _assess(**kwargs)

    assert not result.eligible
    assert any(reason in r for r in result.reasons)


def test_out_of_range_request_is_flagged_outside_product_limits():
    assert not _assess(amount=Decimal("5000000")).within_product_limits


def test_low_overall_score_without_rule_breach():
    product = _product(eligibility_rules={})
    result = _assess(product=product, credit_score=310, existing_emi=Decimal("35000"))

    assert not result.eligible
    assert "Overall credit assessment is below the required level" in result.reasons


def test_product_specific_dti_limit_is_respected():
    product = _product(eligibility_rules={"max_dti": 0.05})

    assert any("affordable limit" in r for r in _assess(product=product).reasons)


# --- Security event presentation -------------------------------------------


@pytest.mark.parametrize(
    ("device", "channel"),
    [
        (None, "Unknown"),
        ("   ", "Unknown"),
        ("curl/8.4", "API"),
        ("python-httpx/0.28", "API"),
        ("Mozilla/5.0 (Linux; Android 14) Mobile", "Mobile app"),
        ("ATM-Terminal-07", "ATM"),
        ("Mozilla/5.0 (Windows NT 10.0) Chrome/130", "Net banking"),
        ("kiosk", "Unknown"),
    ],
)
def test_derive_channel(device, channel):
    assert derive_channel(device) == channel


@pytest.mark.parametrize(
    ("raw", "severity", "status"),
    [
        (None, "Low", "Logged"),
        ("CRITICAL", "Critical", "Requires review"),
        ("high", "High", "Requires review"),
        ("ERROR", "High", "Requires review"),
        ("WARNING", "Medium", "Requires review"),
        ("MEDIUM", "Medium", "Logged"),
        ("INFO", "Low", "Logged"),
        ("weird", "Low", "Logged"),
    ],
)
def test_derive_severity_and_status(raw, severity, status):
    assert derive_severity(raw) == severity
    assert derive_status(raw) == status


@pytest.mark.parametrize(
    ("raw", "label"),
    [
        (None, "Security event"),
        ("LOGIN_FAILED", "Login failed"),
        ("password_changed", "Password changed"),
        ("NEW_DEVICE_SEEN", "New device seen"),
    ],
)
def test_format_event_type(raw, label):
    assert format_event_type(raw) == label


@pytest.mark.parametrize(
    ("event_type", "metadata", "expected"),
    [
        ("LOGIN_SUCCESS", {}, "authenticated successfully"),
        ("LOGIN_FAILED", {"reason": "unknown_email", "email": "x@y.com"}, "unregistered email (x@y.com)"),
        ("LOGIN_FAILED", {"reason": "invalid_password"}, "invalid password"),
        ("LOGIN_FAILED", {"reason": "inactive_account"}, "account is inactive"),
        ("LOGIN_FAILED", {}, "authentication rejected"),
        ("HIGH_VALUE_TRANSFER", {"amount": "250000"}, "Amount: ₹250000"),
        ("HIGH_VALUE_TRANSFER", None, "flagged for monitoring"),
        ("TOKEN_REVOKED", {}, "Security event recorded: TOKEN_REVOKED"),
    ],
)
def test_format_description(event_type, metadata, expected):
    event = SimpleNamespace(event_type=event_type, event_metadata=metadata)

    assert expected in format_description(event)


# --- Tokens and masking --------------------------------------------------------


def test_mask_account_number():
    assert mask_account_number("123456789012") == "XXXX9012"
    assert mask_account_number(None) is None
    assert mask_account_number("") == ""


def test_token_without_role_is_rejected():
    token = jwt.encode({"sub": str(uuid4())}, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)

    with pytest.raises(ValueError):
        decode_access_token(token)


def test_token_signed_with_other_key_is_rejected():
    token = jwt.encode({"sub": str(uuid4()), "role": "ADMIN"}, "attacker-key", algorithm="HS256")

    with pytest.raises(ValueError):
        decode_access_token(token)
