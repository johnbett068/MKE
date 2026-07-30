# Real-Time Event Contract

## Transport

- Driver stream: `/ws/v1/drivers/me/`
- Trip stream: `/ws/v1/trips/{trip_id}/`
- Authentication: `Authorization: Bearer <access-token>` during the WebSocket
  upgrade.

The driver stream resolves identity from JWT and never accepts a driver ID from
the client. A trip stream accepts only the trip customer or assigned driver.

Close codes:

| Code | Meaning |
| --- | --- |
| 4401 | Authentication required or token invalid |
| 4403 | Authenticated account does not own the stream |
| 4409 | Driver must go online through the REST presence API first |

## Version 1 envelope

Every server message uses:

```json
{
  "schema_version": "1.0",
  "event_id": "77c65ae1-7ff5-4d55-8b54-92932620f494",
  "type": "trip_started",
  "occurred_at": "2026-07-30T12:00:00+03:00",
  "aggregate": {
    "type": "trip",
    "id": "42"
  },
  "data": {}
}
```

Clients must ignore unknown fields, reject unsupported major schema versions,
and deduplicate durable messages by `event_id`.

## Server event types

| Event | Stream | Durable |
| --- | --- | --- |
| `connection_ready` | driver/trip | No |
| `offer_received` | driver | Yes |
| `driver_accepted` | trip | Yes |
| `driver_arrived` | trip | Yes |
| `trip_started` | trip | Yes |
| `trip_completed` | trip | Yes |
| `trip_cancelled` | trip | Yes |
| `driver_location_updated` | trip | No |
| `driver_location_acknowledged` | driver | No |
| `protocol_error` | driver/trip | No |

Lifecycle and offer events are written to `EventOutbox` in the same database
transaction as domain state. Delivery is at least once. The on-commit publisher
handles the fast path; `python manage.py publish_outbox` retries pending events.

GPS samples are intentionally ephemeral. Persisting and replaying every sample
would overload the transactional database and is not required to recover the
current trip state.

## Driver messages

The driver stream accepts:

```json
{
  "schema_version": "1.0",
  "type": "driver_location_updated",
  "data": {
    "latitude": -0.781,
    "longitude": 35.342,
    "sequence": 12
  }
}
```

`driver_heartbeat` uses the same coordinate payload. The server validates
coordinate ranges, updates presence, acknowledges the sequence, and sends an
ETA-bearing `driver_location_updated` event to an active trip.
