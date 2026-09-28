from datetime import datetime, timezone
from typing import Any, Dict

from fastapi import APIRouter, Depends

from lib.auth import get_current_user
from lib.db import db
from lib.features import require_feature


router = APIRouter(
    prefix="/analytics",
    tags=["Advanced Analytics"],
)


@router.get("/advanced")
async def get_advanced_analytics(
    user: dict = Depends(get_current_user),
    _: None = Depends(require_feature("advanced_analytics")),
):
    """
    Advanced business analytics for Vyastha Pro users.

    Uses existing invoices, payments and products data.
    Does not modify existing dashboard/business logic.
    """

    user_id = user.get("id") or str(user["_id"])

    # ---------------------------------------------------------
    # Load existing business data
    # ---------------------------------------------------------
    all_invoices = await db.invoices.find(
        {"user_id": user_id},
        {"_id": 0},
    ).to_list(1000)

    all_payments = await db.payments.find(
        {"user_id": user_id},
        {"_id": 0},
    ).to_list(1000)

    all_products = await db.products.find(
        {"user_id": user_id},
        {"_id": 0},
    ).to_list(1000)

    # ---------------------------------------------------------
    # Invoice analytics
    # ---------------------------------------------------------
    active_invoices = [
        invoice
        for invoice in all_invoices
        if invoice.get("status") != "cancelled"
    ]

    paid_invoices = [
        invoice
        for invoice in active_invoices
        if invoice.get("payment_status") == "paid"
    ]

    partially_paid_invoices = [
        invoice
        for invoice in active_invoices
        if invoice.get("payment_status") == "partially_paid"
    ]

    unpaid_invoices = [
        invoice
        for invoice in active_invoices
        if invoice.get("payment_status") == "unpaid"
    ]

    total_revenue = sum(
        float(invoice.get("total_amount", 0) or 0)
        for invoice in active_invoices
    )

    total_invoice_amount_paid = sum(
        float(invoice.get("amount_paid", 0) or 0)
        for invoice in active_invoices
    )

    total_outstanding = sum(
        float(
            invoice.get(
                "balance_due",
                max(
                    float(invoice.get("total_amount", 0) or 0)
                    - float(invoice.get("amount_paid", 0) or 0),
                    0,
                ),
            )
            or 0
        )
        for invoice in active_invoices
    )

    collection_rate = (
        (total_invoice_amount_paid / total_revenue) * 100
        if total_revenue > 0
        else 0
    )

    # ---------------------------------------------------------
    # Payment analytics
    # ---------------------------------------------------------
    successful_payments = [
        payment
        for payment in all_payments
        if payment.get("status") == "successful"
    ]

    pending_payments = [
        payment
        for payment in all_payments
        if payment.get("status") == "pending"
    ]

    failed_payments = [
        payment
        for payment in all_payments
        if payment.get("status") == "failed"
    ]

    total_successful_payments = sum(
        float(payment.get("amount", 0) or 0)
        for payment in successful_payments
    )

    total_pending_payments = sum(
        float(payment.get("amount", 0) or 0)
        for payment in pending_payments
    )

    total_failed_payments = sum(
        float(payment.get("amount", 0) or 0)
        for payment in failed_payments
    )

    # ---------------------------------------------------------
    # Payment method breakdown
    # ---------------------------------------------------------
    payment_methods: Dict[str, Dict[str, Any]] = {}

    for payment in successful_payments:
        method = payment.get("payment_method") or "Unknown"

        if method not in payment_methods:
            payment_methods[method] = {
                "count": 0,
                "amount": 0.0,
            }

        payment_methods[method]["count"] += 1
        payment_methods[method]["amount"] += float(
            payment.get("amount", 0) or 0
        )

    # ---------------------------------------------------------
    # Inventory analytics
    # ---------------------------------------------------------
    total_products = len(all_products)

    low_stock_products = [
        product
        for product in all_products
        if float(product.get("stock_quantity", 0) or 0)
        <= float(product.get("low_stock_threshold", 10) or 10)
    ]

    out_of_stock_products = [
        product
        for product in all_products
        if float(product.get("stock_quantity", 0) or 0) <= 0
    ]

    inventory_value = sum(
        float(product.get("stock_quantity", 0) or 0)
        * float(product.get("unit_price", 0) or 0)
        for product in all_products
    )

    # ---------------------------------------------------------
    # Revenue by month
    # ---------------------------------------------------------
    monthly_revenue: Dict[str, float] = {}

    for invoice in active_invoices:
        invoice_date = (
            invoice.get("invoice_date")
            or invoice.get("created_at")
            or ""
        )

        if not invoice_date:
            continue

        month_key = str(invoice_date)[:7]

        monthly_revenue[month_key] = (
            monthly_revenue.get(month_key, 0.0)
            + float(invoice.get("total_amount", 0) or 0)
        )

    monthly_revenue = {
        month: round(amount, 2)
        for month, amount in sorted(monthly_revenue.items())
    }

    # ---------------------------------------------------------
    # Collections by month
    # ---------------------------------------------------------
    monthly_collections: Dict[str, float] = {}

    for payment in successful_payments:
        payment_date = (
            payment.get("payment_date")
            or payment.get("created_at")
            or ""
        )

        if not payment_date:
            continue

        month_key = str(payment_date)[:7]

        monthly_collections[month_key] = (
            monthly_collections.get(month_key, 0.0)
            + float(payment.get("amount", 0) or 0)
        )

    monthly_collections = {
        month: round(amount, 2)
        for month, amount in sorted(monthly_collections.items())
    }

    # ---------------------------------------------------------
    # Invoice count by month
    # ---------------------------------------------------------
    monthly_invoices: Dict[str, int] = {}

    for invoice in active_invoices:
        invoice_date = (
            invoice.get("invoice_date")
            or invoice.get("created_at")
            or ""
        )

        if not invoice_date:
            continue

        month_key = str(invoice_date)[:7]

        monthly_invoices[month_key] = (
            monthly_invoices.get(month_key, 0) + 1
        )

    # ---------------------------------------------------------
    # Final response
    # ---------------------------------------------------------
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),

        "revenue": {
            "total_revenue": round(total_revenue, 2),
            "total_collected": round(total_successful_payments, 2),
            "invoice_amount_paid": round(total_invoice_amount_paid, 2),
            "total_outstanding": round(total_outstanding, 2),
            "collection_rate_percent": round(collection_rate, 2),
        },

        "invoices": {
            "total": len(all_invoices),
            "active": len(active_invoices),
            "paid": len(paid_invoices),
            "partially_paid": len(partially_paid_invoices),
            "unpaid": len(unpaid_invoices),
            "cancelled": len(all_invoices) - len(active_invoices),
        },

        "payments": {
            "total": len(all_payments),
            "successful_count": len(successful_payments),
            "pending_count": len(pending_payments),
            "failed_count": len(failed_payments),
            "successful_amount": round(total_successful_payments, 2),
            "pending_amount": round(total_pending_payments, 2),
            "failed_amount": round(total_failed_payments, 2),
            "by_method": payment_methods,
        },

        "inventory": {
            "total_products": total_products,
            "low_stock_count": len(low_stock_products),
            "out_of_stock_count": len(out_of_stock_products),
            "inventory_value": round(inventory_value, 2),
        },

        "trends": {
            "monthly_revenue": monthly_revenue,
            "monthly_collections": monthly_collections,
            "monthly_invoice_count": dict(
                sorted(monthly_invoices.items())
            ),
        },
    }