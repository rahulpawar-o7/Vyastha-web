from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr, Field

from lib.auth import get_current_user, hash_password
from lib.db import db
from lib.features import require_feature, resolve_entitlements


router = APIRouter(
    prefix="/team",
    tags=["Team & Staff"],
)


class CreateStaffRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)
    name: str = Field(min_length=1, max_length=100)


@router.get("/members")
async def get_team_members(
    user: dict = Depends(get_current_user),
    _: None = Depends(require_feature("multi_user")),
) -> list[dict[str, Any]]:
    """
    Return all users belonging to the current business.
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


@router.post("/members")
async def create_staff_member(
    payload: CreateStaffRequest,
    user: dict = Depends(get_current_user),
    _: None = Depends(require_feature("multi_user")),
) -> dict[str, Any]:

    business_id = user.get("business_id")

    if not business_id:
        raise HTTPException(
            status_code=500,
            detail="Business context is missing.",
        )

    # Only the business owner can add staff.
    if user.get("role") not in {"owner", "business_owner"}:
        raise HTTPException(
            status_code=403,
            detail="Only the business owner can manage team members.",
        )

   # Count current users in this business.
    current_count = await db.users.count_documents(
        {"business_id": business_id}
    )

    # Read the user limit from the active plan entitlement.
    entitlements = await resolve_entitlements(business_id)

    user_limit = entitlements.get("limits", {}).get("users", 1)

    if current_count >= user_limit:
        raise HTTPException(
            status_code=400,
            detail=f"Maximum of {user_limit} users allowed on your current plan.",
    )

    email = str(payload.email).strip().lower()

    # Email must be unique.
    existing_user = await db.users.find_one(
        {"email": email}
    )

    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="A user with this email already exists.",
        )

    staff_id = str(__import__("uuid").uuid4())

    staff = {
        "id": staff_id,
        "email": email,
        "name": payload.name.strip(),
        "password_hash": hash_password(payload.password),
        "business_id": business_id,
        "role": "staff",
        "is_platform_admin": False,
        "created_at": __import__("datetime").datetime.now(
            __import__("datetime").timezone.utc
        ),
        "updated_at": __import__("datetime").datetime.now(
            __import__("datetime").timezone.utc
        ),
    }

    await db.users.insert_one(staff)

    return {
        "id": staff_id,
        "email": email,
        "name": staff["name"],
        "role": "staff",
        "is_platform_admin": False,
        "created_at": staff["created_at"],
    }


@router.delete("/members/{member_id}")
async def delete_team_member(
    member_id: str,
    user: dict = Depends(get_current_user),
    _: None = Depends(require_feature("multi_user")),
) -> dict[str, str]:

    business_id = user.get("business_id")

    # Only the business owner can remove staff.
    if user.get("role") not in {"owner", "business_owner"}:
        raise HTTPException(
            status_code=403,
            detail="Only the business owner can manage team members.",
        )

    # Find the member inside the current business only.
    member = await db.users.find_one(
        {
            "id": member_id,
            "business_id": business_id,
        }
    )

    if not member:
        raise HTTPException(
            status_code=404,
            detail="Team member not found.",
        )

    # Owner cannot delete their own account through this endpoint.
    if member.get("role") in {"owner", "business_owner"}:
        raise HTTPException(
            status_code=400,
            detail="Business owner cannot be removed.",
        )

    result = await db.users.delete_one(
        {
            "id": member_id,
            "business_id": business_id,
        }
    )

    if result.deleted_count == 0:
        raise HTTPException(
            status_code=404,
            detail="Team member not found.",
        )

    return {
        "message": "Team member removed successfully."
    }