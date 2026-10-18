"""Compliance service layer for generating and querying read-only compliance exceptions."""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from typing import Optional
from uuid import UUID

from sqlalchemy import Date, cast, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.banking import Account, Transaction
from app.models.identity import Customer
from app.schemas.compliance import (
    ComplianceAlertItemResponse,
    ComplianceAlertListResponse,
    ComplianceSummaryResponse,
)
from app.services.common import utcnow


class ComplianceService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_alerts(
        self,
        *,
        category: Optional[str] = None,
        severity: Optional[str] = None,
        status: Optional[str] = None,
        search: Optional[str] = None,
        page: int = 1,
        page_size: int = 10,
        as_of: Optional[datetime | date] = None,
    ) -> ComplianceAlertListResponse:
        # Documented reference timestamp for consistent calculations across the request
        if as_of is not None and not isinstance(as_of, datetime):
            as_of = datetime.combine(as_of, datetime.max.time(), tzinfo=timezone.utc)
        ref_time = as_of or utcnow()
        window_start = ref_time - timedelta(days=30)

        raw_alerts: list[ComplianceAlertItemResponse] = []

        # -------------------------------------------------------------------
        # Rule 1: Reporting — High-value completed transaction review
        # -------------------------------------------------------------------
        high_value_stmt = (
            select(Transaction, Customer)
            .join(Account, Account.id == Transaction.account_id)
            .join(Customer, Customer.id == Account.customer_id)
            .where(
                Transaction.amount >= Decimal("1000000.00"),
                Transaction.transaction_status == "COMPLETED",
            )
        )
        high_value_rows = (await self.db.execute(high_value_stmt)).all()

        for txn, customer in high_value_rows:
            txn_dt = txn.transaction_date
            # Deterministic regulatory calendar formula: 15th of following month
            next_month = 1 if txn_dt.month == 12 else txn_dt.month + 1
            next_year = txn_dt.year + 1 if txn_dt.month == 12 else txn_dt.year
            due_date_str = f"{next_year:04d}-{next_month:02d}-15"

            amt_val = float(txn.amount)
            alert_sev = "High" if amt_val >= 2500000.0 else "Medium"

            raw_alerts.append(
                ComplianceAlertItemResponse(
                    id=f"CA-REP-{str(txn.id).upper()}",
                    customer_id=str(customer.id),
                    customer_name=f"{customer.first_name} {customer.last_name}".strip(),
                    type="Threshold reporting review",
                    category="Reporting",
                    severity=alert_sev,
                    status="Open",
                    due_date=due_date_str,
                    raised_at=txn.transaction_date,
                    description=(
                        f"Completed transaction of ₹{amt_val:,.2f} on "
                        f"{txn_dt.strftime('%Y-%m-%d')} reached the ₹10,00,000 prototype review threshold."
                    ),
                    assigned_to="Compliance Team",
                )
            )

        # -------------------------------------------------------------------
        # Rule 2: Transaction — Transaction velocity review
        # -------------------------------------------------------------------
        velocity_stmt = (
            select(
                Account.customer_id,
                Customer.first_name,
                Customer.last_name,
                func.date(Transaction.transaction_date).label("txn_day"),
                func.count(Transaction.id).label("txn_count"),
                func.max(Transaction.transaction_date).label("latest_txn_time"),
            )
            .join(Account, Account.id == Transaction.account_id)
            .join(Customer, Customer.id == Account.customer_id)
            .where(Transaction.transaction_status == "COMPLETED")
            .group_by(
                Account.customer_id,
                Customer.first_name,
                Customer.last_name,
                func.date(Transaction.transaction_date),
            )
            .having(func.count(Transaction.id) >= 6)
        )
        velocity_rows = (await self.db.execute(velocity_stmt)).all()

        for c_id, f_name, l_name, txn_day, count, latest_time in velocity_rows:
            # Normalize date string
            day_str = str(txn_day)
            date_digits = day_str.replace("-", "")
            try:
                parsed_day = date.fromisoformat(day_str)
                due_date_str = (parsed_day + timedelta(days=7)).isoformat()
            except ValueError:
                due_date_str = day_str

            raised_time = latest_time or datetime.combine(
                parsed_day, datetime.min.time(), tzinfo=timezone.utc
            )

            raw_alerts.append(
                ComplianceAlertItemResponse(
                    id=f"CA-TXN-{str(c_id).upper()}-{date_digits}",
                    customer_id=str(c_id),
                    customer_name=f"{f_name} {l_name}".strip(),
                    type="Transaction velocity review",
                    category="Transaction",
                    severity="High" if count >= 10 else "Medium",
                    status="Open",
                    due_date=due_date_str,
                    raised_at=raised_time,
                    description=(
                        f"Operational velocity threshold reached: {count} completed "
                        f"transactions recorded on {day_str}."
                    ),
                    assigned_to="Compliance Team",
                )
            )

        # -------------------------------------------------------------------
        # Rule 3: KYC — Income-to-transaction-volume review
        # -------------------------------------------------------------------
        kyc_stmt = (
            select(
                Customer.id.label("customer_id"),
                Customer.first_name,
                Customer.last_name,
                Customer.annual_income,
                func.sum(Transaction.amount).label("debit_volume"),
                func.max(Transaction.transaction_date).label("latest_debit_date"),
            )
            .join(Account, Account.customer_id == Customer.id)
            .join(Transaction, Transaction.account_id == Account.id)
            .where(
                Customer.annual_income.is_not(None),
                Customer.annual_income > 0,
                Transaction.transaction_status == "COMPLETED",
                Transaction.transaction_type == "DEBIT",
                Transaction.transaction_date >= window_start,
                Transaction.transaction_date <= ref_time,
            )
            .group_by(
                Customer.id,
                Customer.first_name,
                Customer.last_name,
                Customer.annual_income,
            )
        )
        kyc_rows = (await self.db.execute(kyc_stmt)).all()

        for c_id, f_name, l_name, annual_inc, deb_vol, latest_date in kyc_rows:
            annual_val = float(annual_inc)
            monthly_val = annual_val / 12.0
            volume_val = float(deb_vol or 0)
            threshold = 3.0 * monthly_val

            if volume_val > threshold:
                raised_time = latest_date or ref_time
                due_date_str = (raised_time.date() + timedelta(days=14)).isoformat()
                alert_sev = "Medium" if volume_val >= 5.0 * monthly_val else "Low"

                raw_alerts.append(
                    ComplianceAlertItemResponse(
                        id=f"CA-KYC-{str(c_id).upper()}",
                        customer_id=str(c_id),
                        customer_name=f"{f_name} {l_name}".strip(),
                        type="Income-to-volume review",
                        category="KYC",
                        severity=alert_sev,
                        status="Open",
                        due_date=due_date_str,
                        raised_at=raised_time,
                        description=(
                            f"Trailing 30-day debit volume of ₹{volume_val:,.2f} exceeds "
                            f"3x declared monthly income (₹{monthly_val:,.2f})."
                        ),
                        assigned_to="Compliance Team",
                    )
                )

        # -------------------------------------------------------------------
        # Rule 4: Documentation — Profile completeness review
        # -------------------------------------------------------------------
        active_customers_stmt = (
            select(Customer)
            .join(Account, Account.customer_id == Customer.id)
            .where(Account.status == "ACTIVE")
            .distinct()
        )
        active_customers = (await self.db.scalars(active_customers_stmt)).all()

        for cust in active_customers:
            missing_fields: list[str] = []
            if not cust.phone or not cust.phone.strip():
                missing_fields.append("phone number")
            if not cust.address or not cust.address.strip():
                missing_fields.append("residential address")
            if not cust.occupation or not cust.occupation.strip():
                missing_fields.append("occupation")
            if not cust.employment_type or not cust.employment_type.strip():
                missing_fields.append("employment type")
            if not cust.date_of_birth:
                missing_fields.append("date of birth")

            if missing_fields:
                raised_time = cust.created_at
                due_date_str = (cust.created_at.date() + timedelta(days=30)).isoformat()

                raw_alerts.append(
                    ComplianceAlertItemResponse(
                        id=f"CA-DOC-{str(cust.id).upper()}",
                        customer_id=str(cust.id),
                        customer_name=f"{cust.first_name} {cust.last_name}".strip(),
                        type="Profile documentation review",
                        category="Documentation",
                        severity="Medium",
                        status="Open",
                        due_date=due_date_str,
                        raised_at=raised_time,
                        description=(
                            f"Active account holder has incomplete profile records: missing "
                            f"{', '.join(missing_fields)}."
                        ),
                        assigned_to="Compliance Team",
                    )
                )

        # Deduplicate alerts by alert ID to prevent accidental duplication
        unique_alerts_map: dict[str, ComplianceAlertItemResponse] = {}
        for alert in raw_alerts:
            if alert.id not in unique_alerts_map:
                unique_alerts_map[alert.id] = alert
        all_alerts = list(unique_alerts_map.values())

        # -------------------------------------------------------------------
        # Summary metrics (calculated over the complete dataset)
        # -------------------------------------------------------------------
        open_count = sum(1 for a in all_alerts if a.status == "Open")
        critical_count = sum(1 for a in all_alerts if a.severity == "Critical")
        resolved_count = sum(1 for a in all_alerts if a.status == "Resolved")
        category_counts: dict[str, int] = {
            "KYC": sum(1 for a in all_alerts if a.category == "KYC"),
            "AML": 0,  # Explicitly unsupported, honest count
            "Reporting": sum(1 for a in all_alerts if a.category == "Reporting"),
            "Documentation": sum(1 for a in all_alerts if a.category == "Documentation"),
            "Transaction": sum(1 for a in all_alerts if a.category == "Transaction"),
        }

        summary = ComplianceSummaryResponse(
            open_count=open_count,
            critical_count=critical_count,
            resolved_count=resolved_count,
            category_counts=category_counts,
        )

        # -------------------------------------------------------------------
        # Server-side Filtering for pagination
        # -------------------------------------------------------------------
        filtered = all_alerts

        if category and category.lower() != "all":
            norm_cat = category.strip().lower()
            filtered = [a for a in filtered if a.category.lower() == norm_cat]

        if severity and severity.lower() != "all":
            norm_sev = severity.strip().lower()
            filtered = [a for a in filtered if a.severity.lower() == norm_sev]

        if status and status.lower() != "all":
            norm_status = status.strip().lower()
            filtered = [a for a in filtered if a.status.lower() == norm_status]

        if search and search.strip():
            term = search.strip().lower()
            filtered = [
                a
                for a in filtered
                if term in a.id.lower()
                or term in a.customer_name.lower()
                or term in a.customer_id.lower()
                or term in a.type.lower()
                or term in a.description.lower()
            ]

        # Deterministic sorting: latest raised_at first, secondary tie-break by ID
        filtered.sort(key=lambda a: (-a.raised_at.timestamp(), a.id))

        total = len(filtered)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        items = filtered[start_idx:end_idx]

        return ComplianceAlertListResponse(
            total=total,
            page=page,
            page_size=page_size,
            items=items,
            summary=summary,
        )
