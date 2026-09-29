from lib.db import db


async def get_business_data_owner_id(user: dict) -> str:
    """
    Return the canonical data-owner user_id for the current business.

    Existing Vyastha business data is currently stored using the owner's
    user_id. Staff members share the same business_id, so this helper
    resolves their business owner's user_id without changing existing data.
    """

    current_user_id = user.get("id") or str(user.get("_id", ""))
    business_id = user.get("business_id")

    # Existing users without a business context keep their own scope.
    if not business_id:
        return current_user_id

    # If current user is already the business owner, no lookup is needed.
    if user.get("role") in {"owner", "business_owner"}:
        return current_user_id

    # Staff members use the business owner's existing data scope.
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

    # Safe fallback if an owner cannot be resolved.
    return current_user_id