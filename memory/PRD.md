# Vyastha — Business Billing & Invoicing System (Phase 1)

## Original Problem Statement
Build a full-stack web application called **Vyastha** — a Business Billing & Invoicing System (Phase 1) focused on customer acquisition and trust through a professional invoicing, quotation, payment, and basic inventory system, with authentication (business owner login/signup) and a clean, professional dashboard.

## Architecture
- **Frontend:** React 19 + Tailwind + Shadcn UI + lucide-react + sonner + html2canvas + jsPDF + qrcode
- **Backend:** FastAPI + Motor (async MongoDB) + JWT + bcrypt
- **Database:** MongoDB (collections: users, company_profiles, customers, products, inventory_transactions, invoices, quotations, payments, sequences)
- **Auth:** Custom JWT (Bearer token in localStorage `vyastha_token`)

## User Personas
- **Business Owner (primary):** Small/mid-sized Indian business owner needing GST-compliant invoicing, quotations, stock tracking, UPI collections.

## Core Requirements (static)
1. **Billing Module** — Invoice + Quotation builders with seller/buyer/additional details, editable T&C, bank details, signature (draw/upload), auto-generated dynamic UPI QR, line-items table with real-time auto-calc (subtotal, tax %, discount, total), PDF download, quotation → invoice conversion.
2. **Payments Module** — Payment history (today by default + all), record payments against invoices, dynamic UPI Intent QR (`upi://pay?pa=...&pn=...&am=<total>&cu=INR`).
3. **Inventory Module** — Products with SKU, unit, price, opening stock, low-stock threshold. Auto-deduct stock on invoice save/convert; stock movement log; low-stock banner + counter.
4. **Customers Module** — Save reusable customers with GSTIN/PAN/contacts.
5. **Company Settings** — Seller company profile (GSTIN, PAN, logo, tagline), bank details + UPI ID, signature, default T&C, invoice/quotation number prefixes.
6. **Drafts** — Cap 50 drafts/day; separate Drafts tab to open/edit/finalize/delete.
7. **Dashboard** — Total invoiced, today's collections, outstanding, drafts used, recent invoices & payments.

## What's Been Implemented (2026-02-21)
- **Auth:** JWT register, login, `/auth/me`, 1-click demo login, logout.
- **Company Profile:** Get/put with bank + UPI + signature + prefixes.
- **Customers:** Full CRUD, GST filter, search.
- **Products/Inventory:** CRUD, stock In/Out modal, transactions log, low-stock alerts endpoint.
- **Invoices:** Create/list/get/update/delete, auto-numbering (`INV-YYYY-NNNN`), server-side totals recompute, UPI QR string built on save, auto-deducts stock on finalize.
- **Quotations:** Create/list/get/delete, convert-to-invoice (auto-fills `reference_quotation_number`), guards duplicate conversion (409).
- **Drafts:** 50/day quota enforced; stats endpoint.
- **Payments:** Record + list (filter=today/all); validates amount > 0 and ≤ balance_due; updates invoice payment_status and balance.
- **Dashboard stats:** Revenue, collections, outstanding, drafts count, recent lists.
- **Seed:** `/api/seed/demo-data` populates realistic demo tenant.
- **Frontend:** All routes wired via AuthProvider + ProtectedRoute; 13 pages built (Login, Register, Onboarding, Dashboard, Invoices, InvoiceBuilder, Quotations, QuotationBuilder, Drafts, Payments, Inventory, Customers, Settings); PDF preview with dynamic UPI QR image.

## Testing Status (iteration_1)
- **Backend pytest:** 43/47 passing (91%). Critical ObjectId leak fixed. Remaining known-open: brute-force lockout, seed-admin idempotency, CORS wildcard.
- **Frontend Playwright:** 100% of P0 flows passing (login, all sidebar pages, invoice/quote auto-calc, stock deduct, PDF+QR, quote conversion, payments, drafts, customers, settings, mobile nav).

## Prioritized Backlog

### P1
- [ ] Payment amount ≤ invoice balance validation surfaced to UI (backend now returns 400; frontend should show toast — currently generic).
- [ ] Show provisional invoice/quotation number in pre-save PDF preview instead of empty `#`.
- [ ] Swap native date inputs for shadcn Calendar (dd/mm/yyyy for India).
- [ ] Reverse stock deduction when a finalized invoice is deleted.

### P2
- [ ] Brute-force login lockout after 5 failures (per auth playbook).
- [ ] Explicit CORS origin allowlist from env (current `*` + credentials breaks cookies cross-origin).
- [ ] Make `seed_admin` idempotent on `ADMIN_PASSWORD` change.
- [ ] Return 404 from `DELETE /api/products/{id}` and `DELETE /api/quotations/{id}` on missing IDs.
- [ ] Refactor server.py (1560 LOC) into routers + services; extract `compute_totals()` helper.
- [ ] Object Storage for company logo & signature (currently base64 DataURL — fine for MVP, less scalable).

## Test Credentials
See `/app/memory/test_credentials.md` (demo@vyastha.com / demopassword123).
