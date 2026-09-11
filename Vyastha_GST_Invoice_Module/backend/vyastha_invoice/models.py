from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator


class BusinessProfile(BaseModel):
    name: str
    address: str = ""
    phone: str = ""
    email: str = ""
    gstin: str = ""
    state: str = ""
    state_code: str = ""
    logo_url: str | None = None
    bank_details: str = ""
    upi_id: str = ""
    payment_terms: str = ""
    footer_note: str = ""
    authorized_signatory: str = ""
    invoice_theme: str = "#111827"


class Customer(BaseModel):
    name: str = "Walk-in Customer"
    phone: str = ""
    address: str = ""
    gstin: str = ""
    state: str = ""
    state_code: str = ""


class BillingItem(BaseModel):
    product_id: str = ""
    name: str
    hsn_sac: str = ""
    quantity: Decimal = Field(gt=0)
    unit: str = "pcs"
    price_per_unit: Decimal = Field(ge=0)
    discount: Decimal = Field(default=Decimal("0"), ge=0)
    gst_rate: Decimal = Field(default=Decimal("0"), ge=0, le=Decimal("100"))

    @field_validator("discount")
    @classmethod
    def valid_discount(cls, v: Decimal) -> Decimal:
        if v < 0:
            raise ValueError("Discount cannot be negative")
        return v


class BillingPayload(BaseModel):
    business: BusinessProfile
    customer: Customer = Field(default_factory=Customer)
    items: list[BillingItem] = Field(min_length=1)
    invoice_number: str | None = None
    invoice_date: date | None = None
    amount_received: Decimal = Field(default=Decimal("0"), ge=0)
    payment_terms: str = ""
    notes: str = ""
    template: Literal["classic", "modern", "retail", "premium"] = "classic"


class InvoiceItem(BaseModel):
    product_id: str = ""
    name: str
    hsn_sac: str
    quantity: Decimal
    unit: str
    price_per_unit: Decimal
    discount: Decimal
    gst_rate: Decimal
    taxable_amount: Decimal
    cgst_amount: Decimal
    sgst_amount: Decimal
    igst_amount: Decimal
    final_amount: Decimal


class TaxBreakup(BaseModel):
    hsn_sac: str
    taxable_amount: Decimal
    cgst_rate: Decimal
    cgst_amount: Decimal
    sgst_rate: Decimal
    sgst_amount: Decimal
    igst_rate: Decimal
    igst_amount: Decimal
    total_tax_amount: Decimal


class Invoice(BaseModel):
    id: str
    invoice_number: str
    invoice_date: date
    business: BusinessProfile
    customer: Customer
    items: list[InvoiceItem]
    subtotal: Decimal
    total_discount: Decimal
    taxable_total: Decimal
    cgst: Decimal
    sgst: Decimal
    igst: Decimal
    total_tax: Decimal
    grand_total: Decimal
    amount_received: Decimal
    balance_due: Decimal
    total_savings: Decimal
    amount_in_words: str
    tax_breakup: list[TaxBreakup]
    payment_terms: str
    notes: str
    template: str
    created_at: datetime
    status: str = "finalized"
