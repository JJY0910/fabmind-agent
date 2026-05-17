# PR-25 Performance / Reliability Hardening

## Purpose

PR-25 tightens backend reliability for the production-oriented FabMind Agent workflow after telemetry ingestion and incident lifecycle expansion. The scope is operational hardening only: safer list queries, predictable request tracing, lightweight readiness checks, practical indexes, and contract safety checks.

## Pagination Policy

- List endpoints use bounded `limit` and non-negative `offset` parameters.
- Default `limit` is 50 for most operational lists. The I/O point catalog defaults to 100 to preserve the full seeded signal registry while remaining bounded.
- Maximum `limit` is 100 for standard lists and 200 for audit history.
- List responses should expose `items`, `total`, `limit`, and `offset` where practical.
- Stable ordering is required for paginated endpoints, using domain timestamps or deterministic identifiers.

## Indexing Policy

Indexes are added only for implemented filters and sort paths:

- tenant-scoped incident filtering by status, equipment, alarm code, severity, and updated/opened time
- checklist run filtering by tenant, status, and updated time
- report draft filtering by tenant, status, and updated time
- audit filtering by tenant, event type, severity, resource type, and creation time

The intent is query safety without excessive write overhead.

## Request Correlation

Every HTTP response includes `X-Request-ID`.

- If the client supplies `X-Request-ID`, the value is preserved.
- If the header is absent, the API generates a UUID.
- The value is attached to `request.state.request_id` for future structured logging and error response work.

## Error Handling Principles

- Invalid pagination parameters return validation errors.
- Invalid incident lifecycle transitions return clear 400 errors.
- Role-denied lifecycle actions return 403 errors.
- Unsafe inbound telemetry intent returns a safe rejection message without operational instructions.
- Error text must not describe machine actuation steps.

## Operational Logging Principles

Minimal structured logs are emitted for:

- telemetry ingestion success
- telemetry ingestion blocked by read-only guardrails
- incident creation
- incident status changes
- incident link events

Logs include identifiers and safe metadata only. Raw telemetry payloads are not logged.

## Readiness

`GET /api/v1/health/ready` verifies local database session availability and reports the read-only diagnostic boundary. It does not check equipment connectivity and does not call external systems.

## Safety Boundary

FabMind Agent remains read-only with respect to equipment. PR-25 does not add equipment actuation paths, external AI runtime dependencies, report export, or messaging integrations.

## Validation Expectations

Future hardening PRs should keep:

- backend pytest passing
- frontend typecheck and build passing
- OpenAPI paths aligned with implemented endpoints
- no unsafe equipment actuation paths in API contracts
- no unbounded list endpoints for operational data
