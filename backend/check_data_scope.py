import asyncio
from lib.db import db


async def main():
    users = await db.users.find(
        {},
        {
            "_id": 0,
            "id": 1,
            "email": 1,
            "role": 1,
            "business_id": 1
        }
    ).to_list(100)

    print("\n========== DATA SCOPE CHECK ==========\n")

    for user in users:
        user_id = user.get("id")
        email = user.get("email")
        role = user.get("role")
        business_id = user.get("business_id")

        invoices = await db.invoices.count_documents({
            "user_id": user_id
        })

        products = await db.products.count_documents({
            "user_id": user_id
        })

        quotations = await db.quotations.count_documents({
            "user_id": user_id
        })

        customers = await db.customers.count_documents({
            "user_id": user_id
        })

        payments = await db.payments.count_documents({
            "user_id": user_id
        })

        print(f"Email       : {email}")
        print(f"Role        : {role}")
        print(f"User ID     : {user_id}")
        print(f"Business ID : {business_id}")
        print(f"Invoices    : {invoices}")
        print(f"Products    : {products}")
        print(f"Quotations  : {quotations}")
        print(f"Customers   : {customers}")
        print(f"Payments    : {payments}")
        print("--------------------------------------")


asyncio.run(main())