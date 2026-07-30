# API Contract

The supported API prefix is `/api/v1/`. Responses use JSON. Protected endpoints
require `Authorization: Bearer <access-token>`.

## Authentication and accounts

- `POST /api/v1/accounts/register/`
- `POST /api/v1/accounts/phone/request-code/`
- `POST /api/v1/accounts/phone/verify/`
- `POST /api/v1/accounts/password/request-reset/`
- `POST /api/v1/accounts/password/confirm-reset/`
- `POST /api/v1/auth/token/`
- `POST /api/v1/auth/token/refresh/`
- `GET /api/v1/accounts/me/`

Registration creates an account, profile, customer role, and customer wallet.

Verification and recovery endpoints always return a neutral accepted response
when an identifier may not exist. One-time codes expire, are attempt-limited,
and are stored only as hashes.

## Driver onboarding

- `POST /api/v1/drivers/applications/`
- `GET /api/v1/drivers/applications/me/`
- `GET /api/v1/drivers/vehicles/`
- `GET/PATCH /api/v1/drivers/vehicles/{id}/`
- `POST /api/v1/drivers/documents/`
- `GET /api/v1/drivers/documents/`
- `POST /api/v1/drivers/presence/online/`
- `POST /api/v1/drivers/presence/offline/`
- `POST /api/v1/drivers/presence/heartbeat/`

Staff review driver applications and documents through the operations surface.
Going online requires an approved driver role, driver profile, active vehicle,
and current required documents.

## Quotes and dispatch

- `POST /api/v1/trips/quotes/`
- `GET /api/v1/trips/offers/`
- `POST /api/v1/trips/offers/{id}/accept/`
- `POST /api/v1/trips/offers/{id}/reject/`

Quotes contain server-derived route distance, duration, fare, and expiry.
Creating a trip consumes a valid quote. Drivers receive individual expiring
offers; unassigned trips are not globally listed.

## Trips

- `POST /api/v1/trips/` — customer requests a trip.
- `GET /api/v1/trips/` — participant’s trips.
- `GET /api/v1/trips/{id}/` — customer or assigned driver.
- `POST /api/v1/trips/{id}/start/` — assigned driver with rider PIN.
- `POST /api/v1/trips/{id}/arrived/` — assigned driver arrival signal.
- `POST /api/v1/trips/{id}/complete/` — assigned driver.
- `POST /api/v1/trips/{id}/cancel/` — customer or assigned driver.

The server controls customer, driver, fare, and status fields. Clients cannot
force state transitions by posting arbitrary status values.

## Wallets, verification, ratings, notifications

Existing endpoints remain under:

- `/api/v1/wallets/`
- `/api/v1/verification/`
- `/api/v1/ratings/`
- `/api/v1/notifications/`

Detailed request/response schemas will be generated from OpenAPI when the
mobility contract stabilizes.

## Payments

- `POST /api/v1/payments/mpesa/stk/` requires `Idempotency-Key`.
- `GET /api/v1/payments/intents/{public_id}/`
- M-Pesa callbacks are documented in `docs/PAYMENTS.md`.

## Real-time

The versioned `/ws/v1/` envelope, event catalogue, authentication, close codes,
and retry semantics are documented in `docs/REALTIME.md`.
