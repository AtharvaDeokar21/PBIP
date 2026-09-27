"""
Fraud scenario injector.

Injects five specific fraud scenarios into a small subset of customers.
Each injected row carries a ``fraud_scenario`` key in the metadata so
fraud-detection tests can verify the engine catches them.

Writes rows to:
  - transactions   (scenarios 1, 4, 5 – flagged with is_fraud=True)
  - behaviour_events (scenarios 2, 3 – suspicious login patterns)
  - fraud_events   (one FraudEvent per injected scenario)
  - fraud_alerts   (one FraudAlert per FraudEvent)

Scenario catalogue
------------------
SCENARIO_1 – LARGE_SINGLE_TRANSACTION
    A single debit that is 20-50× the customer's average transaction size.

SCENARIO_2 – IMPOSSIBLE_TRAVEL
    Two LOGIN events from different countries within 15 minutes.

SCENARIO_3 – BRUTE_FORCE_THEN_TRANSFER
    5 failed LOGIN attempts → 1 success → 1 large TRANSFER event,
    all within the same synthetic session.

SCENARIO_4 – HIGH_VELOCITY
    8-12 transactions spread across a 3-minute window.

SCENARIO_5 – MONTHLY_SPEND_SPIKE
    Monthly spending that jumps 5-8× the customer's trailing 3-month average.
    Implemented by injecting a dense cluster of large transactions in the
    current calendar month.
"""

from __future__ import annotations

import random
import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.banking import Transaction
from app.models.fraud import FraudAlert, FraudEvent
from app.models.intelligence import BehaviourEvent
from data.generators.config import FRAUD_CUSTOMER_FRACTION, SEED
from data.generators.customer_generator import CustomerRecord
from data.generators.transaction_generator import AccountRecord, TransactionRecord

# ---------------------------------------------------------------------------
# Severity / priority helpers
# ---------------------------------------------------------------------------

_SCENARIO_SEVERITY: dict[str, str] = {
    "SCENARIO_1": "HIGH",
    "SCENARIO_2": "CRITICAL",
    "SCENARIO_3": "CRITICAL",
    "SCENARIO_4": "HIGH",
    "SCENARIO_5": "MEDIUM",
}

_SCENARIO_PRIORITY: dict[str, int] = {
    # maps to FraudAlert.priority (1=CRITICAL, 2=HIGH, 3=MEDIUM, 4=LOW)
    "SCENARIO_1": 2,
    "SCENARIO_2": 1,
    "SCENARIO_3": 1,
    "SCENARIO_4": 2,
    "SCENARIO_5": 3,
}

_SCENARIO_RISK_SCORE: dict[str, float] = {
    "SCENARIO_1": 82.0,
    "SCENARIO_2": 95.0,
    "SCENARIO_3": 91.0,
    "SCENARIO_4": 78.0,
    "SCENARIO_5": 65.0,
}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_fraud_event(
    rng: random.Random,
    customer_id: uuid.UUID,
    transaction_id: uuid.UUID | None,
    scenario_key: str,
    description: str,
    extra_metadata: dict,
) -> FraudEvent:
    return FraudEvent(
        id=uuid.UUID(int=rng.getrandbits(128)),
        customer_id=customer_id,
        transaction_id=transaction_id,
        event_type=scenario_key,
        risk_score=Decimal(str(_SCENARIO_RISK_SCORE[scenario_key])),
        severity=_SCENARIO_SEVERITY[scenario_key],
        description=description,
        event_metadata={
            "fraud_scenario": scenario_key,
            **extra_metadata,
        },
        detected_at=datetime.now(timezone.utc),
    )


def _make_fraud_alert(
    rng: random.Random,
    fraud_event: FraudEvent,
) -> FraudAlert:
    return FraudAlert(
        id=uuid.UUID(int=rng.getrandbits(128)),
        fraud_event_id=fraud_event.id,
        customer_id=fraud_event.customer_id,
        status="OPEN",
        priority=_SCENARIO_PRIORITY[fraud_event.event_type],
    )


# ---------------------------------------------------------------------------
# Scenario injectors
# ---------------------------------------------------------------------------

def _inject_scenario_1(
    rng: random.Random,
    customer: CustomerRecord,
    txn_records: list[TransactionRecord],
    account_id: uuid.UUID,
) -> tuple[Transaction, FraudEvent, FraudAlert]:
    """LARGE_SINGLE_TRANSACTION – 20-50x average transaction size."""
    customer_txns = [t for t in txn_records if t.customer_id == customer.customer_id]
    avg_amount = (
        sum(t.amount for t in customer_txns) / len(customer_txns)
        if customer_txns
        else 5_000.0
    )
    multiplier = rng.uniform(20, 50)
    fraud_amount = round(avg_amount * multiplier, 2)

    txn_id = uuid.UUID(int=rng.getrandbits(128))
    txn_date = datetime.now(timezone.utc) - timedelta(days=rng.randint(1, 30))

    txn = Transaction(
        id=txn_id,
        account_id=account_id,
        transaction_reference=f"FRD{txn_id.hex[:12].upper()}",
        transaction_type="DEBIT",
        amount=Decimal(str(fraud_amount)),
        currency="INR",
        category="SHOPPING",
        description="FRAUD – Large single transaction",
        merchant_name="Unknown Merchant",
        merchant_category="SHOPPING",
        transaction_status="COMPLETED",
        transaction_date=txn_date,
        channel="CARD",
        is_fraud=True,
    )
    event = _make_fraud_event(
        rng, customer.customer_id, txn_id, "SCENARIO_1",
        f"Transaction amount ₹{fraud_amount:,.2f} is {multiplier:.1f}x the customer average ₹{avg_amount:,.2f}",
        {"fraud_amount": fraud_amount, "avg_amount": avg_amount, "multiplier": multiplier},
    )
    alert = _make_fraud_alert(rng, event)
    return txn, event, alert


def _inject_scenario_2(
    rng: random.Random,
    customer: CustomerRecord,
) -> tuple[list[BehaviourEvent], FraudEvent, FraudAlert]:
    """IMPOSSIBLE_TRAVEL – two LOGINs from different countries within 15 min."""
    base_time = datetime.now(timezone.utc) - timedelta(days=rng.randint(1, 60))
    second_time = base_time + timedelta(minutes=rng.randint(3, 14))
    session_id = uuid.UUID(int=rng.getrandbits(128))

    country_pairs = [
        ("India", "103.15.24.1", "Nigeria", "105.112.50.10"),
        ("India", "49.36.150.1", "Russia",  "5.62.18.20"),
        ("India", "117.239.1.1", "China",   "218.30.117.5"),
        ("India", "122.160.5.1", "Brazil",  "177.92.102.8"),
    ]
    c1_name, c1_ip, c2_name, c2_ip = rng.choice(country_pairs)

    events = [
        BehaviourEvent(
            id=uuid.UUID(int=rng.getrandbits(128)),
            customer_id=customer.customer_id,
            session_id=session_id,
            event_type="LOGIN",
            page="/login",
            action="SUBMIT",
            event_metadata={
                "fraud_scenario": "SCENARIO_2",
                "country": c1_name,
                "ip_address": c1_ip,
                "device_type": "MOBILE",
                "login_success": True,
            },
            ip_address=c1_ip,
            device_type="MOBILE",
            timestamp=base_time,
        ),
        BehaviourEvent(
            id=uuid.UUID(int=rng.getrandbits(128)),
            customer_id=customer.customer_id,
            session_id=uuid.UUID(int=rng.getrandbits(128)),  # different session
            event_type="LOGIN",
            page="/login",
            action="SUBMIT",
            event_metadata={
                "fraud_scenario": "SCENARIO_2",
                "country": c2_name,
                "ip_address": c2_ip,
                "device_type": "DESKTOP",
                "login_success": True,
                "minutes_since_previous_login": (second_time - base_time).seconds // 60,
            },
            ip_address=c2_ip,
            device_type="DESKTOP",
            timestamp=second_time,
        ),
    ]
    event = _make_fraud_event(
        rng, customer.customer_id, None, "SCENARIO_2",
        f"Login from {c1_name} ({c1_ip}) and {c2_name} ({c2_ip}) within "
        f"{(second_time - base_time).seconds // 60} minutes",
        {"country_1": c1_name, "ip_1": c1_ip, "country_2": c2_name, "ip_2": c2_ip,
         "minutes_gap": (second_time - base_time).seconds // 60},
    )
    alert = _make_fraud_alert(rng, event)
    return events, event, alert


def _inject_scenario_3(
    rng: random.Random,
    customer: CustomerRecord,
    account_id: uuid.UUID,
) -> tuple[list[BehaviourEvent], Transaction, FraudEvent, FraudAlert]:
    """BRUTE_FORCE_THEN_TRANSFER – 5 failed logins → success → large transfer."""
    base_time = datetime.now(timezone.utc) - timedelta(days=rng.randint(1, 30))
    session_id = uuid.UUID(int=rng.getrandbits(128))
    ip = f"185.{rng.randint(10,250)}.{rng.randint(10,250)}.{rng.randint(10,250)}"

    beh_events: list[BehaviourEvent] = []

    # 5 failed attempts
    for i in range(5):
        ts = base_time + timedelta(seconds=i * rng.randint(20, 60))
        beh_events.append(
            BehaviourEvent(
                id=uuid.UUID(int=rng.getrandbits(128)),
                customer_id=customer.customer_id,
                session_id=session_id,
                event_type="LOGIN",
                page="/login",
                action="SUBMIT",
                event_metadata={
                    "fraud_scenario": "SCENARIO_3",
                    "login_success": False,
                    "attempt_number": i + 1,
                    "ip_address": ip,
                },
                ip_address=ip,
                device_type="DESKTOP",
                timestamp=ts,
            )
        )

    # 1 successful login
    success_ts = base_time + timedelta(minutes=rng.randint(5, 15))
    beh_events.append(
        BehaviourEvent(
            id=uuid.UUID(int=rng.getrandbits(128)),
            customer_id=customer.customer_id,
            session_id=session_id,
            event_type="LOGIN",
            page="/login",
            action="SUBMIT",
            event_metadata={
                "fraud_scenario": "SCENARIO_3",
                "login_success": True,
                "ip_address": ip,
            },
            ip_address=ip,
            device_type="DESKTOP",
            timestamp=success_ts,
        )
    )

    # Large transfer transaction shortly after
    transfer_ts = success_ts + timedelta(minutes=rng.randint(2, 10))
    transfer_amount = round(customer.annual_income * rng.uniform(0.25, 0.75), 2)
    txn_id = uuid.UUID(int=rng.getrandbits(128))
    txn = Transaction(
        id=txn_id,
        account_id=account_id,
        transaction_reference=f"FRD{txn_id.hex[:12].upper()}",
        transaction_type="DEBIT",
        amount=Decimal(str(transfer_amount)),
        currency="INR",
        category="SHOPPING",
        description="FRAUD – Post brute-force transfer",
        merchant_name="Unknown Recipient",
        merchant_category="TRANSFER",
        transaction_status="COMPLETED",
        transaction_date=transfer_ts,
        channel="NETBANKING",
        is_fraud=True,
    )

    fraud_event = _make_fraud_event(
        rng, customer.customer_id, txn_id, "SCENARIO_3",
        f"5 failed logins followed by success and ₹{transfer_amount:,.2f} transfer within the same session",
        {"failed_attempts": 5, "transfer_amount": transfer_amount, "session_ip": ip},
    )
    alert = _make_fraud_alert(rng, fraud_event)
    return beh_events, txn, fraud_event, alert


def _inject_scenario_4(
    rng: random.Random,
    customer: CustomerRecord,
    account_id: uuid.UUID,
) -> tuple[list[Transaction], FraudEvent, FraudAlert]:
    """HIGH_VELOCITY – 8-12 transactions in a 3-minute window."""
    base_time = datetime.now(timezone.utc) - timedelta(days=rng.randint(1, 60))
    num_txns = rng.randint(8, 12)
    window_seconds = 180  # 3 minutes

    txns: list[Transaction] = []
    for i in range(num_txns):
        offset_secs = int(i * (window_seconds / num_txns)) + rng.randint(0, 5)
        ts = base_time + timedelta(seconds=offset_secs)
        txn_id = uuid.UUID(int=rng.getrandbits(128))
        amount = round(rng.uniform(500, 5_000), 2)
        txns.append(
            Transaction(
                id=txn_id,
                account_id=account_id,
                transaction_reference=f"VEL{txn_id.hex[:12].upper()}",
                transaction_type="DEBIT",
                amount=Decimal(str(amount)),
                currency="INR",
                category="SHOPPING",
                description="FRAUD – Velocity burst transaction",
                merchant_name="Rapid Pay",
                merchant_category="SHOPPING",
                transaction_status="COMPLETED",
                transaction_date=ts,
                channel="CARD",
                is_fraud=True,
            )
        )

    # Tag all txns' reference with scenario in description (metadata is on FraudEvent)
    fraud_event = _make_fraud_event(
        rng, customer.customer_id, txns[0].id, "SCENARIO_4",
        f"{num_txns} transactions within a 3-minute window",
        {"num_transactions": num_txns, "window_seconds": window_seconds,
         "transaction_ids": [str(t.id) for t in txns]},
    )
    alert = _make_fraud_alert(rng, fraud_event)
    return txns, fraud_event, alert


def _inject_scenario_5(
    rng: random.Random,
    customer: CustomerRecord,
    txn_records: list[TransactionRecord],
    account_id: uuid.UUID,
) -> tuple[list[Transaction], FraudEvent, FraudAlert]:
    """MONTHLY_SPEND_SPIKE – current month spending 5-8x trailing 3-month average."""
    now = datetime.now(timezone.utc)

    # Compute trailing 3-month average from existing txn_records
    three_months_ago = now - timedelta(days=90)
    current_month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    trailing = [
        t.amount for t in txn_records
        if t.customer_id == customer.customer_id
        and three_months_ago <= t.transaction_date < current_month_start
        and t.category not in ("SALARY", "INVESTMENT")
    ]
    trailing_avg = sum(trailing) / 3 if trailing else customer.annual_income / 12 * 0.5

    multiplier = rng.uniform(5, 8)
    spike_total = trailing_avg * multiplier
    num_spike_txns = rng.randint(8, 18)

    txns: list[Transaction] = []
    for _ in range(num_spike_txns):
        ts = current_month_start + timedelta(
            days=rng.randint(0, min(now.day - 1, 1)),
            hours=rng.randint(0, 23),
            minutes=rng.randint(0, 59),
        )
        amount = round(spike_total / num_spike_txns * rng.uniform(0.7, 1.3), 2)
        txn_id = uuid.UUID(int=rng.getrandbits(128))
        txns.append(
            Transaction(
                id=txn_id,
                account_id=account_id,
                transaction_reference=f"SPK{txn_id.hex[:12].upper()}",
                transaction_type="DEBIT",
                amount=Decimal(str(amount)),
                currency="INR",
                category="SHOPPING",
                description="FRAUD – Monthly spend spike transaction",
                merchant_name="Luxury Mart",
                merchant_category="SHOPPING",
                transaction_status="COMPLETED",
                transaction_date=ts,
                channel="CARD",
                is_fraud=True,
            )
        )

    fraud_event = _make_fraud_event(
        rng, customer.customer_id, txns[0].id, "SCENARIO_5",
        f"Monthly spend ₹{spike_total:,.2f} is {multiplier:.1f}x the trailing 3-month average ₹{trailing_avg:,.2f}",
        {
            "trailing_3month_avg": trailing_avg,
            "spike_total": spike_total,
            "multiplier": multiplier,
            "num_spike_txns": num_spike_txns,
            "transaction_ids": [str(t.id) for t in txns],
        },
    )
    alert = _make_fraud_alert(rng, fraud_event)
    return txns, fraud_event, alert


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

async def inject_fraud_scenarios(
    session: AsyncSession,
    customer_records: list[CustomerRecord],
    account_records: list[AccountRecord],
    txn_records: list[TransactionRecord],
    seed: int = SEED,
) -> None:
    """
    Select a small subset of customers and inject one scenario each.

    Distribution across 5 scenarios is round-robin so all scenarios are
    represented proportionally.
    """
    rng = random.Random(seed + 4)

    total_fraud_customers = max(5, int(len(customer_records) * FRAUD_CUSTOMER_FRACTION))
    fraud_customers = rng.sample(customer_records, k=total_fraud_customers)

    # Build a quick lookup: customer_id → list of account_ids
    cust_accounts: dict[uuid.UUID, list[uuid.UUID]] = {}
    for acc in account_records:
        cust_accounts.setdefault(acc.customer_id, []).append(acc.account_id)

    scenarios = ["SCENARIO_1", "SCENARIO_2", "SCENARIO_3", "SCENARIO_4", "SCENARIO_5"]
    all_txns: list[Transaction] = []
    all_beh: list[BehaviourEvent] = []
    all_events: list[FraudEvent] = []
    all_alerts: list[FraudAlert] = []

    for idx, customer in enumerate(fraud_customers):
        scenario = scenarios[idx % len(scenarios)]
        accs = cust_accounts.get(customer.customer_id, [])
        if not accs:
            continue
        account_id = accs[0]  # primary account

        if scenario == "SCENARIO_1":
            txn, ev, al = _inject_scenario_1(rng, customer, txn_records, account_id)
            all_txns.append(txn)
            all_events.append(ev)
            all_alerts.append(al)

        elif scenario == "SCENARIO_2":
            beh_evs, ev, al = _inject_scenario_2(rng, customer)
            all_beh.extend(beh_evs)
            all_events.append(ev)
            all_alerts.append(al)

        elif scenario == "SCENARIO_3":
            beh_evs, txn, ev, al = _inject_scenario_3(rng, customer, account_id)
            all_beh.extend(beh_evs)
            all_txns.append(txn)
            all_events.append(ev)
            all_alerts.append(al)

        elif scenario == "SCENARIO_4":
            txns, ev, al = _inject_scenario_4(rng, customer, account_id)
            all_txns.extend(txns)
            all_events.append(ev)
            all_alerts.append(al)

        elif scenario == "SCENARIO_5":
            txns, ev, al = _inject_scenario_5(rng, customer, txn_records, account_id)
            all_txns.extend(txns)
            all_events.append(ev)
            all_alerts.append(al)

    # Persist in dependency order
    if all_txns:
        session.add_all(all_txns)
        await session.flush()
    if all_beh:
        session.add_all(all_beh)
        await session.flush()
    if all_events:
        session.add_all(all_events)
        await session.flush()
    if all_alerts:
        session.add_all(all_alerts)
        await session.flush()

    print(
        f"  [fraud] injected {len(fraud_customers)} fraud customers | "
        f"{len(all_txns)} fraud txns | {len(all_beh)} fraud behaviour events | "
        f"{len(all_events)} fraud_events | {len(all_alerts)} fraud_alerts"
    )
    scenario_counts = {s: 0 for s in scenarios}
    for i, _ in enumerate(fraud_customers):
        scenario_counts[scenarios[i % len(scenarios)]] += 1
    for s, count in scenario_counts.items():
        print(f"    {s}: {count} customers")
