"""
Behaviour event generator.

Writes rows to:
  - behaviour_events

Generates realistic login, page_view, and session events with device/location
fields correlated to the customer's segment and city.
"""

from __future__ import annotations

import random
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.intelligence import BehaviourEvent
from data.generators.config import BEHAVIOUR_EVENTS_PER_CUSTOMER, HISTORY_DAYS, SEED
from data.generators.customer_generator import CustomerRecord

# ---------------------------------------------------------------------------
# Lookup tables
# ---------------------------------------------------------------------------

DEVICE_TYPES: dict[str, list[str]] = {
    "MASS_MARKET":    ["ANDROID", "ANDROID", "ANDROID", "DESKTOP"],
    "MASS_AFFLUENT":  ["ANDROID", "IOS", "DESKTOP", "ANDROID"],
    "AFFLUENT":       ["IOS", "ANDROID", "DESKTOP", "IOS"],
    "HIGH_NET_WORTH": ["IOS", "IOS", "DESKTOP", "TABLET"],
}

PAGES: list[str] = [
    "/dashboard", "/accounts", "/transactions", "/transfers",
    "/loans", "/investments", "/profile", "/settings",
    "/bill-payments", "/support", "/notifications",
]

PAGE_WEIGHTS: dict[str, list[float]] = {
    "MASS_MARKET":    [0.25, 0.20, 0.20, 0.10, 0.05, 0.02, 0.05, 0.03, 0.05, 0.03, 0.02],
    "MASS_AFFLUENT":  [0.20, 0.15, 0.18, 0.12, 0.08, 0.08, 0.05, 0.04, 0.04, 0.03, 0.03],
    "AFFLUENT":       [0.18, 0.12, 0.15, 0.10, 0.10, 0.15, 0.05, 0.05, 0.04, 0.03, 0.03],
    "HIGH_NET_WORTH": [0.15, 0.10, 0.10, 0.08, 0.08, 0.22, 0.06, 0.06, 0.04, 0.05, 0.06],
}

ACTIONS: list[str] = [
    "VIEW", "CLICK", "SCROLL", "SUBMIT", "DOWNLOAD", "SEARCH",
]

EVENT_TYPES: list[str] = ["LOGIN", "PAGE_VIEW", "SESSION_START", "SESSION_END", "LOGOUT"]
EVENT_WEIGHTS: list[float] = [0.10, 0.60, 0.10, 0.10, 0.10]

# IP address prefixes by city (simulated)
CITY_IP_PREFIX: dict[str, str] = {
    "Mumbai":      "103.15",
    "Delhi":       "122.160",
    "Bengaluru":   "49.36",
    "Hyderabad":   "115.240",
    "Chennai":     "117.239",
    "Kolkata":     "103.21",
    "Pune":        "49.204",
    "Ahmedabad":   "122.170",
    "Jaipur":      "117.197",
    "Lucknow":     "103.59",
    "Kochi":       "43.241",
    "Chandigarh":  "117.201",
    "Indore":      "103.47",
    "Nagpur":      "49.37",
    "Bhopal":      "122.175",
}


def _fake_ip(city: str, rng: random.Random) -> str:
    prefix = CITY_IP_PREFIX.get(city, "192.168")
    return f"{prefix}.{rng.randint(0, 255)}.{rng.randint(1, 254)}"


async def generate_behaviour_events(
    session: AsyncSession,
    customer_records: list[CustomerRecord],
    seed: int = SEED,
) -> None:
    """
    Generate behaviour events for all customers and flush to the DB.
    """
    rng = random.Random(seed + 2)
    now = datetime.now(timezone.utc)

    events: list[BehaviourEvent] = []

    for cust in customer_records:
        # Group events into sessions (2–5 events per session)
        events_left = BEHAVIOUR_EVENTS_PER_CUSTOMER
        while events_left > 0:
            session_id = uuid.UUID(int=rng.getrandbits(128))
            device = rng.choice(DEVICE_TYPES[cust.segment])
            ip = _fake_ip(cust.city, rng)

            # Session start time
            session_start = now - timedelta(
                days=rng.randint(0, HISTORY_DAYS),
                hours=rng.randint(0, 23),
                minutes=rng.randint(0, 59),
            )

            session_size = rng.randint(min(2, events_left), min(5, events_left))
            for offset in range(session_size):
                ts = session_start + timedelta(minutes=offset * rng.randint(1, 8))
                event_type = rng.choices(EVENT_TYPES, weights=EVENT_WEIGHTS, k=1)[0]
                page = rng.choices(PAGES, weights=PAGE_WEIGHTS[cust.segment], k=1)[0]
                action = rng.choice(ACTIONS)

                event = BehaviourEvent(
                    id=uuid.UUID(int=rng.getrandbits(128)),
                    customer_id=cust.customer_id,
                    session_id=session_id,
                    event_type=event_type,
                    page=page,
                    action=action,
                    event_metadata={
                        "device_type": device,
                        "location": cust.city,
                        "ip_address": ip,
                        "session_offset_minutes": offset,
                    },
                    ip_address=ip,
                    device_type=device,
                    timestamp=ts,
                )
                events.append(event)

            events_left -= session_size

    session.add_all(events)
    await session.flush()

    print(f"  [behaviour] inserted {len(events)} behaviour_events")
