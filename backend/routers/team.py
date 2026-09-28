from typing import Any

from fastapi import APIRouter, Depends

from lib.auth import get_current_user
from lib.db import db
from lib.features import require_feature


router = APIRouter(
    prefix="/team",
    tags=["Team & Staff"],
)


@router.get("/members")
async def get_team_members(
    user: dict = Depends(get_current_user),
    _: None = Depends(require_feature("multi_user")),
) -> list[dict[str, Any]]:
    """
    Return all users belonging to the current business.

    Team & Staff Management is available only to plans
    with the multi_user feature enabled.
    """

    business_id = user.get("business_id")

    members = await db.users.find(
        {"business_id": business_id},
        {
            "_id": 0,
            "id": 1,
            "email": 1,
            "name": 1,
            "role": 1,
            "is_platform_admin": 1,
            "created_at": 1,
        },
    ).sort("created_at", 1).to_list(100)

    return members