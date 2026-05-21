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

### PR-28 System Acceptance / Release Candidate Audit - Completed

Summary:
Audit implementation state against product requirements, traceability, quality gates, OpenAPI, DB schema, routes, and test coverage after PR-20 through PR-27.

Implemented scope:

- Refresh `docs/12_product_requirements_v1.md`
- Refresh `docs/13_module_traceability_matrix.md`
- Refresh `docs/14_industrial_quality_gate.md`
- Refresh this roadmap
- Add `docs/21_release_candidate_acceptance_audit.md`
- Add lightweight static acceptance checks where useful
- Verify product language and safety scans

Acceptance result:

System acceptance was documented as an operational acceptance baseline without a final deployment certification claim.

### PR-29 End-to-End Operational Flow Acceptance Test - Completed

Summary:
Add an implementation-backed acceptance test for the full operational workflow across telemetry, incident, diagnosis, analysis, checklist, report, approval, and audit records.

Implemented scope:

- backend API flow test for the golden operational path
- acceptance fixture alignment with Load Port / FOUP Clamp / EtherCAT I/O
- no new product modules
- acceptance note describing covered entities, audit events, RBAC expectations, and read-only boundary

Acceptance result:

Backend/TestClient operational flow acceptance connects telemetry, incident, diagnosis, checklist, report, approval, and audit records while preserving the read-only equipment boundary.

### PR-30 Release Candidate v0.2.0 Packaging / Release Notes - Current

Purpose:
Package the current release-candidate baseline with release notes and repeatable local execution guidance.

Expected scope:

- Add `docs/23_release_notes_v0_2_0.md`
- Add `docs/24_release_candidate_validation_runbook.md`
- Refresh README release-candidate status and validation links
- Refresh release-candidate acceptance audit with PR-29 and PR-30 status
- Add lightweight static release packaging checks
- Preserve runtime behavior, API contract, database schema, and frontend UI behavior

Exit criteria:

- PR-30 targeted backend packaging test passes.
- Full backend pytest passes.
- Frontend typecheck/build pass.
- `git diff --check` passes.
- Product language scan has no matches.
- Safety phrase scan has no user-facing docs/UI matches.
- Release notes document known limitations without a final deployment certification claim.

Acceptance result:

Release-candidate packaging, release notes, validation runbook, README links, roadmap/audit updates, and static packaging checks were completed without runtime behavior changes.

## Current PR

### PR-31 Deployment / Containerization - Current

Purpose:
Add local deployment/containerization support for the v0.2.0 release-candidate baseline without changing product workflow behavior.

Expected scope:

- Add root `docker-compose.yml` for PostgreSQL, API, and web services
- Add backend API Dockerfile
- Add frontend web Dockerfile
- Add non-secret root `.env.example`
- Add Docker ignore files for generated artifacts and local env files
- Add `docs/25_deployment_containerization.md`
- Refresh README, roadmap, release-candidate audit, and release notes
- Add lightweight static deployment packaging checks
- Preserve runtime behavior, API contract, database schema, and frontend UI behavior

Exit criteria:

- PR-31 targeted deployment packaging test passes.
- Full backend pytest passes.
- Frontend typecheck/build pass.
- `git diff --check` passes.
- Product language scan has no matches.
- Safety phrase scan has no user-facing docs/UI matches.
- `docker compose config` passes when Docker Compose is available.
- Documentation keeps local containerized execution distinct from final deployment certification.

## Next Release Backlog

### Observability / Incident Timeline Hardening

Purpose:
Improve operational traceability across incident lifecycle events.

Expected scope:

- incident timeline read model
- correlation ID propagation into audit/log views
- actor/date filters for audit console
- assignment and handoff metadata

### Read-Only Real Equipment Connector Specification

Purpose:
Define the factory integration contract for inbound telemetry without creating equipment-control capability.

Expected scope:

- connector interface specification
- supported source systems and payload envelopes
- validation and rejection policy
- offline and replay ingestion considerations

### Offline Factory Network Execution Mode

Purpose:
Document and validate execution in restricted factory networks.

Expected scope:

- no external runtime dependency check
- local deployment profile
- seed/reference data handling
- operational backup and restore guidance

### Browser Full Operational Flow Acceptance

Purpose:
Add browser-level coverage for the complete operational workflow after the current backend acceptance baseline.

Expected scope:

- authenticated browser workflow coverage
- incident-to-diagnosis-to-checklist-to-report navigation checks
- approval path confirmation
- audit trail visibility checks

### Migration Replay CI

Purpose:
Add CI coverage that validates schema migration replay in a fresh environment.

Expected scope:

- migration replay smoke job
- seed integrity confirmation after replay
- failure reporting for schema drift

## Roadmap Guardrails

- Keep the scope limited to Load Port / FOUP Clamp / EtherCAT I/O.
- Do not add broad semiconductor fault domains without a requirements update.
- Do not introduce equipment-control APIs or UI.
- Do not add external AI runtime dependency for deterministic analysis.
- Keep final report approval human-controlled.
- Preserve audit logging for sensitive actions and denials.
