from lib.db import db


async def get_business_data_owner_id(user: dict) -> str:
    """
    Returns the canonical data-owner user ID for the current business.

    Staff members keep their own identity/role, but business-owned
    data continues to use the business owner's existing user_id.
    """

    user_id = user.get("id") or str(user["_id"])

    business_id = user.get("business_id")

    if not business_id:
        return user_id

    owner = await db.users.find_one(
        {
            "business_id": business_id,
            "role": {"$in": ["owner", "business_owner"]},
        },
        {
            "_id": 0,
            "id": 1,
        },
    )

    if owner and owner.get("id"):
        return owner["id"]

    return user_id
