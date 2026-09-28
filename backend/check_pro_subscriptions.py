import asyncio
from lib.db import db


async def main():
    subscriptions = await db.subscriptions.find(
        {"plan_slug": "pro"},
        {
            "_id": 0,
            "id": 1,
            "user_id": 1,
            "business_id": 1,
            "plan_slug": 1,
            "status": 1,
            "billing_cycle": 1,
            "amount": 1,
            "current_period_start": 1,
            "current_period_end": 1,
            "created_at": 1,
            "updated_at": 1,
        }
    ).sort("created_at", -1).to_list(100)

    print("\n=== PRO SUBSCRIPTIONS ===")

    if not subscriptions:
        print("No Pro subscriptions found.")
        return

    for i, sub in enumerate(subscriptions, 1):
        print(f"\n[{i}]")
        print(f"subscription_id : {sub.get('id')}")
        print(f"user_id         : {sub.get('user_id')}")
        print(f"business_id     : {sub.get('business_id')}")
        print(f"status          : {sub.get('status')}")
        print(f"billing_cycle   : {sub.get('billing_cycle')}")
        print(f"amount          : {sub.get('amount')}")
        print(f"period_start    : {sub.get('current_period_start')}")
        print(f"period_end      : {sub.get('current_period_end')}")
        print(f"created_at      : {sub.get('created_at')}")


if __name__ == "__main__":
    asyncio.run(main())