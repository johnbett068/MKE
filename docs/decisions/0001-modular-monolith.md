# ADR 0001: Modular monolith for the pilot

Status: accepted

MKE will remain one Django deployment during the pilot. Domain apps provide
ownership boundaries, but share a relational database and transactional service
layer. Extraction is considered only when independent scaling, reliability, or
team ownership produces measurable value.
