import asyncio

from lib.db import db


async def main():
    print("\n=== UPDATING PAYMENT DUE MANAGEMENT ===")

    free_result = await db.plans.update_one(
        {"slug": "free"},
        {
            "$set": {
                "features.payment_due_management": False
            }
        }
    )

    pro_result = await db.plans.update_one(
        {"slug": "pro"},
        {
            "$set": {
                "features.payment_due_management": True
            }
        }
    )

    print("Free matched:", free_result.matched_count)
    print("Free modified:", free_result.modified_count)

    print("Pro matched:", pro_result.matched_count)
    print("Pro modified:", pro_result.modified_count)

    print("\nPayment due management feature updated successfully.")


if __name__ == "__main__":
    asyncio.run(main())