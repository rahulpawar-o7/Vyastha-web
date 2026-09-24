import asyncio
from lib.db import db


async def main():
    print("Database:", db.name)

    count = await db.users.count_documents({})
    print("Users count:", count)

    users = await db.users.find(
        {},
        {
            "_id": 0,
            "email": 1,
            "created_at": 1,
            "updated_at": 1,
            "last_login": 1,
            "first_login_at": 1,
            "login_at": 1,
            "business_id": 1,
        }
    ).to_list(None)

    print("Users found:", len(users))

    for user in users:
        print(user)


asyncio.run(main())