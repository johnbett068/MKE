# ADR 0002: Trip is the mobility aggregate root

Status: accepted

`Trip` is the authoritative lifecycle object. `Ride` is a one-to-one extension
for ride-specific coordinates and financial outcomes. `drivers.Driver` is the
authoritative driver presence record. The duplicate `DriverAvailability` model
is deprecated and will be removed after data migration.
