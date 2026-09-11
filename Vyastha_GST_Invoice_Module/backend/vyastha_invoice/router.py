from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, HTTPException

from .amount_words import amount_in_words
from .calculator import calculate
from .models import BillingPayload, Invoice
from .repository import InvoiceRepository

router = APIRouter(prefix="/invoices", tags=["GST Invoices"])
repo = InvoiceRepository()


@router.post("", response_model=Invoice)
async def create_invoice(payload: BillingPayload):
    try:
        calc = calculate(payload)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    invoice_number = payload.invoice_number or await repo.next_number()
    invoice = Invoice(
        id=str(uuid4()),
        invoice_number=invoice_number,
        invoice_date=payload.invoice_date or datetime.now().date(),
        business=payload.business,
        customer=payload.customer,
        **calc,
        amount_in_words=amount_in_words(calc["grand_total"]),
        payment_terms=payload.payment_terms or payload.business.payment_terms,
        notes=payload.notes or payload.business.footer_note,
        template=payload.template,
        created_at=datetime.now(timezone.utc),
    )

    try:
        return await repo.create(invoice)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.get("/{invoice_id}", response_model=Invoice)
async def get_invoice(invoice_id: str):
    invoice = await repo.get(invoice_id)
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return invoice


@router.get("", response_model=list[Invoice])
async def list_invoices():
    return await repo.list()


@router.post("/{invoice_id}/duplicate", response_model=Invoice)
async def duplicate_invoice(invoice_id: str):
    source = await repo.get(invoice_id)
    if not source:
        raise HTTPException(status_code=404, detail="Invoice not found")

    data = source.model_dump()
    data["id"] = str(uuid4())
    data["invoice_number"] = await repo.next_number()
    data["status"] = "draft"
    data["created_at"] = datetime.now(timezone.utc)
    return await repo.create(Invoice(**data))
