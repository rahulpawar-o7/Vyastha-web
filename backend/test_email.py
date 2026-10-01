import asyncio
from lib.email import send_email

async def main():
    result = await send_email(
        to_email="pawar.rahuljii@gmail.com",
        subject="Vyastha Email Test",
        html="""
        <h2>Vyastha Email Service Working</h2>
        <p>This is a test email from the Vyastha backend.</p>
        <p>Resend integration is working successfully.</p>
        """,
    )

    print("EMAIL RESULT:", result)

asyncio.run(main())
