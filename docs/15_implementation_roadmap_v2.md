# Implementation Roadmap v2

This roadmap starts from PR-19 and focuses on closing industrial product completeness gaps without changing the safety boundary. Future work must remain read-only, deterministic, evidence-based, tenant-scoped, and human-in-the-loop.

## Completed Implementation PRs

### PR-20 Backend Sidebar Module APIs - Completed

Summary:
Added backend list/detail APIs required by visible sidebar modules.

Implemented scope:

- `GET /api/v1/equipment`
- `GET /api/v1/equipment/{equipment_id}`
- `GET /api/v1/incidents`
- `GET /api/v1/incidents/{incident_id}`
- `GET /api/v1/checklist-runs`
- `GET /api/v1/report-drafts`
- `GET /api/v1/approvals`
- `GET /api/v1/system/safety-settings`
- OpenAPI updates
- pytest coverage

Acceptance result:
Backend contracts exist for sidebar modules and remain read-only.

### PR-21 Frontend Sidebar Module Completion - Completed

Summary:
Implemented visible sidebar hub pages so operational users do not hit missing module routes.

Implemented routes:

- `/equipment`
- `/active-incidents`
- `/checklists`
- `/approvals`
- `/settings`

Acceptance result:
Visible navigation routes exist and map to real product modules.

### PR-22 Navigation / Contract / E2E Hardening - Completed

Summary:
Added browser smoke coverage for visible sidebar routes and representative workflow IDs.

Implemented scope:

- visible sidebar navigation smoke test
- direct route no-404 coverage
- representative ID visibility checks
- OpenAPI path coverage checks
- stable sidebar selectors

Acceptance result:
GitHub Actions Playwright is the source of truth for browser validation because local WSL Ubuntu 26.04 browser execution is constrained in this environment.

### PR-23 Read-Only Equipment Data Adapter - Completed

Summary:
Introduced inbound telemetry ingestion for equipment-originated diagnostic evidence.

Implemented scope:

- alarm event ingestion
- I/O snapshot ingestion
- EtherCAT status snapshot ingestion
- read-only adapter service
- unsafe command-like intent rejection
- audit events for successful and blocked ingestion
- OpenAPI, schema, migration, and pytest coverage

Acceptance result:
Telemetry records can be stored in FabMind while preserving the no equipment-control boundary.

### PR-24 Incident Lifecycle / Case Management - Completed

Summary:
Converted incidents from a derived read model into a first-class operational case entity.

Implemented scope:

- `equipment_incidents` table/model/schema
- incident list/detail/create endpoints
- status transition endpoint
- link endpoint for diagnosis/checklist/report/approval context
- alarm-event-to-incident linking
- diagnosis-session-to-incident linking
- RBAC and audit coverage

Acceptance result:
Operational cases can link telemetry, diagnosis, checklist, report, approval, and audit records.

### PR-25 Performance / Reliability Hardening - Completed

Summary:
Hardened backend list behavior, request correlation, readiness, and query support.

Implemented scope:

- pagination consistency on operational list endpoints
- safe limits and offsets
- additional indexes for implemented filters/sorts
- `X-Request-ID` middleware
- `/api/v1/health/ready`
- structured operational logging guardrails
- OpenAPI safety checks

Acceptance result:
Backend APIs have bounded list behavior and lightweight readiness/correlation support.

### PR-26 Frontend API Contract Tightening / Fallback Reduction - Completed

Summary:
Tightened frontend API usage so pages distinguish live backend data from degraded reference state.

Implemented scope:

- normalized paginated list response handling
- backend error preservation
- explicit backend-unavailable/degraded state on sidebar module pages
- read-only settings rendering
- audit payload rendering safety

Acceptance result:
Frontend pages no longer silently present reference data as live operational data.

### PR-27 RBAC / Approval Hardening - Completed

Summary:
Hardened report approval and incident lifecycle authorization across backend and frontend.

Implemented scope:

- field user report approve/reject denial
- senior/admin approve/reject success coverage
- senior-only incident transition denial for field users
- denial audit context
- current-user role parsing in frontend API helper
- conservative approval controls when role is unknown

Acceptance result:
Backend RBAC remains the enforcement source of truth, and frontend controls reflect authenticated role state conservatively.

## Current PR

### PR-28 System Acceptance / Release Candidate Audit - Current

Goal:
Audit implementation state against product requirements, traceability, quality gates, OpenAPI, DB schema, routes, and test coverage after PR-20 through PR-27.

Required scope:

- Refresh `docs/12_product_requirements_v1.md`
- Refresh `docs/13_module_traceability_matrix.md`
- Refresh `docs/14_industrial_quality_gate.md`
- Refresh this roadmap
- Add `docs/21_release_candidate_acceptance_audit.md`
- Add lightweight static acceptance checks where useful
- Verify product language and safety scans

Exit criteria:

- Backend pytest passes.
- Frontend typecheck/build pass.
- `git diff --check` passes.
- Product language scan has no matches.
- Safety phrase scan has no user-facing docs/UI matches.
- Acceptance document identifies known limitations without claiming final production readiness.

## Next Release Backlog

### PR-29 End-to-End Operational Flow Acceptance Test

Purpose:
Add an implementation-backed acceptance test for the full operational workflow across telemetry, incident, diagnosis, analysis, checklist, report, approval, and audit records.

Expected scope:

- backend API flow test for the golden operational path
- route-level frontend smoke linkage where practical
- acceptance fixture alignment with Load Port / FOUP Clamp / EtherCAT I/O
- no new product modules

### PR-30 Release Candidate v0.2.0 Packaging / Release Notes

Purpose:
Package the current release-candidate baseline with release notes and repeatable local execution guidance.

Expected scope:

- API container build
- web container build
- database migration execution path
- environment variable documentation
- health/readiness probe wiring
- release notes with scope, known limitations, rollback notes, and validation checklist

### PR-31 Observability / Incident Timeline Hardening

Purpose:
Improve operational traceability across incident lifecycle events.

Expected scope:

- incident timeline read model
- correlation ID propagation into audit/log views
- actor/date filters for audit console
- assignment and handoff metadata

### PR-32 Read-Only Real Equipment Connector Specification

Purpose:
Define the factory integration contract for inbound telemetry without creating equipment-control capability.

Expected scope:

- connector interface specification
- supported source systems and payload envelopes
- validation and rejection policy
- offline and replay ingestion considerations

### PR-33 Offline Factory Network Execution Mode

Purpose:
Document and validate execution in restricted factory networks.

Expected scope:

- no external runtime dependency check
- local deployment profile
- seed/reference data handling
- operational backup and restore guidance

## Roadmap Guardrails

- Keep the scope limited to Load Port / FOUP Clamp / EtherCAT I/O.
- Do not add broad semiconductor fault domains without a requirements update.
- Do not introduce equipment-control APIs or UI.
- Do not add external AI runtime dependency for deterministic analysis.
- Keep final report approval human-controlled.
- Preserve audit logging for sensitive actions and denials.
