import random
import uuid
from decimal import Decimal
from datetime import datetime, timedelta, timezone


CATEGORIES = {
    "GROCERIES": [
        "DMart",
        "Reliance Fresh",
        "Nature's Basket",
    ],
    "DINING": [
        "Restaurant",
        "Swiggy",
        "Zomato",
    ],
    "TRANSPORT": [
        "Uber",
        "Ola",
        "Metro",
    ],
    "SHOPPING": [
        "Amazon",
        "Flipkart",
        "Myntra",
    ],
    "UTILITIES": [
        "Electricity",
        "Water",
        "Internet",
        "Mobile",
    ],
    "ENTERTAINMENT": [
        "Netflix",
        "Spotify",
        "BookMyShow",
    ],
    "TRAVEL": [
        "MakeMyTrip",
        "IndiGo",
        "IRCTC",
    ],
}


def generate_transaction(account_id, customer_profile=None):
    category = random.choice(list(CATEGORIES.keys()))
    merchant = random.choice(CATEGORIES[category])

    amount = Decimal(
        str(round(random.uniform(200, 15000), 2))
    )

    return {
        "id": uuid.uuid4(),
        "account_id": account_id,
        "transaction_reference": (
            f"TXN{uuid.uuid4().hex[:12].upper()}"
        ),
        "transaction_type": "DEBIT",
        "amount": amount,
        "currency": "INR",
        "category": category,
        "description": f"{category.title()} payment",
        "merchant_name": merchant,
        "merchant_category": category,
        "transaction_status": "COMPLETED",
        "transaction_date": (
            datetime.now(timezone.utc)
            - timedelta(days=random.randint(0, 365))
        ),
        "channel": random.choice(
            ["MOBILE", "WEB", "ATM", "CARD"]
        ),
        "is_fraud": False,
    }