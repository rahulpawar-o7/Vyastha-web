import asyncio
from datetime import datetime, timedelta, timezone

from lib.db import db


SUBSCRIPTION_ID = "b4fba37f-a298-4d2f-94b3-133b1f871ca2"


async def main():
    now = datetime.now(timezone.utc)
    new_end = now + timedelta(days=3)

    result = await db.subscriptions.update_one(
        {"id": SUBSCRIPTION_ID},
        {
            "$set": {
                "status": "trialing",
                "current_period_start": now,
                "current_period_end": new_end,
                "amount": 99.0,
                "billing_cycle": "monthly",
                "cancel_at_period_end": False,
                "cancelled_at": None,
                "updated_at": now,
            }
        },
    )

    print("Matched:", result.matched_count)
    print("Modified:", result.modified_count)

    if result.modified_count == 1:
        print("\nPro trial reset successfully.")
        print("Start:", now)
        print("End  :", new_end)
    else:
        print("\nSubscription was not updated.")


if __name__ == "__main__":
    asyncio.run(main())