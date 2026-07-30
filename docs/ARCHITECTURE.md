# System Architecture

## Current architecture

MKE is a Django modular monolith. This is intentional for the pilot: shared
transactions, one deployment, and fast iteration are more valuable than early
microservices. Module boundaries must still be enforced so domains can be
extracted later when scale or team ownership requires it.

## Domain ownership

| Domain | Owns | Must not own |
| --- | --- | --- |
| accounts | identity, roles, profiles | trip state, balances |
| core | normalized locations and shared primitives | service workflows |
| drivers | driver profile, presence, live location | customer trips |
| rides | trips, ride details, events, matching lifecycle | ledger mutation |
| pricing | quote rules and fare calculation | settlement |
| commissions | commission rules | wallet balances |
| wallets | wallets and immutable financial entries | trip transitions |
| verification | submitted evidence and review | role identity |
| notifications | durable in-app notifications | business decisions |
| ratings | post-service reputation | service authorization |
| payments | provider intents, callbacks, and reconciliation boundary | direct balance mutation |
| core events | versioned outbox and real-time delivery contract | domain decisions |

Shops, housing, jobs, and marketplace remain future bounded contexts until
their milestone begins.

## Authoritative mobility aggregate

`Trip` owns customer, assigned driver, vehicle, type, status, locations, quote,
distance, and timestamps. `Ride` is a one-to-one ride extension containing raw
coordinates and settlement results. `Driver` owns online/available presence and
the latest provider coordinates.

Allowed trip transitions:

```text
requested -> accepted -> in_progress -> completed
     |           |             |
     +-----------+-------------+-> cancelled
```

Transitions occur only through the ride service. Views never set status
directly. Acceptance locks the trip and driver rows to prevent two drivers from
accepting the same request.

## Financial invariants

- Amounts are positive decimals.
- A wallet row is locked before balance mutation.
- A `(wallet, service, reference_id, entry_kind)` operation is idempotent.
- Customer cash payment creates provider commission debt.
- Digital settlement debits the customer/platform source and credits the
  provider using one database transaction.
- Historical ledger entries are never edited or deleted through public APIs.

The current ledger is a pragmatic pilot ledger. Before real-money launch it
must become a balanced double-entry journal with payment-provider reconciliation.

## API and security

- REST endpoints live under `/api/v1/`.
- JWT authenticates HTTP clients.
- Object-level permissions restrict trips to their customer or assigned driver.
- Driver actions require an active approved driver role and profile.
- Administrative verification review requires staff status.
- WebSockets must authenticate JWT clients and verify ride/driver ownership
  before accepting a connection.
- Rate limiting and audit events are required before public launch.

## Real-time consistency

Dispatch offers and lifecycle events use a transactional outbox. The domain
transaction writes both state and the event record; an on-commit fast path
publishes through Channels, while a retry worker drains pending events. Delivery
is at least once and clients deduplicate by event ID.

Driver GPS events are ephemeral and use the same versioned envelope without
entering the relational outbox. The latest driver position remains in the driver
presence record.

## Payment boundary

Payment provider adapters create and update `PaymentIntent` records. Views and
provider payloads cannot alter wallets directly. Successful, deduplicated
callbacks invoke transactional settlement services, which create wallet ledger
entries and update the intent atomically.

## Deployment direction

Development may use SQLite and the in-memory channel layer. Staging and
production require PostgreSQL, Redis, object storage, HTTPS, background workers,
centralized logs, error reporting, backups, and secret management.

## Architectural decision records

Material decisions should be added to `docs/decisions/` before implementation.
Decisions may be superseded, but history should remain visible.
