"""
Subscription routes for Vyastha.

Handles plan activation and free-trial subscription creation.
Razorpay payment integration will be added separately.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from lib.auth import get_current_user
from lib.db import db
from lib import plans as plans_lib
from models.billing import Subscription


router = APIRouter(
    prefix="/subscriptions",
    tags=["subscriptions"],
)


class StartTrialRequest(BaseModel):
    plan_slug: str


@router.post("/start-trial")
async def start_trial(
    payload: StartTrialRequest,
    user: dict = Depends(get_current_user),
):
    """
    Start a free trial for the requested plan.

    Currently intended for the Vyastha Pro 3-day trial.
    Razorpay is not involved in this endpoint.
    """

    plan_slug = payload.plan_slug.strip().lower()

    if plan_slug != "pro":
        raise HTTPException(
            status_code=400,
            detail="Only Vyastha Pro trial can be started here.",
        )

    business_id = user.get("business_id")

    if not business_id:
        raise HTTPException(
            status_code=400,
            detail="Business account is not linked to this user.",
        )

    # Check the business's existing subscription.
    existing = await db.subscriptions.find_one(
        {"business_id": business_id}
    )

    if existing:
        existing_plan = str(
            existing.get("plan_slug", "free")
        ).strip().lower()

        trial_already_used = bool(
            existing.get("pro_trial_used", False)
        )

        # Any existing Pro subscription means the trial has already
        # been used, including older records without the new field.
        if existing_plan == "pro":
            trial_already_used = True

        if trial_already_used:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Vyastha Pro free trial has already been used. "
                    "Please purchase the Pro subscription to continue."
                ),
            )

        if existing_plan != "free":
            raise HTTPException(
                status_code=400,
                detail="Only the Free plan is eligible for the Pro trial.",
            )

    # Load the active Pro plan from MongoDB.
    pro_plan = await db.plans.find_one(
        {
            "slug": "pro",
            "active": True,
        }
    )

    if not pro_plan:
        raise HTTPException(
            status_code=404,
            detail="Vyastha Pro plan not found.",
        )

    now = datetime.now(timezone.utc)

    trial_days = int(
        pro_plan.get("trial_days", 3)
    )

    trial_end = now + timedelta(days=trial_days)

    amount = float(
        plans_lib.get_plan_price(
            "pro",
            "monthly",
        )
    )

    # Existing Vyastha subscription:
    # update the same subscription document.
    if existing:
        await db.subscriptions.update_one(
            {"id": existing["id"]},
            {
                "$set": {
                    "plan_id": str(pro_plan["id"]),
                    "plan_slug": "pro",
                    "billing_cycle": "monthly",
                    "status": "trialing",
                    "amount": amount,
                    "currency": "INR",
                    "trial_days": trial_days,
                    "current_period_start": now,
                    "current_period_end": trial_end,
                    "cancel_at_period_end": False,
                    "cancelled_at": None,
                    "pending_plan_slug": None,
                    "updated_at": now,
                    "pro_trial_used": True,
                }
            },
        )

        subscription_data = {
            "id": existing["id"],
            "user_id": existing["user_id"],
            "business_id": existing["business_id"],
            "plan_id": str(pro_plan["id"]),
            "plan_slug": "pro",
            "billing_cycle": "monthly",
            "status": "trialing",
            "amount": amount,
            "currency": "INR",
            "trial_days": trial_days,
            "current_period_start": now,
            "current_period_end": trial_end,
        }

    # No existing subscription:
    # create a new Pro trial subscription.
    else:
        subscription = Subscription(
            user_id=user["id"],
            business_id=business_id,
            plan_id=str(pro_plan["id"]),
            plan_slug="pro",
            billing_cycle="monthly",
            status="trialing",
            amount=amount,
            currency="INR",
            trial_days=trial_days,
            current_period_start=now,
            current_period_end=trial_end,
        )

        await db.subscriptions.insert_one(
            subscription.model_dump()
        )

        subscription_data = subscription.model_dump()

    return {
        "message": "Vyastha Pro trial started successfully.",
        "subscription": {
            "id": subscription_data["id"],
            "plan_slug": subscription_data["plan_slug"],
            "status": subscription_data["status"],
            "trial_days": subscription_data["trial_days"],
            "amount_after_trial": amount,
            "currency": subscription_data["currency"],
            "current_period_start": subscription_data[
                "current_period_start"
            ],
            "current_period_end": subscription_data[
                "current_period_end"
            ],
        },
    }