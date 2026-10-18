import pytest
from sqlalchemy import func, select

from app.intelligence.analytics.risk import recalculate_risk_profiles
from data.generators.generate import _delete_generated_data
from app.models.identity import Customer
from app.models.identity import User
from app.models.intelligence import CustomerRiskProfile


@pytest.mark.asyncio
async def test_recalculate_creates_one_profile_per_customer(session_factory, seed):
    async with session_factory() as db:
        count = await recalculate_risk_profiles(db)
        await db.commit()
        customer_count = await db.scalar(select(func.count()).select_from(Customer))
        profile_count = await db.scalar(
            select(func.count()).select_from(CustomerRiskProfile)
        )

    assert count == customer_count
    assert profile_count == customer_count


@pytest.mark.asyncio
async def test_recalculate_updates_without_duplicates(session_factory, seed):
    async with session_factory() as db:
        await recalculate_risk_profiles(db, [seed.customer.id])
        await db.commit()
        first = await db.scalar(
            select(CustomerRiskProfile).where(
                CustomerRiskProfile.customer_id == seed.customer.id
            )
        )
        first_id = first.id

        await recalculate_risk_profiles(db, [seed.customer.id])
        await db.commit()
        profiles = list(
            await db.scalars(
                select(CustomerRiskProfile).where(
                    CustomerRiskProfile.customer_id == seed.customer.id
                )
            )
        )

    assert len(profiles) == 1
    assert profiles[0].id == first_id
    assert profiles[0].last_calculated_at is not None


@pytest.mark.asyncio
async def test_reset_removes_generated_profiles(session_factory, seed):
    async with session_factory() as db:
        await recalculate_risk_profiles(db)
        await db.commit()
        customer_ids = list(await db.scalars(select(Customer.id)))
        user_ids = list(
            await db.scalars(
                select(User.id).where(User.id.in_(select(Customer.user_id)))
            )
        )
        await _delete_generated_data(db, customer_ids, user_ids)
        await db.commit()
        remaining = await db.scalar(
            select(func.count()).select_from(CustomerRiskProfile)
        )
        remaining_customers = await db.scalar(select(func.count()).select_from(Customer))

    assert remaining == 0
    assert remaining_customers == 0
