# Development Guide

## Setup

1. Create and activate a Python 3.13 virtual environment.
2. Install `pip install -r requirements-dev.txt`.
3. Copy `.env.example` to `.env` and set a development secret.
4. Run `python manage.py migrate`.
5. Run `python manage.py createsuperuser`.
6. Start with `python manage.py runserver`.

SQLite is the zero-configuration development default. Set `DATABASE_URL` to a
PostgreSQL URL for integration and production-like testing.

`SMS_BACKEND=console` logs development OTP messages. It must be replaced by a
real SMS provider adapter before staging. `ROUTING_API_URL` accepts an
OSRM-compatible base URL; when absent, development quotes use a clearly labelled
Haversine estimate. `REDIS_URL` enables the production channel layer.

Driver clients should send a heartbeat at least every 20 seconds. Run
`python manage.py expire_driver_heartbeats` every 15–30 seconds through the
production scheduler so connections older than 45 seconds become offline.

Run `python manage.py publish_outbox` continuously or on a short scheduler
interval as a recovery publisher. Production Channels requires `REDIS_URL`.

M-Pesa sandbox variables are listed in `.env.example`. The STK endpoint returns
503 until all required credentials and callback URL are configured.

## Quality commands

```text
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test
ruff check .
```

## Definition of done

- Acceptance criteria and permissions are explicit.
- State changes live in domain services.
- Migrations are included.
- Success, authorization, validation, and concurrency behavior are tested.
- Secrets and personal data are not logged or committed.
- Documentation changes with behavior.
