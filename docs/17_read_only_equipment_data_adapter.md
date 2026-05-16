# Read-Only Equipment Data Adapter

## Purpose

PR-23 introduces an inbound telemetry adapter for equipment-originated snapshots. The adapter normalizes alarm events, I/O state observations, and EtherCAT status observations into FabMind Agent's tenant-scoped database so diagnosis and incident workflows can use recent operational evidence.

This adapter is read-only from the equipment perspective. It stores received telemetry; it does not provide an outbound channel to machines, controllers, or field devices.

## Supported Data Types

- Alarm events: alarm code, summary, severity, status, source event ID, occurrence time, source system, and optional raw payload.
- I/O snapshots: captured input states, observed output states, capture time, source system, and optional raw payload.
- EtherCAT status snapshots: master state, slave count, working counter, link status, optional error details, capture time, source system, and optional raw payload.

Observed output state is handled only as telemetry. Field names use `observed_outputs` to keep the boundary clear.

## Adapter Boundary

The `ReadOnlyEquipmentDataAdapter` is an inbound data path only:

- It resolves equipment within the authenticated user's tenant.
- It validates payloads for command-like intent fields.
- It persists normalized records.
- It writes audit events for successful ingestion and blocked unsafe payloads.

It does not expose methods for machine actuation, machine recovery, safety defeat, motion, reset, or state-changing requests.

## Validation Guardrails

Ingestion rejects payloads that place command-like intent in dedicated action/request fields such as requested action, desired state, machine operation, or maintenance instruction fields. Normal alarm text and raw telemetry descriptions may still be stored when they are observational rather than an instruction.

This keeps real equipment integration focused on evidence collection while preserving the industrial safety boundary.

## Future Integration Path

The adapter prepares PR-24 and later work by giving incident lifecycle and diagnosis workflows a durable source of:

- recent alarm events,
- current I/O observations,
- EtherCAT communication state,
- source system metadata,
- audit history for telemetry ingestion.

Future equipment connectors should call these ingestion endpoints with telemetry snapshots only. They must not add any equipment-control endpoint or outbound machine-control channel.
