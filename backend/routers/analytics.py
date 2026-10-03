from datetime import datetime, timezone, date, timedelta
from typing import Any, Dict

from fastapi import APIRouter, Depends

from lib.auth import get_current_user
from lib.db import db
from lib.features import require_feature
from lib.business_scope import get_business_data_owner_id


router = APIRouter(
    prefix="/analytics",
    tags=["Advanced Analytics"],
)


@router.get("/advanced")
async def get_advanced_analytics(
    period: str = "month",
    user: dict = Depends(get_current_user),
    _: None = Depends(require_feature("advanced_analytics")),
    ):
    """
     Advanced business analytics for Vyastha Pro users.

    Uses existing invoices, payments and products data.
     Does not modify existing dashboard/business logic.
    """
    if period not in {"day", "week", "month", "year", "all"}:
        period = "month"

    user_id = await get_business_data_owner_id(user)
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

    # Top Products by Revenue
    # Uses finalized/sent/paid invoices only and aggregates
    # historical line-item revenue product-wise.

    product_revenue: Dict[str, Dict[str, Any]] = {}

    for invoice in active_invoices:
        if invoice.get("status") not in ["finalized", "sent", "paid"]:
            continue

        for item in invoice.get("line_items", []):
            product_id = item.get("product_id")
            product_name = (
                item.get("description")
                or product_id
                or "Unknown Product"
            )

            quantity = float(item.get("quantity", 0) or 0)
            unit_price = float(item.get("unit_price", 0) or 0)

            if quantity <= 0 or unit_price < 0:
                continue

            item_revenue = quantity * unit_price

            key = product_id or product_name

            if key not in product_revenue:
                product_revenue[key] = {
                    "product_name": product_name,
                    "revenue": 0.0,
                }

            product_revenue[key]["revenue"] += item_revenue

    top_products = sorted(
        product_revenue.values(),
        key=lambda item: item["revenue"],
        reverse=True,
    )[:5]

    top_products = [
        {
            "product_name": item["product_name"],
            "revenue": round(item["revenue"], 2),
        }
        for item in top_products
    ]

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
    # Period-based Sales vs Collections Chart
    # ---------------------------------------------------------
    from collections import defaultdict

    chart_sales = defaultdict(float)
    chart_collections = defaultdict(float)

    today = date.today()

    def parse_analytics_date(value):
        if not value:
            return None

        try:
            return datetime.fromisoformat(
                str(value).replace("Z", "+00:00")
            ).date()
        except (ValueError, TypeError):
            try:
                return date.fromisoformat(str(value)[:10])
            except (ValueError, TypeError):
                return None


    def get_period_key(value):
        if period == "day":
            return value.isoformat()

        if period == "week":
            week_start = value - timedelta(days=value.weekday())
            return week_start.isoformat()

        if period in {"month", "all"}:
            return value.strftime("%Y-%m")

        if period == "year":
            return str(value.year)

        return value.strftime("%Y-%m")

    # Define chart date range and labels
    if period == "day":
        start_date = today - timedelta(days=29)
        date_keys = [
            (start_date + timedelta(days=i)).isoformat()
            for i in range(30)
        ]

    elif period == "week":
        current_week_start = today - timedelta(days=today.weekday())
        start_date = current_week_start - timedelta(weeks=11)
        date_keys = [
            (start_date + timedelta(weeks=i)).isoformat()
            for i in range(12)
        ]

    elif period == "month":
        current_month = today.replace(day=1)
        date_keys = []

        for i in range(11, -1, -1):
            year = current_month.year
            month = current_month.month - i

            while month <= 0:
                month += 12
                year -= 1

            date_keys.append(f"{year:04d}-{month:02d}")

        start_date = date(
            int(date_keys[0][:4]),
            int(date_keys[0][5:7]),
            1,
        )

    else:
        start_date = None
        date_keys = []

    for invoice in active_invoices:
        invoice_date = parse_analytics_date(
            invoice.get("invoice_date") or invoice.get("created_at")
        )

        if invoice_date and (
            start_date is None or invoice_date >= start_date
        ):
            key = get_period_key(invoice_date)
            chart_sales[key] += float(
                invoice.get("total_amount", 0) or 0
            )

    for payment in successful_payments:
        payment_date = parse_analytics_date(
            payment.get("payment_date") or payment.get("created_at")
        )

        if payment_date and (
            start_date is None or payment_date >= start_date
        ):
            key = get_period_key(payment_date)
            chart_collections[key] += float(
                payment.get("amount", 0) or 0
            )

    if period == "year":
        date_keys = sorted(
            set(chart_sales.keys()) | set(chart_collections.keys())
        )

    elif period == "all":
        date_keys = sorted(
            set(chart_sales.keys()) | set(chart_collections.keys())
        )

    chart_data = [
        {
            "label": key,
            "sales": round(chart_sales[key], 2),
            "collected": round(chart_collections[key], 2),
        }
        for key in date_keys
    ]

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
        "top_products": top_products,

                "trends": {
            "monthly_revenue": monthly_revenue,
            "monthly_collections": monthly_collections,
            "monthly_invoice_count": dict(
                sorted(monthly_invoices.items())
            ),
            "chart_data": chart_data,
        },
    }