import hashlib
import secrets
from datetime import datetime, timedelta, timezone


VERIFICATION_TOKEN_EXPIRE_MINUTES = 30


def generate_email_verification_token() -> tuple[str, str, datetime]:
    """
    Generate a secure email-verification token.

    Returns:
        raw_token:
            Token that is safe to send in the email link.

        token_hash:
            SHA-256 hash stored in MongoDB.

        expires_at:
            UTC expiration timestamp.
    """

    raw_token = secrets.token_urlsafe(32)

    token_hash = hashlib.sha256(
        raw_token.encode("utf-8")
    ).hexdigest()

    expires_at = (
        datetime.now(timezone.utc)
        + timedelta(
            minutes=VERIFICATION_TOKEN_EXPIRE_MINUTES
        )
    )

    return (
        raw_token,
        token_hash,
        expires_at,
    )


def hash_email_verification_token(
    token: str,
) -> str:
    """
    Hash a verification token received from the URL.
    """

    return hashlib.sha256(
        token.encode("utf-8")
    ).hexdigest()