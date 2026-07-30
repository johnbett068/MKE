# Payment and Settlement Boundary

## Principles

- Provider callbacks never mutate balances directly from views.
- Every client initiation requires an account-scoped `Idempotency-Key`.
- Provider callbacks have their own provider/event uniqueness boundary.
- Wallet and intent state changes occur in one database transaction.
- M-Pesa credentials and callback tokens are environment configuration.
- Raw callback payloads are retained for reconciliation and disputes.

## Payment intents

`PaymentIntent` represents a requested collection:

- `wallet_topup` credits available wallet balance.
- `cash_debt` reduces cash-commission debt.

Repeating the same account/idempotency key returns the original intent. Reusing
that key with different wallet, purpose, or amount is rejected.

## M-Pesa integration hooks

- `POST /api/v1/payments/mpesa/stk/`
- `POST /api/v1/payments/webhooks/mpesa/stk/`
- `POST /api/v1/payments/webhooks/mpesa/c2b/validation/`
- `POST /api/v1/payments/webhooks/mpesa/c2b/confirmation/`
- `POST /api/v1/payments/webhooks/mpesa/b2c/result/`

The STK callback correlates by `CheckoutRequestID`, verifies the collected
amount, records the provider event, and idempotently settles the wallet.

C2B and B2C hooks currently provide durable, deduplicated ingestion boundaries.
Their product-specific reconciliation policies must be defined before they
settle balances.

When `MPESA_CALLBACK_TOKEN` is configured, callbacks require the same value in
`X-MKE-Callback-Token`. Production must additionally apply HTTPS, gateway/IP
controls where supported, monitoring, and reconciliation jobs.

`MpesaGateway.initiate_b2c` is intentionally blocked until certificate-backed
security credentials and an approved disbursement policy are configured.
