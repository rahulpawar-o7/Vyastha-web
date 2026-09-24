from datetime import datetime, timezone, timedelta
import os

import bcrypt
import jwt
from bson import ObjectId
from fastapi import HTTPException, Request

from lib.db import db


JWT_SECRET = os.environ.get(
    "JWT_SECRET",
    "vyastha_jwt_secret_key_2026_default_99",
)

JWT_ALGORITHM = "HS256"


def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(
        password.encode("utf-8"),
        salt,
    )
    return hashed.decode("utf-8")


def verify_password(
    plain_password: str,
    hashed_password: str,
) -> bool:
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            hashed_password.encode("utf-8"),
        )
    except Exception:
        return False


def create_access_token(
    user_id: str,
    email: str,
) -> str:
    payload = {
        "sub": user_id,
        "email": email,
        "exp": datetime.now(timezone.utc)
        + timedelta(days=7),
        "type": "access",
    }

    return jwt.encode(
        payload,
        JWT_SECRET,
        algorithm=JWT_ALGORITHM,
    )


def create_refresh_token(
    user_id: str,
) -> str:
    payload = {
        "sub": user_id,
        "exp": datetime.now(timezone.utc)
        + timedelta(days=30),
        "type": "refresh",
    }

    return jwt.encode(
        payload,
        JWT_SECRET,
        algorithm=JWT_ALGORITHM,
    )


async def get_current_user(
    request: Request,
) -> dict:
    token = request.cookies.get(
        "access_token"
    )

    if not token:
        auth_header = request.headers.get(
            "Authorization",
            "",
        )

        if auth_header.startswith(
            "Bearer "
        ):
            token = auth_header[7:]

    if not token:
        raise HTTPException(
            status_code=401,
            detail="Authentication required",
        )

    try:
        payload = jwt.decode(
            token,
            JWT_SECRET,
            algorithms=[JWT_ALGORITHM],
        )

        if payload.get("type") != "access":
            raise HTTPException(
                status_code=401,
                detail="Invalid token type",
            )

        user_id = payload.get("sub")

        try:
            user = await db.users.find_one(
                {"_id": ObjectId(user_id)}
            )
        except Exception:
            user = await db.users.find_one(
                {"id": user_id}
            )

        if not user:
            user = await db.users.find_one(
                {
                    "email": payload.get(
                        "email"
                    )
                }
            )

        if not user:
            raise HTTPException(
                status_code=401,
                detail="User not found",
            )

        user["_id"] = str(user["_id"])
        user.pop(
            "password_hash",
            None,
        )

        return user

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=401,
            detail="Token expired",
        )

    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=401,
            detail="Invalid token",
        )