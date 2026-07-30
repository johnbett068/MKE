# Making Life Easier

Making Life Easier (MLE) is an Africa-first super-app platform for mobility,
delivery, local commerce, rentals, hospitality, jobs, and trusted errands.

The backend is a Django REST Framework modular monolith. The first supported
product milestone is a safe, operationally observable mobility pilot in Bomet,
Kenya. Broader modules are deliberately sequenced after the shared identity,
location, payments, verification, and fulfilment foundations are reliable.

## Documentation

- [Product roadmap](docs/PRODUCT_ROADMAP.md)
- [Architecture](docs/ARCHITECTURE.md)
- [API contract](docs/API.md)
- [UI foundations](docs/UI_FOUNDATIONS.md)
- [Real-time event contract](docs/REALTIME.md)
- [Payments and settlement](docs/PAYMENTS.md)
- [Development guide](docs/DEVELOPMENT.md)
- [Current engineering status](docs/STATUS.md)
- [Architecture decisions](docs/decisions/)

## Quick start

```text
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements-dev.txt
copy .env.example .env
python manage.py migrate
python manage.py runserver
```

The application uses SQLite by default for local development. Production and
integration environments should set `DATABASE_URL` to PostgreSQL.

## Status

Milestone 0, engineering foundation, is in progress. Shops, housing, jobs, and
marketplace are planned bounded contexts and should not yet be treated as
implemented products.
