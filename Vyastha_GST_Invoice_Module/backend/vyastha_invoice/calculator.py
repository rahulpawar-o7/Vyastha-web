from __future__ import annotations

from collections import defaultdict
from decimal import Decimal, ROUND_HALF_UP

from .models import BillingPayload, InvoiceItem, TaxBreakup

PAISE = Decimal("0.01")


def money(value: Decimal) -> Decimal:
    return value.quantize(PAISE, rounding=ROUND_HALF_UP)


def same_state(business_state_code: str, customer_state_code: str) -> bool:
    # For GST billing, state code is the strongest normalized comparison.
    # If both are present and equal, transaction is intra-state.
    return bool(business_state_code and customer_state_code and
                business_state_code.strip() == customer_state_code.strip())


def calculate(payload: BillingPayload):
    intra = same_state(payload.business.state_code, payload.customer.state_code)

    items: list[InvoiceItem] = []
    subtotal = Decimal("0")
    discount_total = Decimal("0")
    taxable_total = Decimal("0")
    cgst_total = Decimal("0")
    sgst_total = Decimal("0")
    igst_total = Decimal("0")

    for src in payload.items:
        gross = money(src.quantity * src.price_per_unit)
        discount = money(min(src.discount, gross))
        taxable = money(gross - discount)
        tax = money(taxable * src.gst_rate / Decimal("100"))

        if intra:
            cgst = money(tax / 2)
            sgst = money(tax - cgst)
            igst = Decimal("0.00")
        else:
            cgst = Decimal("0.00")
            sgst = Decimal("0.00")
            igst = tax

        final = money(taxable + cgst + sgst + igst)

        items.append(InvoiceItem(
            product_id=src.product_id,
            name=src.name,
            hsn_sac=src.hsn_sac,
            quantity=src.quantity,
            unit=src.unit,
            price_per_unit=money(src.price_per_unit),
            discount=discount,
            gst_rate=src.gst_rate,
            taxable_amount=taxable,
            cgst_amount=cgst,
            sgst_amount=sgst,
            igst_amount=igst,
            final_amount=final,
        ))

        subtotal += gross
        discount_total += discount
        taxable_total += taxable
        cgst_total += cgst
        sgst_total += sgst
        igst_total += igst

    subtotal = money(subtotal)
    discount_total = money(discount_total)
    taxable_total = money(taxable_total)
    cgst_total = money(cgst_total)
    sgst_total = money(sgst_total)
    igst_total = money(igst_total)

    total_tax = money(cgst_total + sgst_total + igst_total)
    grand_total = money(taxable_total + total_tax)

    received = money(payload.amount_received)
    if received > grand_total:
        raise ValueError("Amount received cannot exceed grand total")

    balance = money(grand_total - received)

    grouped = defaultdict(lambda: {
        "taxable": Decimal("0"), "cgst": Decimal("0"),
        "sgst": Decimal("0"), "igst": Decimal("0"), "rate": Decimal("0")
    })

    for item in items:
        key = item.hsn_sac or "N/A"
        grouped[key]["taxable"] += item.taxable_amount
        grouped[key]["cgst"] += item.cgst_amount
        grouped[key]["sgst"] += item.sgst_amount
        grouped[key]["igst"] += item.igst_amount
        grouped[key]["rate"] = item.gst_rate

    breakup = []
    for hsn, x in grouped.items():
        rate = x["rate"]
        breakup.append(TaxBreakup(
            hsn_sac=hsn,
            taxable_amount=money(x["taxable"]),
            cgst_rate=money(rate / 2) if intra else Decimal("0.00"),
            cgst_amount=money(x["cgst"]),
            sgst_rate=money(rate / 2) if intra else Decimal("0.00"),
            sgst_amount=money(x["sgst"]),
            igst_rate=rate if not intra else Decimal("0.00"),
            igst_amount=money(x["igst"]),
            total_tax_amount=money(x["cgst"] + x["sgst"] + x["igst"]),
        ))

    return {
        "items": items,
        "subtotal": subtotal,
        "total_discount": discount_total,
        "taxable_total": taxable_total,
        "cgst": cgst_total,
        "sgst": sgst_total,
        "igst": igst_total,
        "total_tax": total_tax,
        "grand_total": grand_total,
        "amount_received": received,
        "balance_due": balance,
        "total_savings": discount_total,
        "tax_breakup": breakup,
    }
