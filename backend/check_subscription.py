import asyncio

from lib.db import db


async def main():
    subscription = await db.subscriptions.find_one(
        {
            "user_id": "16e64a61-e9ab-4dcb-8480-e6998e9eda20"
        },
        {
            "_id": 0
        }
    )

    print(subscription)


asyncio.run(main())