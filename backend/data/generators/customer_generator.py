"""
Customer (+ User) generator.

Writes rows to:
  - users
  - customers

Each generated customer gets a deterministically seeded User account so the
rest of the pipeline can reference customer_id / user_id foreign keys.
"""

from __future__ import annotations

import random
import uuid
from datetime import date, datetime, timezone

from faker import Faker
from passlib.hash import bcrypt
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.identity import Customer, User
from data.generators.config import (
    HISTORY_DAYS,
    INCOME_BANDS,
    NUM_CUSTOMERS,
    SEED,
    SEGMENT_WEIGHTS,
)

# ---------------------------------------------------------------------------
# Lookup tables
# ---------------------------------------------------------------------------

OCCUPATIONS: dict[str, list[str]] = {
    "MASS_MARKET": [
        "Shop Assistant", "Factory Worker", "Delivery Driver", "Security Guard",
        "Housekeeping Staff", "Data Entry Operator", "Auto Driver",
    ],
    "MASS_AFFLUENT": [
        "School Teacher", "Junior Software Engineer", "Accountant",
        "Bank Clerk", "Nurse", "Sales Executive", "HR Executive",
    ],
    "AFFLUENT": [
        "Senior Software Engineer", "Product Manager", "Marketing Manager",
        "Chartered Accountant", "Architect", "Doctor", "Lawyer",
    ],
    "HIGH_NET_WORTH": [
        "Business Owner", "CTO", "Managing Director", "Investment Banker",
        "Surgeon", "Venture Capitalist", "CFO",
    ],
}

EMPLOYMENT_TYPES: dict[str, list[str]] = {
    "MASS_MARKET":    ["FULL_TIME", "PART_TIME", "CONTRACT"],
    "MASS_AFFLUENT":  ["FULL_TIME", "CONTRACT", "SELF_EMPLOYED"],
    "AFFLUENT":       ["FULL_TIME", "SELF_EMPLOYED"],
    "HIGH_NET_WORTH": ["SELF_EMPLOYED", "FULL_TIME"],
}

RISK_PROFILES: dict[str, list[str]] = {
    "MASS_MARKET":    ["LOW", "LOW", "MODERATE"],
    "MASS_AFFLUENT":  ["LOW", "MODERATE", "MODERATE"],
    "AFFLUENT":       ["MODERATE", "MODERATE", "HIGH"],
    "HIGH_NET_WORTH": ["MODERATE", "HIGH", "HIGH"],
}

INDIAN_CITIES: list[str] = [
    "Mumbai", "Delhi", "Bengaluru", "Hyderabad", "Chennai",
    "Kolkata", "Pune", "Ahmedabad", "Jaipur", "Lucknow",
    "Kochi", "Chandigarh", "Indore", "Nagpur", "Bhopal",
]

INDIAN_STATES: dict[str, str] = {
    "Mumbai": "Maharashtra", "Delhi": "Delhi", "Bengaluru": "Karnataka",
    "Hyderabad": "Telangana", "Chennai": "Tamil Nadu", "Kolkata": "West Bengal",
    "Pune": "Maharashtra", "Ahmedabad": "Gujarat", "Jaipur": "Rajasthan",
    "Lucknow": "Uttar Pradesh", "Kochi": "Kerala", "Chandigarh": "Punjab",
    "Indore": "Madhya Pradesh", "Nagpur": "Maharashtra", "Bhopal": "Madhya Pradesh",
}

# ---------------------------------------------------------------------------
# Segmentation helper
# ---------------------------------------------------------------------------

def _pick_segment(rng: random.Random) -> str:
    segments = list(SEGMENT_WEIGHTS.keys())
    weights = list(SEGMENT_WEIGHTS.values())
    return rng.choices(segments, weights=weights, k=1)[0]


def _compute_segment(annual_income: float, total_balance: float, investment: float) -> str:
    """
    Derive a customer segment from financial metrics.

    Score formula (documented in config.py):
        score = income/1_000_000 + balance/500_000 + investment/2_000_000
    """
    score = (
        annual_income / 1_000_000
        + total_balance / 500_000
        + investment / 2_000_000
    )
    if score < 1.5:
        return "MASS_MARKET"
    if score < 4.0:
        return "MASS_AFFLUENT"
    if score < 10.0:
        return "AFFLUENT"
    return "HIGH_NET_WORTH"


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

class CustomerRecord:
    """Lightweight in-memory representation shared across generators."""

    __slots__ = (
        "user_id", "customer_id", "segment", "annual_income",
        "risk_profile", "city", "occupation", "first_name", "last_name",
    )

    def __init__(
        self,
        user_id: uuid.UUID,
        customer_id: uuid.UUID,
        segment: str,
        annual_income: float,
        risk_profile: str,
        city: str,
        occupation: str,
        first_name: str,
        last_name: str,
    ) -> None:
        self.user_id = user_id
        self.customer_id = customer_id
        self.segment = segment
        self.annual_income = annual_income
        self.risk_profile = risk_profile
        self.city = city
        self.occupation = occupation
        self.first_name = first_name
        self.last_name = last_name


async def generate_customers(
    session: AsyncSession,
    num_customers: int = NUM_CUSTOMERS,
    seed: int = SEED,
) -> list[CustomerRecord]:
    """
    Generate `num_customers` User + Customer rows and flush them to the DB.

    Returns a list of :class:`CustomerRecord` objects used by downstream generators.
    """
    rng = random.Random(seed)
    fake = Faker("en_IN")
    fake.seed_instance(seed)

    # Pre-hash a single dummy password once (expensive bcrypt call)
    _hashed_pw = bcrypt.hash("Password@123")

    records: list[CustomerRecord] = []
    users: list[User] = []
    customers: list[Customer] = []

    for i in range(num_customers):
        segment = _pick_segment(rng)
        income_min, income_max = INCOME_BANDS[segment]
        annual_income = round(rng.uniform(income_min, income_max), 2)

        occupation = rng.choice(OCCUPATIONS[segment])
        employment_type = rng.choice(EMPLOYMENT_TYPES[segment])
        risk_profile = rng.choice(RISK_PROFILES[segment])
        city = rng.choice(INDIAN_CITIES)
        state = INDIAN_STATES[city]

        dob_year = rng.randint(1960, 2000)
        dob = date(dob_year, rng.randint(1, 12), rng.randint(1, 28))

        first_name = fake.first_name()
        last_name = fake.last_name()
        email = (
            f"{first_name.lower()}.{last_name.lower()}"
            f"{rng.randint(10, 999)}@example.com"
        )

        user_id = uuid.UUID(int=rng.getrandbits(128))
        customer_id = uuid.UUID(int=rng.getrandbits(128))

        # Placeholder balance/investment for segmentation – accounts generator
        # will set real balances; we use income-correlated estimates here.
        estimated_balance = annual_income * rng.uniform(0.05, 0.30)
        estimated_investment = annual_income * rng.uniform(0.0, 0.50)
        derived_segment = _compute_segment(annual_income, estimated_balance, estimated_investment)

        user = User(
            id=user_id,
            email=email,
            password_hash=_hashed_pw,
            role="CUSTOMER",
            is_active=True,
            mfa_enabled=False,
            last_login_at=datetime.now(timezone.utc),
        )

        customer = Customer(
            id=customer_id,
            user_id=user_id,
            customer_number=f"CUST{str(i + 1).zfill(6)}",
            first_name=first_name,
            last_name=last_name,
            date_of_birth=dob,
            phone=fake.phone_number()[:30],
            address=fake.address()[:200],
            city=city,
            state=state,
            postal_code=fake.postcode()[:20],
            occupation=occupation,
            employment_type=employment_type,
            annual_income=annual_income,
            risk_profile=risk_profile,
            customer_segment=derived_segment,
        )

        users.append(user)
        customers.append(customer)
        records.append(
            CustomerRecord(
                user_id=user_id,
                customer_id=customer_id,
                segment=derived_segment,
                annual_income=annual_income,
                risk_profile=risk_profile,
                city=city,
                occupation=occupation,
                first_name=first_name,
                last_name=last_name,
            )
        )

    session.add_all(users)
    await session.flush()
    session.add_all(customers)
    await session.flush()

    print(f"  [customers] inserted {len(users)} users + {len(customers)} customers")
    return records
