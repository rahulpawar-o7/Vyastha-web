import asyncio
import server

async def check():
    u = await server.db.users.find_one({})
    if not u:
        print("NO USER FOUND")
        return

    print({
        "id": u.get("id"),
        "email": u.get("email"),
        "name": u.get("name"),
        "business_id": u.get("business_id"),
        "role": u.get("role"),
    })

asyncio.run(check())
