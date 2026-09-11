# Vyastha GST Invoice Module

Integration-ready GST Tax Invoice module for Vyastha.

## Important
This module is intentionally isolated behind clean service/API boundaries because the complete Vyastha frontend/backend source was not supplied. It does **not** invent your existing model names or overwrite billing logic.

The backend exposes:
- GST calculation
- invoice creation from billing payload
- invoice retrieval
- duplicate invoice as a new draft
- invoice listing
- tax breakup
- amount in words
- UPI QR payload generation

The frontend provides:
- A4 invoice preview
- Classic GST template
- Modern GST template
- Retail template
- Premium template
- Print
- Browser PDF via print dialog
- WhatsApp/share actions
- Responsive preview

## Backend
Copy `backend/vyastha_invoice/` into the existing FastAPI backend and mount the router:

```python
from vyastha_invoice.router import router as invoice_router
app.include_router(invoice_router, prefix="/api")
```

The default in-memory repository is only a development adapter. Replace
`InvoiceRepository` methods with your existing MongoDB `db.<collection>` calls.

## Frontend
Copy `frontend/InvoiceModule.tsx` and `frontend/invoice.css` into the existing React/TypeScript application.

Use:

```tsx
<InvoiceModule
  billingData={confirmedBill}
  onSaved={(invoice) => console.log(invoice)}
/>
```

`billingData` is normalized by the module, but the recommended production integration is to map your existing billing object to the documented `BillingPayload`.

## Production integration rule
Inventory deduction must happen when the existing bill is confirmed, not when an invoice is previewed, printed, downloaded or shared. The invoice service should consume the confirmed transaction/snapshot so reprints cannot deduct stock twice.
