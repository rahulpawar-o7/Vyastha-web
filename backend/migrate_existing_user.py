import asyncio
import sys
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from dotenv import load_dotenv

from lib.db import db, ensure_indexes


load_dotenv()


TRIAL_DAYS = 90
FREE_PLAN_SLUG = "free"


def now_utc():
    return datetime.now(timezone.utc)


async def migrate_existing_users():
    await ensure_indexes()

    print("\n========================================")
    print(" VYASTHA EXISTING USER MIGRATION")
    print("========================================\n")

    users = await db.users.find(
        {"role": "business_owner"}
    ).to_list(length=None)

    print(f"Business owners found: {len(users)}\n")

    migrated = 0
    skipped = 0
    errors = 0

    for user in users:
        email = user.get("email", "")
        user_id = user.get("id")

        print("----------------------------------------")
        print(email)
        print(f"User ID: {user_id}")

        try:
            # --------------------------------------------------
            # 1. Check existing business link
            # --------------------------------------------------
            existing_business_id = user.get("business_id")

            if existing_business_id:
                existing_business = await db.businesses.find_one(
                    {"id": existing_business_id}
                )

                if existing_business:
                    existing_subscription = await db.subscriptions.find_one(
                        {"business_id": existing_business_id}
                    )

                    if existing_subscription:
                        print(
                            f"Already migrated / configured."
                        )
                        print(
                            f"Business: {existing_business_id}"
                        )
                        print(
                            f"Subscription: "
                            f"{existing_subscription.get('plan_slug')} / "
                            f"{existing_subscription.get('status')}"
                        )

                        skipped += 1
                        continue

            # --------------------------------------------------
            # 2. Find company profile
            # --------------------------------------------------
            profile = await db.company_profiles.find_one(
                {"user_id": user_id}
            )

            if not profile:
                print(
                    "ERROR: Company profile not found."
                )
                errors += 1
                continue

            company_name = (
                profile.get("company_name")
                or user.get("company_name")
                or "My Business"
            )

            print(
                f"Company: {company_name}"
            )

            # --------------------------------------------------
            # 3. Create business
            # --------------------------------------------------
            business_id = str(uuid4())

            business_doc = {
                "id": business_id,
                "owner_user_id": user_id,
                "name": company_name,
                "company_name": company_name,
                "email": profile.get(
                    "email",
                    email,
                ),
                "phone": profile.get(
                    "phone"
                ),
                "created_at": now_utc(),
                "updated_at": now_utc(),
            }

            await db.businesses.insert_one(
                business_doc
            )

            print(
                f"Created business: {business_id}"
            )

            # --------------------------------------------------
            # 4. Link user -> business
            # --------------------------------------------------
            await db.users.update_one(
                {"_id": user["_id"]},
                {
                    "$set": {
                        "business_id": business_id,
                    }
                },
            )

            print(
                "Linked user.business_id"
            )

            # --------------------------------------------------
            # 5. Create 90-day Free Trial
            # --------------------------------------------------
            trial_start = now_utc()
            trial_end = (
                trial_start
                + timedelta(days=TRIAL_DAYS)
            )

            subscription_id = str(uuid4())

            subscription_doc = {
                "id": subscription_id,
                "user_id": user_id,
                "business_id": business_id,

                "plan_id": FREE_PLAN_SLUG,
                "plan_slug": FREE_PLAN_SLUG,

                "billing_cycle": "monthly",

                "status": "trialing",

                "amount": 49,
                "currency": "INR",

                "trial_days": TRIAL_DAYS,

                "current_period_start": trial_start,
                "current_period_end": trial_end,

                "cancel_at_period_end": False,

                "razorpay_customer_id": None,
                "razorpay_subscription_id": None,
                "razorpay_plan_id": None,

                "pending_plan_slug": None,

                "created_at": trial_start,
                "updated_at": trial_start,
            }

            await db.subscriptions.insert_one(
                subscription_doc
            )

            print(
                "Created Vyastha subscription"
            )

            print(
                f"Trial: {TRIAL_DAYS} days"
            )

            print(
                f"Start: {trial_start}"
            )

            print(
                f"End:   {trial_end}"
            )

            migrated += 1

        except Exception as exc:
            print(
                f"ERROR while migrating {email}:"
            )
            print(str(exc))

            errors += 1

    print("\n========================================")
    print(" MIGRATION SUMMARY")
    print("========================================")
    print(
        f"Business owners: {len(users)}"
    )
    print(
        f"Migrated:        {migrated}"
    )
    print(
        f"Skipped:         {skipped}"
    )
    print(
        f"Errors:          {errors}"
    )
    print("========================================\n")


if __name__ == "__main__":
    try:
        asyncio.run(
            migrate_existing_users()
        )
    except KeyboardInterrupt:
        print("\nMigration cancelled.")
        sys.exit(1)