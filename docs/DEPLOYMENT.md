# MKE Production Deployment and Field Operations

This guide promotes the MKE v1.0 release candidate through staging and into a
single-host production deployment. Treat staging as mandatory: complete the
payment, routing, reconnect, and physical-device checks there before processing
real customer trips.

## 1. Production topology

`docker-compose.prod.yml` runs:

- `web`: Daphne ASGI serving REST, operations pages, and WebSockets;
- `outbox`: continuously publishes committed real-time outbox events;
- `maintenance`: expires stale driver heartbeats and dispatch offers;
- `db`: PostgreSQL 17 with PostGIS and `btree_gist`;
- `redis`: persistent Channels transport with a no-eviction policy;
- `nginx`: TLS termination, static/media delivery, and WebSocket proxying; and
- `certbot`: an on-demand certificate bootstrap/renewal profile.

The database and Redis are private to the Docker network. Only Nginx exposes
ports 80 and 443. The current `Location` model stores decimal coordinates;
PostGIS is enabled now so a later GeoDjango migration can introduce real
geography columns and GiST indexes without replacing the production database.

## 2. Host preparation

Use a supported 64-bit Linux server with Docker Engine, Docker Compose v2, DNS,
and at least 4 GB RAM for an initial pilot.

1. Point the production API domain, for example `api.mke.example`, to the host.
2. Allow inbound TCP 80 and 443. Do not expose PostgreSQL or Redis.
3. Clone the repository and check out an immutable release tag.
4. Copy the production template:

   ```bash
   cp .env.production.example .env.production
   chmod 600 .env.production
   ```

5. Replace every placeholder. Generate independent Django, JWT, database, and
   callback secrets with a cryptographically secure password generator.
6. Never commit `.env.production`, certificates, signing keys, or service-account
   files.

All Compose commands below must include:

```bash
docker compose --env-file .env.production -f docker-compose.prod.yml
```

For brevity, this guide refers to that prefix as `docker compose ...`.

## 3. TLS certificate bootstrap

Nginx intentionally refuses to start without a real certificate.

```bash
docker compose ... up -d db redis web
docker compose ... --profile certificate run --rm --service-ports certbot \
  certonly --standalone \
  --domain api.mke.example \
  --email operations@mke.example \
  --agree-tos --no-eff-email
docker compose ... up -d
```

Replace the domain and email. For renewal, stop Nginx briefly, run
`certbot renew` through the same profile, and restart Nginx. A load balancer or
managed certificate service may replace this flow, but it must preserve
`X-Forwarded-Proto` and WebSocket upgrade headers.

## 4. First deployment

Validate the rendered Compose model before starting:

```bash
docker compose ... config --quiet
docker compose ... build
docker compose ... up -d
docker compose ... ps
```

The web entrypoint applies migrations and collects static files. After it becomes
healthy, run both Django's deployment checks and MKE's stricter validator:

```bash
docker compose ... exec web python manage.py check --deploy
docker compose ... exec web python manage.py check_production_readiness
```

The second command verifies production secrets and hosts, PostgreSQL/PostGIS,
Redis configuration, HTTPS endpoints, HSTS, SMS credentials, OSRM, and M-Pesa.
It exits non-zero on any missing or unsafe setting.

Create the initial administrator interactively:

```bash
docker compose ... exec web python manage.py createsuperuser
```

Then sign in at `/admin/`, seed supported `Location`, `PricingRule`, and
`CommissionRule` records, and verify `/operations/`. Do not create administrators
through a committed data migration.

Smoke-test:

```bash
curl --fail https://api.mke.example/health/
docker compose ... logs --tail=100 web outbox maintenance nginx
```

## 5. Safaricom M-Pesa

Use the official [Safaricom Daraja Developer Portal](https://developer.safaricom.co.ke/).

1. Create an organization/individual account and a sandbox application.
2. Enable the products required for the pilot: Lipa Na M-Pesa Online/STK Push,
   and only the C2B/B2C products whose business approval has been completed.
3. Store the consumer key, consumer secret, shortcode, and STK passkey in
   `.env.production`.
4. Set `MPESA_BASE_URL` to the sandbox URL during staging and the production URL
   only after Safaricom go-live approval.
5. Register the public callback:

   `https://api.mke.example/api/v1/payments/webhooks/mpesa/stk/`

6. Configure the gateway/proxy to add `X-MKE-Callback-Token` with the exact
   `MPESA_CALLBACK_TOKEN`. Safaricom cannot add this private header directly, so
   production should use a narrowly scoped callback gateway or remove this
   requirement only after implementing and verifying Safaricom IP/signature
   validation.
7. Run sandbox payments for success, cancellation, timeout, duplicate callback,
   and wrong-amount cases. Confirm one `PaymentWebhookEvent`, one ledger effect,
   and the expected `PaymentIntent` state.
8. Re-run `check_production_readiness` after changing credentials.

Never log access tokens, passkeys, full callback payload PII, or customer PINs.

## 6. OSRM routing

MKE expects an OSRM-compatible route endpoint in `ROUTING_API_URL`. Follow the
current [OSRM server documentation](https://project-osrm.org/docs/) and pin a
reviewed OSRM image version in your infrastructure repository.

For a Kenya extract using the MLD pipeline:

```bash
docker run --rm -t -v "$PWD/osrm-data:/data" <OSRM_IMAGE> \
  osrm-extract -p /opt/car.lua /data/kenya-latest.osm.pbf
docker run --rm -t -v "$PWD/osrm-data:/data" <OSRM_IMAGE> \
  osrm-partition /data/kenya-latest.osrm
docker run --rm -t -v "$PWD/osrm-data:/data" <OSRM_IMAGE> \
  osrm-customize /data/kenya-latest.osrm
docker run -d --name mke-osrm --restart unless-stopped \
  -v "$PWD/osrm-data:/data:ro" <OSRM_IMAGE> \
  osrm-routed --algorithm mld /data/kenya-latest.osrm
```

Place OSRM behind an internal HTTPS proxy, monitor latency/error rate, and update
OpenStreetMap data on a tested schedule. Verify a Bomet route through OSRM before
enabling bookings. The backend labels and uses its local estimate fallback when
the routing provider is unavailable; operations should alert on fallback usage.

## 7. Database, backup, and rollback

Before every release:

```bash
docker compose ... exec db pg_dump -U "$POSTGRES_USER" -Fc "$POSTGRES_DB" \
  > "mke-$(date +%F-%H%M).dump"
docker compose ... exec web python manage.py migrate --plan
```

Store encrypted backups outside the host and test restoration. Deploy a release
tag, run migrations, then verify health and one synthetic booking. Application
rollback means redeploying the prior image tag. Database rollback requires a
reviewed reverse migration or restore; never run destructive migration reversal
blindly.

## 8. Observability and operations

- Ship container logs to durable centralized storage.
- Alert on `/health/`, HTTP 5xx, WebSocket disconnect rate, Redis/PostgreSQL
  health, unpublished outbox age, callback failures, and stale online drivers.
- Keep host time synchronized; offer TTLs, OTPs, JWTs, and callbacks depend on it.
- Rotate secrets and administrator credentials on a schedule.
- Scale Daphne horizontally only with Redis enabled. Run exactly one outbox
  worker until row-leasing is added; delivery remains intentionally at-least-once
  and mobile clients must deduplicate by event ID.
- Keep media backups and apply a retention policy to driver identity documents.

## 9. Android field builds

Install the current stable Flutter SDK, Android Studio/SDK, Java, and an Android
device with USB debugging. From each application:

```bash
cd mobile/customer_app
flutter create --platforms=android .
flutter pub get
flutter analyze --fatal-infos
flutter build apk --release \
  --dart-define=MKE_API_URL=https://api.mke.example \
  --dart-define=MKE_WS_URL=wss://api.mke.example
```

Repeat from `mobile/driver_app`. Follow Flutter's official
[Android release guide](https://docs.flutter.dev/deployment/android) to create
and protect the upload keystore and configure release signing. Configure the
Google Maps Android key in the generated runner, restrict it by package name and
signing certificate, and do not use an unrestricted key.

Install on a connected test device:

```bash
adb install -r build/app/outputs/flutter-apk/app-release.apk
```

Field validation must cover:

- denied/limited location permission and GPS loss;
- OTP resend and expiry;
- online/offline heartbeat under weak mobile data;
- offer countdown, reconnect, and duplicate delivery;
- pickup arrival and wrong/correct PIN;
- background/foreground transitions during a trip;
- M-Pesa success, cancellation, timeout, and delayed callback;
- battery usage, map rendering, accessibility, and emergency support paths.

The release workflow produces unsigned iOS runner bundles. App Store artifacts
still require Apple signing identities, provisioning profiles, protected GitHub
secrets, and an approved release process.

## 10. CI/CD release process

`backend-ci.yml` runs Ruff, Django checks, migration drift, all backend tests,
Compose rendering, and a production image build.

`mobile-ci.yml` generates native runners and analyzes both apps on changes.
Pushing a signed `v*` tag additionally creates Android APK and unsigned iOS
runner artifacts. Configure repository variables:

- `MKE_API_URL=https://api.mke.example`
- `MKE_WS_URL=wss://api.mke.example`

Release checklist:

1. Green backend and mobile workflows.
2. Reviewed migration plan and recent restorable backup.
3. Staging E2E and physical-device field test signed off.
4. `check --deploy` and `check_production_readiness` pass.
5. Tag an immutable release, deploy that image, and retain rollback artifacts.
