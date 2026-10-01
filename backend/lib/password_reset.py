import hashlib
import secrets
from datetime import datetime, timedelta, timezone


PASSWORD_RESET_TOKEN_EXPIRE_MINUTES = 30


def generate_password_reset_token() -> tuple[str, str, datetime]:
    raw_token = secrets.token_urlsafe(32)

    token_hash = hashlib.sha256(
        raw_token.encode("utf-8")
    ).hexdigest()

    expires_at = (
        datetime.now(timezone.utc)
        + timedelta(
            minutes=PASSWORD_RESET_TOKEN_EXPIRE_MINUTES
        )
    )

    return (
        raw_token,
        token_hash,
        expires_at,
    )


def hash_password_reset_token(
    token: str,
) -> str:
    return hashlib.sha256(
        token.encode("utf-8")
    ).hexdigest()