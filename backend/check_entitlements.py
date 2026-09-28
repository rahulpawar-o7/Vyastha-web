import asyncio

from lib.db import db
from lib.features import resolve_entitlements


async def main():
    user = await db.users.find_one(
        {
            "id": "16e64a61-e9ab-4dcb-8480-e6998e9eda20"
        },
        {
            "_id": 0
        }
    )

    print("USER:")
    print(user)

    print("\nENTITLEMENTS:")
    entitlements = await resolve_entitlements(user)
    print(entitlements)


asyncio.run(main())