# Making Life Easier Product Roadmap

## Product mission

Making Life Easier (MLE) is an Africa-first service platform that lets a person
request transport, delivery, shopping, accommodation, rentals, work, and other
trusted local services from one account.

The long-term interface is conversational: a user describes an outcome, MLE
turns it into a structured request, presents the price and important choices,
and acts only after explicit confirmation.

## Product principles

1. Trust before growth: providers, vehicles, merchants, and properties must be
   verifiable.
2. Cash is a first-class payment method, not an exception.
3. Every financial balance change must have an auditable ledger entry.
4. Every service request has an explicit state machine.
5. Location and identity data are private and available only to participants.
6. AI interprets and assists; it never silently commits money or invents facts.
7. Start town-by-town, measure operations, then expand.
8. Present one cohesive orange-and-blue design language across customer,
   provider, merchant, and operations products.

## Milestone 0 — Engineering foundation

Exit criteria:

- Reproducible local environment and CI checks.
- Environment-based secrets and database configuration.
- One account, role, driver, trip, wallet, and location model path.
- Versioned and permission-protected APIs.
- Tested trip state transitions and wallet settlement.
- Authenticated WebSockets with ride-participant authorization.
- Architecture and API documentation maintained with code.

## Milestone 1 — Bomet mobility pilot

Customer:

- Register, verify phone, set pickup/destination, receive a quote.
- Request, cancel, track, contact, and rate a ride.
- Pay cash initially; wallet and M-Pesa follow behind a controlled feature flag.

Driver:

- Apply for the driver role and submit identity, licence, and vehicle documents.
- Go online, receive offers, accept one offer atomically, navigate, start using a
  rider PIN, complete, and view earnings/debt.

Operations:

- Approve drivers, configure fares and commissions, monitor live trips, issue
  adjustments, handle incidents, and reconcile cash commission debt.

## Milestone 2 — Parcel delivery and errands

- Sender/recipient details and delivery instructions.
- Proof of pickup and proof of delivery.
- Package category, value, size, and restricted-item controls.
- Shop-and-deliver errands with spending limits and substitution rules.

## Milestone 3 — Merchant commerce

- Merchant and branch onboarding.
- Catalogues, availability, carts, orders, substitutions, and receipts.
- Merchant acceptance, courier fulfilment, refunds, and settlement.
- Initial supermarket partnerships use managed catalogues or merchant portals.

## Milestone 4 — Hospitality and property

- Guest-house inventory and short-stay bookings.
- Long-term rental listings, viewing requests, applications, and deposits.
- Separate booking and tenancy workflows; they must not share one ambiguous
  "rental" state machine.

## Milestone 5 — Jobs and marketplace

- Verified employers, job posts, applications, and moderation.
- Classified listings, messaging, safety prompts, and fraud reporting.

## Milestone 6 — Conversational assistant

The assistant pipeline is:

`utterance -> intent -> entities -> place/merchant resolution -> clarification
-> quote -> explicit confirmation -> service command -> status updates`

Example ride:

> Pick me up from my current location and take me to Equity Bank in Bomet.

Example shopping request:

> Buy two kilograms of sugar from Giftmart and bring it to my home.

Before execution the assistant must resolve ambiguity, show the destination or
items, disclose the estimated total, payment method, substitutions, and obtain
confirmation. All resulting commands use the same APIs as the mobile clients.

## Product measures

- Request-to-match time and match rate.
- Driver acceptance and cancellation rates.
- Pickup ETA accuracy.
- Completion and incident rates.
- Gross bookings, platform revenue, provider earnings, and cash debt.
- Repeat customers and retained providers.
- Support contacts and refund rate per completed service.
