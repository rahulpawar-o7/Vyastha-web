import os
from html import escape
from pathlib import Path

import resend
from dotenv import load_dotenv


ROOT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(ROOT_DIR / ".env")


RESEND_API_KEY = os.environ.get("RESEND_API_KEY")

# Temporary development sender.
# Later, after buying and verifying the Vyastha domain,
# this will be replaced through EMAIL_FROM in .env.
EMAIL_FROM = os.environ.get(
    "EMAIL_FROM",
    "Vyastha <onboarding@resend.dev>",
)

FRONTEND_URL = os.environ.get(
    "FRONTEND_URL",
    "http://localhost:3000",
)


if not RESEND_API_KEY:
    raise RuntimeError(
        "RESEND_API_KEY is missing from backend/.env"
    )


resend.api_key = RESEND_API_KEY


async def send_email(
    to_email: str,
    subject: str,
    html: str,
) -> dict:
    """
    Send an email through Resend.
    """

    try:
        params: resend.Emails.SendParams = {
            "from": EMAIL_FROM,
            "to": [to_email],
            "subject": subject,
            "html": html,
        }

        result = await resend.Emails.send_async(params)

        return {
            "success": True,
            "id": getattr(result, "id", None),
        }

    except Exception as exc:
        print(f"Resend email error: {exc}")
        raise RuntimeError("Failed to send email") from exc


async def send_verification_email(
    to_email: str,
    user_name: str,
    verification_token: str,
) -> dict:
    """
    Send account email-verification link.
    """

    safe_name = escape(user_name)

    verification_url = (
        f"{FRONTEND_URL}/verify-email"
        f"?token={verification_token}"
    )

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Verify your Vyastha account</title>
    </head>

    <body
        style="
            margin:0;
            padding:0;
            background:#f4f7fb;
            font-family:Arial,Helvetica,sans-serif;
            color:#1f2937;
        "
    >

        <div
            style="
                max-width:600px;
                margin:40px auto;
                background:#ffffff;
                border-radius:12px;
                overflow:hidden;
                box-shadow:0 4px 18px rgba(0,0,0,0.08);
            "
        >

            <div
                style="
                    background:#2563eb;
                    padding:24px;
                    text-align:center;
                    color:#ffffff;
                "
            >
                <h1 style="margin:0;font-size:28px;">
                    Vyastha
                </h1>

                <p style="margin:8px 0 0;font-size:14px;">
                    Business Billing & Management
                </p>
            </div>

            <div style="padding:32px;">

                <h2 style="margin-top:0;">
                    Verify your email
                </h2>

                <p>
                    Hi {safe_name},
                </p>

                <p>
                    Thanks for creating your Vyastha account.
                    Please verify your email address to activate
                    your account.
                </p>

                <div style="text-align:center;margin:32px 0;">

                    <a
                        href="{verification_url}"
                        style="
                            display:inline-block;
                            background:#2563eb;
                            color:#ffffff;
                            text-decoration:none;
                            padding:13px 24px;
                            border-radius:8px;
                            font-weight:bold;
                        "
                    >
                        Verify Email
                    </a>

                </div>

                <p style="font-size:14px;color:#6b7280;">
                    If the button does not work, copy and open this link:
                </p>

                <p
                    style="
                        font-size:13px;
                        word-break:break-all;
                        color:#2563eb;
                    "
                >
                    {escape(verification_url)}
                </p>

                <p style="font-size:14px;color:#6b7280;">
                    If you did not create this account, you can safely
                    ignore this email.
                </p>

            </div>

            <div
                style="
                    padding:18px 32px;
                    background:#f9fafb;
                    text-align:center;
                    font-size:12px;
                    color:#6b7280;
                "
            >
                © Vyastha. All rights reserved.
            </div>

        </div>

    </body>
    </html>
    """

    return await send_email(
        to_email=to_email,
        subject="Verify your Vyastha account",
        html=html,
    )


async def send_password_reset_email(
    to_email: str,
    user_name: str,
    reset_token: str,
) -> dict:
    """
    Send password-reset link.
    """

    safe_name = escape(user_name)

    reset_url = (
        f"{FRONTEND_URL}/reset-password"
        f"?token={reset_token}"
    )

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Reset your Vyastha password</title>
    </head>

    <body
        style="
            margin:0;
            padding:0;
            background:#f4f7fb;
            font-family:Arial,Helvetica,sans-serif;
            color:#1f2937;
        "
    >

        <div
            style="
                max-width:600px;
                margin:40px auto;
                background:#ffffff;
                border-radius:12px;
                overflow:hidden;
                box-shadow:0 4px 18px rgba(0,0,0,0.08);
            "
        >

            <div
                style="
                    background:#2563eb;
                    padding:24px;
                    text-align:center;
                    color:#ffffff;
                "
            >
                <h1 style="margin:0;font-size:28px;">
                    Vyastha
                </h1>

                <p style="margin:8px 0 0;font-size:14px;">
                    Business Billing & Management
                </p>
            </div>

            <div style="padding:32px;">

                <h2 style="margin-top:0;">
                    Reset your password
                </h2>

                <p>
                    Hi {safe_name},
                </p>

                <p>
                    We received a request to reset the password
                    for your Vyastha account.
                </p>

                <div style="text-align:center;margin:32px 0;">

                    <a
                        href="{reset_url}"
                        style="
                            display:inline-block;
                            background:#2563eb;
                            color:#ffffff;
                            text-decoration:none;
                            padding:13px 24px;
                            border-radius:8px;
                            font-weight:bold;
                        "
                    >
                        Reset Password
                    </a>

                </div>

                <p style="font-size:14px;color:#6b7280;">
                    If the button does not work, copy and open this link:
                </p>

                <p
                    style="
                        font-size:13px;
                        word-break:break-all;
                        color:#2563eb;
                    "
                >
                    {escape(reset_url)}
                </p>

                <p style="font-size:14px;color:#6b7280;">
                    If you did not request a password reset,
                    you can safely ignore this email.
                </p>

            </div>

            <div
                style="
                    padding:18px 32px;
                    background:#f9fafb;
                    text-align:center;
                    font-size:12px;
                    color:#6b7280;
                "
            >
                © Vyastha. All rights reserved.
            </div>

        </div>

    </body>
    </html>
    """

    return await send_email(
        to_email=to_email,
        subject="Reset your Vyastha password",
        html=html,
    )