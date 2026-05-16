# Incident Lifecycle Case Management

## Purpose

PR-24 introduces `equipment_incidents` as the first-class operational case entity for FabMind Agent. Incidents connect read-only equipment telemetry, diagnosis sessions, checklist execution, report drafts, approval decisions, and audit history into a single tenant-scoped workflow.

The incident lifecycle does not change the equipment safety boundary. It organizes operational evidence and human workflow state; it does not provide an equipment actuation path.

## Operational Case Entity

An incident records:

- equipment and alarm context,
- primary alarm event when available,
- linked diagnosis session, checklist run, report draft, and approval record,
- case number, title, summary, severity, owner, and assigned role,
- lifecycle timestamps for triage, checklist start, report submission, approval, and closure.

Existing diagnosis sessions remain evidence records. Incidents reference them instead of overwriting their diagnostic state.

## Status Lifecycle

Supported statuses:

- `OPEN`
- `TRIAGED`
- `CHECKLIST_IN_PROGRESS`
- `REPORT_SUBMITTED`
- `APPROVED`
- `CLOSED`
- `CANCELLED`

Field engineers may move work into triage or checklist execution. Senior engineers and admins may perform final lifecycle transitions such as approval and closure. Invalid transitions are rejected and sensitive denials are audit logged.

## Telemetry Linking

When a read-only alarm event is ingested, the backend deterministically links it to an active incident for the same equipment and alarm code. If no active incident exists, the backend opens a new `OPEN` incident. This keeps telemetry ingestion inbound-only while making the evidence visible to case management.

Diagnosis session creation also opens a linked incident so operational work can be tracked from the beginning of troubleshooting.

## Auditability

The incident workflow records audit events for:

- incident creation,
- lifecycle status changes,
- denied lifecycle updates,
- closure,
- links to diagnosis sessions, checklist runs, report drafts, approvals, and alarm events.

## Safety Boundary

Incident APIs are case-management APIs only. They do not expose machine actuation, machine recovery, safety defeat, motion, reset, or state-changing endpoints. Future operational monitoring should continue using inbound telemetry and evidence links while keeping equipment integration read-only.
