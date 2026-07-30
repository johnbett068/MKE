# Engineering Status

Last updated: 2026-07-30

## v1.0 release candidate master inventory

### Architecture and financial core

- Django/DRF modular monolith with versioned `/api/v1/` boundaries, Channels
  ASGI real-time transport, and separate customer/driver Flutter clients.
- `Trip` is the authoritative mobility aggregate with explicit requested,
  accepted, in-progress, completed, and cancelled transitions. `Ride` holds
  ride-specific coordinates, PIN verification material, and financial results.
- `Driver` is the authoritative duty/presence record; approved driver accounts
  are connected to reviewed applications, documents, vehicles, and a
  driver-role wallet.
- Wallet operations use database transactions, row locks, positive-amount
  validation, immutable references, and idempotent service methods.
- Cash trips assess platform commission as driver wallet debt atomically with
  trip completion. Successful debt-payment callbacks reduce that debt once.

### Identity, onboarding, and security

- Customer registration provisions an account, profile, approved customer role,
  and wallet.
- Phone verification, phone login, and password recovery use hashed,
  purpose-bound, expiring, attempt-limited one-time codes behind an SMS adapter.
- JWT access/refresh authentication protects REST and WebSocket connections;
  production supports a signing secret independent from Django's secret key.
- Driver onboarding covers application submission, required identity/vehicle
  document uploads, staff approval/rejection comments, role activation, driver
  provisioning, vehicle management, and wallet creation.
- Ownership and role checks prevent customers or drivers from reading or
  commanding trips, offers, wallets, or streams that do not belong to them.
- Production settings enforce explicit hosts/origins, HTTPS forwarding, secure
  cookies, HSTS, TLS redirection, callback tokens, and fail-closed validation.

### Dispatch, routing, and geospatial behavior

- Mobile coordinates resolve to supported service areas before booking.
- Fare quotes use route distance and duration through an OSRM-compatible
  provider, have a five-minute price lock, and label the local fallback estimate
  when routing is unavailable.
- Online drivers publish authenticated GPS heartbeats; stale presence is expired
  by the maintenance worker. Redis is the production Channels transport.
- Dispatch creates private, driver-specific 30-second offers instead of exposing
  globally visible trips. Acceptance is atomic and competing offers are
  withdrawn; unanswered offers expire.
- Customers receive a deterministic four-digit ride-start PIN. Only the assigned
  driver can mark arrival, verify the PIN, start, complete, or cancel according
  to lifecycle rules.
- Cancellation records capture actor, reason, configurable customer fee windows,
  fee status, driver cancellation counts, and availability consequences.

### Real-time and payment engine

- Versioned WebSocket envelopes carry event IDs, occurrence times, aggregate
  identity, typed payloads, and schema version `1.0`.
- Owned `/ws/v1/drivers/me/` and participant-only `/ws/v1/trips/{id}/` streams
  deliver offers, lifecycle events, GPS updates, ETA information, acknowledgments,
  and authenticated driver commands.
- A transactional outbox records dispatch and lifecycle events in the same
  database transaction as domain changes. The outbox worker retries unpublished
  events and provides at-least-once delivery.
- Provider-neutral payment intents support request idempotency, provider
  references, callback deduplication, exact-amount validation, failure states,
  wallet top-ups, and commission-debt settlement.
- M-Pesa STK Push initiation and callback settlement are implemented. C2B
  validation/confirmation and B2C result endpoints durably ingest hooks; their
  final reconciliation/disbursement policies remain intentionally gated.

### Mobile applications and shared packages

- `mle_ui` defines the orange/blue design system, typography, controls, cards,
  inputs, and reusable brand elements.
- `mle_api` supplies secure token persistence, serialized token refresh,
  normalized API failures, DTO mappings, repositories, and reconnecting
  WebSocket infrastructure.
- The customer Riverpod workflow covers OTP login, map pickup/drop-off, service
  area resolution, quote/payment selection, price lock, booking, dispatch search,
  PIN display, live driver tracking, cancellation, completion, and rebooking.
- The driver Riverpod workflow covers OTP login, approval/document states,
  camera uploads, duty toggling, GPS heartbeat health, private offer countdown,
  accept/reject, arrival, PIN start, GPS-derived distance, completion, wallet
  debt, and M-Pesa top-up initiation.
- Native runner generation, Flutter analysis, Android APKs, and unsigned iOS
  runner bundles are automated in CI. Signed store releases remain a deployment
  responsibility.

### Operations and administration

- Django Admin exposes accounts, roles, drivers, applications, documents,
  vehicles, trips, offers, events, wallets, commissions, payment intents, and
  outbox records according to registered model surfaces.
- The staff-only `/operations/` dashboard presents driver/application/document
  approvals, live driver state, current trips, and booking visibility.
- `/health/` checks PostgreSQL and Redis for containers and load balancers.
- Management commands publish/watch the outbox, expire stale heartbeats and
  offers, run recurring maintenance, and validate production readiness.

### Production packaging, CI/CD, and verification

- A non-root, multi-stage backend image runs Daphne ASGI.
- Production Compose defines PostgreSQL/PostGIS, persistent Redis, Daphne,
  outbox and maintenance workers, TLS Nginx, shared static/media volumes, health
  gates, and an on-demand Certbot profile.
- Nginx terminates TLS, redirects HTTP, applies upload limits, forwards trusted
  proxy headers, and explicitly upgrades `/ws/v1/` WebSocket connections.
- `check_production_readiness` rejects missing credentials, development settings,
  unsafe hosts/origins, non-HTTPS providers, non-PostgreSQL databases, or missing
  PostGIS.
- `backend-ci.yml` runs Ruff, Django checks, migration drift, all backend tests,
  Compose rendering, and the production image build.
- `mobile-ci.yml` generates runners and analyzes both apps, then produces Android
  APK and unsigned iOS artifacts for `v*` release tags.
- Current local verification: Ruff passed; Django system checks passed; migration
  drift is clean; all **22/22 backend tests** passed; all 12 Dart source files
  passed formatter/parser validation.

## Completed in foundation milestone

- Replaced the incomplete README with product, architecture, API, development,
  and decision documentation.
- Added pinned runtime/development dependencies and environment-based settings.
- Added SQLite local development with PostgreSQL configuration through
  `DATABASE_URL`.
- Versioned the REST API under `/api/v1/`.
- Added account registration that creates profile, customer role, and wallet.
- Added role approval status and seeded platform roles.
- Made `Trip` the mobility aggregate and `Driver` the presence source of truth.
- Replaced unrestricted trip updates with authorized lifecycle commands.
- Rebuilt pricing calculation.
- Added row-locked, validated, idempotent wallet operations.
- Added cash commission debt settlement for completed trips.
- Secured WebSocket connections with JWT and participant/owner checks.
- Added initial automated tests and static analysis.
- Added a CI workflow for linting, Django checks, migration drift, and tests.
- Defined the orange-and-blue visual identity, UI tokens, accessibility rules,
  and core screen composition.

## Completed in mobility onboarding and dispatch milestone

- Added hashed, expiring, attempt-limited phone verification and password-reset
  codes behind an SMS provider boundary.
- Added driver applications, required document review, approval provisioning,
  vehicle management, driver role activation, and driver wallets.
- Added authenticated online, offline, and heartbeat APIs plus an expiry command.
- Added route-derived five-minute fare quotes with an OSRM provider boundary and
  a labelled local estimate fallback.
- Replaced globally visible trips with driver-specific 30-second offers.
- Added atomic offer acceptance and automatic withdrawal of competing offers.
- Added a customer-visible four-digit ride-start PIN and driver verification.
- Added cancellation records, configurable free windows, rider fees, and driver
  cancellation counters.
- Added orange-and-blue Flutter source foundations for separate customer and
  driver applications.
- Added a staff-only operations dashboard at `/operations/` for live trip,
  driver, application, document, and bookings visibility.

## Completed in real-time and mobile integration milestone

- Versioned all real-time messages with stable IDs, timestamps, aggregate
  identity, typed data, and schema version `1.0`.
- Moved WebSockets to owned `/ws/v1/drivers/me/` and participant-protected
  `/ws/v1/trips/{id}/` streams with JWT upgrade authentication.
- Added durable transactional outbox delivery for dispatch and lifecycle events.
- Added ephemeral validated driver GPS streaming, acknowledgements, and trip ETA
  propagation.
- Added `offer_received`, `driver_accepted`, `driver_arrived`, `trip_started`,
  `trip_completed`, and `trip_cancelled` event contracts.
- Added a shared Dart package with secure token persistence, serialized JWT
  refresh, normalized API failures, DTOs, repositories, and reconnecting
  WebSockets.
- Added Riverpod dependency containers to both Flutter applications.
- Added provider-neutral payment intents and M-Pesa STK, C2B, and B2C hook
  boundaries.
- Added account-scoped request idempotency, provider-event deduplication, callback
  amount verification, wallet top-ups, and cash-debt settlement.

## Completed in mobile workflows and system integration milestone

- Added phone-number login OTP endpoints that issue refresh/access JWTs after
  successful verification.
- Added coordinate-to-service-area resolution so mobile map selections are
  normalized to supported backend locations before quoting.
- Added authenticated driver WebSocket commands for accepting/rejecting offers,
  arrival, PIN-verified trip start, and trip completion.
- Built the customer Riverpod workflow for authentication, Google Map pickup and
  destination selection, fare lock/payment selection, booking/dispatch, customer
  PIN display, live driver tracking, cancellation, and completion.
- Built the driver Riverpod workflow for authentication, approval/document
  status, camera uploads, GPS duty heartbeat, private 30-second offer countdowns,
  arrival/PIN/start/complete controls, GPS-derived trip distance, wallet debt,
  and M-Pesa top-up initiation.
- Added a full multi-user integration test that creates a quote and trip through
  REST, delivers and accepts the private offer over WebSocket, completes the
  PIN-protected trip, assesses commission debt atomically, and settles that debt
  through an idempotent simulated M-Pesa STK callback.
- Verification on 2026-07-30: Django system checks and migration-drift checks
  pass; the current 22-test suite includes the full lifecycle E2E scenario.
  All 12 Dart source files pass the SDK formatter/parser. Flutter dependency
  bootstrap is still blocked by a non-responsive `flutter_tools` pub bootstrap
  on this Windows host, so package analysis and device builds remain pending.

## Completed in production packaging and release automation milestone

- Added a non-root, multi-stage production image running Daphne ASGI.
- Added a health-gated production Compose topology for PostgreSQL/PostGIS,
  persistent Redis, Daphne, the durable outbox worker, mobility maintenance,
  Nginx, and on-demand Certbot.
- Added TLS-only Nginx routing with explicit `/ws/v1/` upgrade handling,
  forwarded-protocol headers, upload limits, and static/media mounts.
- Added continuous outbox publishing plus explicit stale-heartbeat and
  dispatch-offer expiry worker commands.
- Added `/health/` database/Redis readiness checks for containers and load
  balancers.
- Added production security settings for independent JWT signing, trusted
  origins, forwarded TLS, HSTS, and HTTPS redirects.
- Added a generic authenticated HTTP SMS provider adapter while retaining the
  console adapter for development.
- Added `check_production_readiness`, which fails closed on missing secrets,
  unsafe hosts/origins, non-HTTPS providers, non-PostgreSQL databases, or absent
  PostGIS.
- Replaced the original CI file with backend quality/image packaging and mobile
  analysis/release-artifact workflows.
- Added the production environment template and complete deployment, M-Pesa,
  OSRM, backup, rollback, observability, and Android field-test guide.
- Verification on 2026-07-30: Ruff, Django system checks, migration drift, all
  22 backend tests, and formatting/parsing of all 12 Dart source files pass.

## Known intentional limitations

- Production SMS, M-Pesa, routing, maps, and mobile signing credentials remain
  deployment secrets and have not been exercised against live providers.
- Live M-Pesa credentials, Google sign-in, and email recovery are not connected.
- Turn-by-turn navigation, support incidents, emergency workflows, and refunds
  are not implemented.
- Mobile event-ID deduplication is not yet persisted across application restarts.
- The pilot ledger is not yet a complete double-entry accounting journal.
- `DriverAvailability` remains as a deprecated compatibility table pending a
  data-removal migration.
- Shops, housing, jobs, and marketplace remain scaffolds.
- Native Flutter runners and device builds require successful Flutter toolchain
  bootstrap plus Android/iOS signing and map-key configuration; CI now owns
  runner generation and release builds, but its first remote run is still a
  release gate.
- C2B/B2C callbacks are durably ingested but do not settle balances until their
  reconciliation and disbursement policies are approved.
- Durable events currently provide at-least-once delivery; mobile consumers must
  deduplicate by event ID.

## Release status

The repository is a **v1.0 release candidate**, not yet a live-production
release.

### External services to configure

1. Create separate Safaricom Daraja sandbox and production applications; install
   approved STK credentials, shortcode/passkey, callback gateway, and callback
   token. C2B/B2C must remain disabled until settlement policy is approved.
2. Connect an HTTPS SMS provider endpoint, API key, and approved sender ID; test
   login, verification, password reset, expiry, retry, and delivery failure.
3. Host a monitored OSRM Kenya/pilot-area dataset behind HTTPS and configure
   `ROUTING_API_URL`; measure route accuracy, latency, and fallback frequency.
4. Provision restricted Google Maps keys for the signed Android/iOS application
   identities and configure production API/WebSocket URLs.
5. Provision production DNS, TLS certificates, PostgreSQL/PostGIS, Redis,
   encrypted media storage/backups, and centralized logs/alerts.

### Pre-flight verification

1. Use Git Credential Manager or SSH, create the reviewed RC commit, and push the
   immutable release candidate without embedding credentials in remote URLs.
2. Require green first runs of `backend-ci.yml` and `mobile-ci.yml`; inspect the
   Docker build, Flutter analysis, APK, and iOS artifact outputs.
3. Deploy the immutable release tag to staging and run:
   `python manage.py check --deploy` and
   `python manage.py check_production_readiness`.
4. Install signed customer and driver APKs on representative physical devices.
   Exercise permissions, background/foreground behavior, weak data, reconnects,
   duplicate events, GPS loss, OTP expiry, offer TTL, wrong PIN, cancellation,
   completion, and delayed/duplicate payment callbacks.
5. Run the full customer-to-driver cash and M-Pesa journeys against sandbox
   services, reconciling Trip, Ride, Wallet, PaymentIntent, webhook, and
   commission records.
6. Prove backup restoration, migration rollback strategy, container restart,
   Redis/PostgreSQL recovery, outbox backlog recovery, and certificate renewal.

### Operational prerequisites for accepting live rides

1. Assign named owners and escalation paths for dispatch operations, driver
   approvals, payment reconciliation, customer support, safety incidents,
   infrastructure, privacy, and provider outages.
2. Approve cash handling, commission collection, refunds, failed/late M-Pesa
   payments, C2B/B2C reconciliation, and driver suspension procedures.
3. Publish customer/driver terms, privacy notice, document-retention schedule,
   emergency/support contacts, and consent language reviewed for the launch
   jurisdiction.
4. Configure dashboards and alerts for health checks, HTTP 5xx, WebSocket
   disconnects, stale drivers, unpublished outbox age, payment failures, callback
   anomalies, database capacity, backups, and certificate expiry.
5. Seed and independently review service areas, prices, commissions,
   cancellation configuration, operations accounts, and least-privilege access.
6. Complete load, security, accessibility, battery, poor-network, and pilot
   acceptance testing with documented go/no-go sign-off.

### Promotion gates

1. Green first runs of `backend-ci.yml` and `mobile-ci.yml`.
2. A staging deployment where both production readiness commands pass.
3. Signed Android builds with restricted map keys and physical-device testing.
4. SMS and M-Pesa sandbox certification, including delayed/duplicate callbacks.
5. A hosted OSRM dataset and measured route/fallback behavior in the pilot area.
6. Backup restoration, rollback, reconnect, load, battery, accessibility, and
   poor-network exercises.
7. Approved incident response, emergency support, privacy, document retention,
   and C2B/B2C settlement procedures.
