"""
Authentication routes for Vyastha.

Authentication method:
- Email + password
- Server-side session
- httpOnly cookie
- Every user belongs to one business

Security:
- Passwords are never stored in plain text.
- Session identifiers are stored server-side.
- Authentication cookies are httpOnly.
- Password errors use a generic message.
"""

from __future__ import annotations

from urllib import response
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, Response

from lib.auth import (
    create_access_token,
    create_refresh_token,
    get_current_user,
    hash_password,
    verify_password,
)
from lib.db import db
from lib.email import (
    send_password_reset_email,
    send_verification_email,
)
from lib.email_verification import (
    generate_email_verification_token,
    hash_email_verification_token,
)
from lib.password_reset import (
    generate_password_reset_token,
    hash_password_reset_token,
)
from lib.features import resolve_entitlements
from models.billing import (
    BusinessOut,
    EntitlementsOut,
    ForgotPasswordRequest,
    LoginRequest,
    ResetPasswordRequest,
    SignupRequest,
    Subscription,
    UserOut,
)

router = APIRouter(
    prefix="/auth",
    tags=["auth"],
)

async def create_session(
    response: Response,
    user_id: str,
) -> str:
    user = await db.users.find_one({"id": user_id})

    if not user:
        raise HTTPException(
            status_code=401,
            detail="User not found",
        )

    email = user.get("email", "")

    access_token = create_access_token(
        user_id,
        email,
    )

    refresh_token = create_refresh_token(
        user_id,
    )

    response.set_cookie(
    key="access_token",
    value=access_token,
    httponly=True,
    secure=False,
    samesite="lax",
    max_age=86400 * 7,
    path="/",
)

    response.set_cookie(
    key="refresh_token",
    value=refresh_token,
    httponly=True,
    secure=False,
    samesite="lax",
    max_age=86400 * 30,
    path="/",
)

    return access_token


async def destroy_session(
    request: Request,
    response: Response,
) -> None:
    response.delete_cookie(
        key="access_token",
        path="/",
    )

    response.delete_cookie(
        key="refresh_token",
        path="/",
    )
# ---------------------------------------------------------------------------
# USER RESPONSE
# ---------------------------------------------------------------------------

async def _user_out(
    user: dict[str, Any],
) -> UserOut:
    """
    Convert an internal MongoDB user document into a safe public response.

    Password hashes and other internal fields are never returned.
    """

    business_id = user.get("business_id")

    if not business_id:
        raise HTTPException(
            status_code=500,
            detail="User business configuration is missing.",
        )

    business = await db.businesses.find_one(
        {"id": business_id}
    )

    if business is None:
        raise HTTPException(
            status_code=500,
            detail="Business configuration is missing.",
        )

    return UserOut(
        id=str(user["id"]),
        email=str(user["email"]),
        name=str(user.get("name", "")),
        role=str(user.get("role", "owner")),
        is_platform_admin=bool(
            user.get("is_platform_admin", False)
        ),
        business=BusinessOut(
            id=str(business["id"]),
            name=str(
                business.get(
                    "name",
                    "Business",
                )
            ),
        ),
    )


# ---------------------------------------------------------------------------
# SIGNUP
# ---------------------------------------------------------------------------

@router.post(
    "/signup",
    response_model=UserOut,
)
async def signup(
    payload: SignupRequest,
    response: Response,
) -> UserOut:
    """
    Create a new Vyastha user and business.

    A newly registered user becomes the owner of the created business.
    """

    email = str(payload.email).strip().lower()
    name = payload.name.strip()
    business_name = payload.business_name.strip()

    if not name or not business_name:
        raise HTTPException(
            status_code=400,
            detail="Name and business name are required.",
        )

    # Prevent duplicate accounts.
    existing_user = await db.users.find_one(
        {"email": email}
    )

    if existing_user:
        raise HTTPException(
            status_code=409,
            detail=(
                "An account with this email "
                "already exists."
            ),
        )

    now = datetime.now(timezone.utc)

    business_id = str(uuid.uuid4())
    user_id = str(uuid.uuid4())

    # -----------------------------------------------------------------------
    # CREATE BUSINESS
    # -----------------------------------------------------------------------

    business = {
        "id": business_id,
        "name": business_name,
        "created_at": now,
        "updated_at": now,
    }

    await db.businesses.insert_one(
        business
    )

    # -----------------------------------------------------------------------
    # CREATE USER
    # -----------------------------------------------------------------------

    raw_verification_token, verification_token_hash, verification_expires_at = (
        generate_email_verification_token()
    )

    user = {
    "id": user_id,
    "email": email,
    "name": name,
    "password_hash": hash_password(
        payload.password
    ),
    "business_id": business_id,
    "role": "owner",
    "is_platform_admin": False,
    "email_verified": False,
    "email_verification_token_hash": verification_token_hash,
    "email_verification_expires_at": verification_expires_at,
    "created_at": now,
    "updated_at": now,
}

    try:
        await db.users.insert_one(
            user
        )

    except Exception:
        # If user creation fails, remove the business that was created
        # immediately before it. This prevents orphan businesses.
        await db.businesses.delete_one(
            {"id": business_id}
        )
        raise

    # -----------------------------------------------------------------------
    # CREATE DEFAULT VYASTHA TRIAL SUBSCRIPTION
    # -----------------------------------------------------------------------

    free_plan = await db.plans.find_one(
        {"slug": "free"}
    )

    if not free_plan or not free_plan.get("id"):
        # Roll back the newly created user and business because
        # the default subscription plan is not configured.
        await db.users.delete_one(
            {"id": user_id}
        )
        await db.businesses.delete_one(
            {"id": business_id}
        )

        raise HTTPException(
            status_code=500,
            detail="Default Vyastha plan is not configured.",
        )

    trial_end = now + timedelta(
        days=int(
            free_plan.get(
                "trial_days",
                90,
            )
        )
    )

    subscription = Subscription(
    user_id=user_id,
    business_id=business_id,
    plan_id=str(
        free_plan["id"]
    ),
    plan_slug="free",
    billing_cycle="monthly",
    status="trialing",
    amount=0,
    currency="INR",
    trial_days=int(
        free_plan.get(
            "trial_days",
            90,
        )
    ),
    current_period_start=now,
    current_period_end=trial_end,
)

    await db.subscriptions.insert_one(
        subscription.model_dump()
    )
    # -----------------------------------------------------------------------
    # SEND EMAIL VERIFICATION
    # -----------------------------------------------------------------------

    try:
        await send_verification_email(
            to_email=email,
            user_name=name,
            verification_token=raw_verification_token,
        )
    except Exception:
        # Do not leave an unusable unverified account behind
        # if the verification email cannot be sent.
        await db.subscriptions.delete_one(
            {"user_id": user_id}
        )

        await db.users.delete_one(
            {"id": user_id}
        )

        await db.businesses.delete_one(
            {"id": business_id}
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "We could not send the verification email. "
                "Please try again."
            ),
        )

    # -----------------------------------------------------------------------
    # IMPORTANT:
    # Do not create a login session yet.
    # The user must verify the email first.
    # -----------------------------------------------------------------------

    return await _user_out(
        user
    )


# ---------------------------------------------------------------------------
# LOGIN
# ---------------------------------------------------------------------------

@router.post(
    "/login",
)
async def login(
    payload: LoginRequest,
    response: Response,
) -> dict[str, Any]:
    """
    Authenticate a user using email + password.
    """

    email = str(
        payload.email
    ).strip().lower()

    user = await db.users.find_one(
        {"email": email}
    )

    password_hash = (
        user.get("password_hash", "")
        if user
        else ""
    )

    # Generic error prevents account enumeration.
    if (
        not user
        or not password_hash
        or not verify_password(
            payload.password,
            password_hash,
        )
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password",
        )

    # Existing users created before email verification was introduced
    # are treated as verified for backward compatibility.
    if user.get("email_verified") is False:
        raise HTTPException(
            status_code=403,
            detail=(
                "Please verify your email address before logging in."
            ),
        )

    if not user.get("business_id"):
        raise HTTPException(
            status_code=500,
            detail="User business configuration is missing.",
        )

    access_token = await create_session(
        response,
        str(user["id"]),
    )

    user_data = await _user_out(user)

    return {
        "token": access_token,
        "user": user_data.model_dump(),
    }
@router.post("/forgot-password")
async def forgot_password(payload: ForgotPasswordRequest) -> dict[str, str]:
    email = payload.email.strip().lower()

    user = await db.users.find_one({"email": email})

    # Security: account exist karta hai ya nahi, response se reveal nahi karna.
    if not user:
        return {
            "message": "If an account exists with this email, a password reset link has been sent."
        }

    raw_token, token_hash, expires_at = generate_password_reset_token()

    await db.users.update_one(
        {"id": user["id"]},
        {
            "$set": {
                "password_reset_token_hash": token_hash,
                "password_reset_expires_at": expires_at,
                "updated_at": datetime.now(timezone.utc),
            }
        },
    )

    try:
        await send_password_reset_email(
            to_email=user["email"],
            user_name=user.get("name", "there"),
            reset_token=raw_token,
        )
    except Exception:
        # Token ko invalidate kar do agar email send nahi ho paya.
        await db.users.update_one(
            {"id": user["id"]},
            {
                "$unset": {
                    "password_reset_token_hash": "",
                    "password_reset_expires_at": "",
                }
            },
        )
        raise HTTPException(
            status_code=500,
            detail="Unable to send password reset email. Please try again later.",
        )

    return {
        "message": "If an account exists with this email, a password reset link has been sent."
    }



@router.post("/reset-password")
async def reset_password(
    payload: ResetPasswordRequest,
) -> dict[str, str]:
    token = payload.token.strip()

    token_hash = hash_password_reset_token(token)

    user = await db.users.find_one(
        {
            "password_reset_token_hash": token_hash,
        }
    )

    if not user:
        raise HTTPException(
            status_code=400,
            detail="Invalid or already used password reset link.",
        )

    expires_at = user.get("password_reset_expires_at")

    if not expires_at:
        raise HTTPException(
            status_code=400,
            detail="Password reset link is invalid.",
        )

    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)

    if expires_at <= datetime.now(timezone.utc):
        raise HTTPException(
            status_code=400,
            detail="Password reset link has expired.",
        )

    new_password_hash = hash_password(payload.new_password)

    await db.users.update_one(
        {"id": user["id"]},
        {
            "$set": {
                "password_hash": new_password_hash,
                "updated_at": datetime.now(timezone.utc),
            },
            "$unset": {
                "password_reset_token_hash": "",
                "password_reset_expires_at": "",
            },
        },
    )

    return {
        "message": "Password reset successfully. You can now log in with your new password."
    }
# ---------------------------------------------------------------------------
# LOGOUT
# ---------------------------------------------------------------------------

@router.post(
    "/logout",
)
async def logout(
    request: Request,
    response: Response,
) -> dict[str, bool]:
    """
    Destroy the current server-side session and clear the cookie.
    """

    await destroy_session(
        request,
        response,
    )

    return {
        "ok": True
    }


# ---------------------------------------------------------------------------
# CURRENT USER
# ---------------------------------------------------------------------------

@router.get(
    "/me",
    response_model=UserOut,
)
async def me(
    user: dict[str, Any] = Depends(
        get_current_user
    ),
) -> UserOut:
    """
    Return the currently authenticated user.
    """

    return await _user_out(
        user
    )


# ---------------------------------------------------------------------------
# ENTITLEMENTS
# ---------------------------------------------------------------------------

@router.get(
    "/entitlements",
    response_model=EntitlementsOut,
)
async def entitlements(
    user: dict[str, Any] = Depends(
        get_current_user
    ),
) -> EntitlementsOut:
    """
    Return the effective subscription features and limits
    available to the current business.
    """

    business_id = user.get(
        "business_id"
    )

    if not business_id:
        raise HTTPException(
            status_code=500,
            detail="Business context is missing.",
        )

    entitlement_data = await resolve_entitlements(
        business_id
    )

    return EntitlementsOut(
        **entitlement_data
    )



# ---------------------------------------------------------------------------
# EMAIL VERIFICATION
# ---------------------------------------------------------------------------

@router.get(
    "/verify-email",
)
async def verify_email(
    token: str,
) -> dict[str, str]:
    """
    Verify a user's email address using a one-time token.
    """

    token = token.strip()

    if not token:
        raise HTTPException(
            status_code=400,
            detail="Verification token is required.",
        )

    token_hash = hash_email_verification_token(
        token
    )

    user = await db.users.find_one(
        {
            "email_verification_token_hash": token_hash,
            "email_verified": False,
        }
    )

    if not user:
        raise HTTPException(
            status_code=400,
            detail=(
                "Invalid or already used verification link."
            ),
        )

    expires_at = user.get(
        "email_verification_expires_at"
    )

    if not expires_at:
        raise HTTPException(
            status_code=400,
            detail="Verification link is invalid.",
        )

    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(
            tzinfo=timezone.utc
        )

    if expires_at <= datetime.now(timezone.utc):
        raise HTTPException(
            status_code=400,
            detail="Verification link has expired.",
        )

    await db.users.update_one(
        {
            "id": user["id"],
        },
        {
            "$set": {
                "email_verified": True,
                "updated_at": datetime.now(
                    timezone.utc
                ),
            },
            "$unset": {
                "email_verification_token_hash": "",
                "email_verification_expires_at": "",
            },
        },
    )

    return {
        "message": "Email verified successfully.",
    }