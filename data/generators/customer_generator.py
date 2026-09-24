import random
import uuid
from decimal import Decimal

from faker import Faker

fake = Faker("en_IN")


RISK_PROFILES = [
    "LOW",
    "MODERATE",
    "HIGH",
]

SEGMENTS = [
    "STUDENT",
    "YOUNG_PROFESSIONAL",
    "MASS_MARKET",
    "MASS_AFFLUENT",
    "PREMIUM",
]


def generate_customer():
    return {
        "id": uuid.uuid4(),
        "customer_number": f"CUST{uuid.uuid4().hex[:10].upper()}",
        "first_name": fake.first_name(),
        "last_name": fake.last_name(),
        "phone": fake.phone_number(),
        "city": fake.city(),
        "state": fake.state(),
        "occupation": fake.job(),
        "employment_type": random.choice(
            ["FULL_TIME", "PART_TIME", "SELF_EMPLOYED"]
        ),
        "annual_income": Decimal(
            str(random.randint(300000, 5000000))
        ),
        "risk_profile": random.choice(RISK_PROFILES),
        "customer_segment": random.choice(SEGMENTS),
    }