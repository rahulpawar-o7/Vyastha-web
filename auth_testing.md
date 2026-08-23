# Auth Testing Guide for Vyastha

## Credentials
- Admin: `admin@vyastha.com` / `adminpassword123`
- Demo: `demo@vyastha.com` / `demopassword123`

## Verification Steps:
1. Register or login via `/api/auth/login` or `/api/auth/demo-login`.
2. Check that response includes `token` and `user` object.
3. Verify `/api/auth/me` returns the authenticated user.
4. Check all billing, quotation, payment, and inventory endpoints require active authentication.