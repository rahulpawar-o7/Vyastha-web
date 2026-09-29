import asyncio

from lib.db import db
from lib.data_scope import get_business_data_owner_id


async def main():
    users = await db.users.find(
        {
            "business_id": "0b0928f1-492c-4f21-b5cf-ac8cf2e84166"
        },
        {
            "_id": 0,
            "id": 1,
            "email": 1,
            "role": 1,
            "business_id": 1,
        },
    ).to_list(100)

    for user in users:
        owner_id = await get_business_data_owner_id(user)

        print("--------------------------------")
        print("Email       :", user.get("email"))
        print("Role        :", user.get("role"))
        print("Current ID  :", user.get("id"))
        print("Business ID :", user.get("business_id"))
        print("Data Owner  :", owner_id)


asyncio.run(main())