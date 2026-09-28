import asyncio

from lib.db import db


async def main():
    print("\n=== PAYMENT DUE MANAGEMENT FEATURE ===")

    for slug in ["free", "pro"]:
        plan = await db.plans.find_one(
            {"slug": slug},
            {"_id": 0, "slug": 1, "name": 1, "features": 1}
        )

        print(f"\nPLAN: {slug}")

        if not plan:
            print("Plan not found in MongoDB")
            continue

        print("Name:", plan.get("name"))
        print(
            "payment_due_management:",
            plan.get("features", {}).get("payment_due_management", "MISSING")
        )

        print("All features:")
        print(plan.get("features", {}))


if __name__ == "__main__":
    asyncio.run(main())