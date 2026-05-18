# Product Requirements v1

## 1. Product Mission

FabMind Agent is a production-oriented field-operations troubleshooting platform for semiconductor Load Port / FOUP Clamp / EtherCAT I/O workflows. It supports read-only diagnostics, evidence-based troubleshooting, deterministic rule analysis, checklist execution, human approval, incident lifecycle traceability, and auditability.

The product mission is to help field engineers and senior engineers make traceable troubleshooting decisions without introducing equipment-control risk.

## 2. Scope

In scope:

- Load Port operational troubleshooting
- FOUP Clamp sensor, door, presence, and interlock-related troubleshooting
- EtherCAT I/O state interpretation
- Tenant-scoped equipment registry and equipment knowledge
- Read-only alarm event, I/O snapshot, and EtherCAT status snapshot ingestion
- Active incident lifecycle case management
- Diagnosis sessions
- Deterministic agent analysis
- Inspection checklist execution
- Field notes tied to checklist work
- Deterministic report drafts
- Senior/admin approval workflow
- Audit console and audit events
- System safety settings visibility
- Requirements traceability and acceptance audit

## 3. Non-Goals

Out of scope:

- Real equipment control or machine-state changes
- External AI or LLM calls in runtime-critical analysis
- PDF export
- Email sending
- Broad semiconductor fault coverage outside Load Port / FOUP Clamp / EtherCAT I/O
- Claims of self-repair or unsupervised maintenance decisions

## 4. Safety Boundaries

- The platform is read-only with respect to equipment.
- The deterministic engine must not provide direct machine-control instructions.
- Risky action requests must be blocked or routed to senior/admin review.
- Reports must remain human-approved.
- Every diagnosis claim must be evidence-linked.
- Sensitive actions and denied permissions must be audit logged.
- Synthetic seed records must not be represented as real company data.

## 5. Equipment Domain

### Load Port

The system tracks equipment code, line/site association, family, operational status, alarm codes, I/O points, EtherCAT devices, telemetry snapshots, incidents, and related diagnosis sessions for Load Port troubleshooting.

### FOUP Clamp

The system focuses on clamp command/feedback mismatch, FOUP present state, door closed state, clamp done state, related sensor alignment signals, and interlock chain context.

### EtherCAT I/O

The system interprets expected device state, observed diagnosis snapshot state, read-only telemetry snapshots, slave state transition problems, and I/O signal mismatches. It remains read-only and does not attempt to transition equipment state.

## 6. Status Legend

- **Implemented**: The capability has backed implementation, route/API coverage, and tests.
- **Partially implemented**: A meaningful subset exists, but an expected workflow surface or model remains incomplete.
- **Needs hardening**: The capability works but requires stronger scale, observability, acceptance, or operational depth.
- **Future release**: The capability is intentionally deferred.

## 7. Requirement Catalog

### REQ-DASH-001 Dashboard Summary

Description:
Dashboard must summarize operational workload, including active diagnosis count, pending approvals, high-risk sessions, evidence-linked rate, open checklist count, report status counts, recent diagnosis sessions, required actions, and guardrail blocks.

User value:
Field operations can quickly identify work requiring attention.

Acceptance criteria:

- Dashboard route `/` renders without 404.
- Dashboard summary uses tenant-scoped data.
- Recent sessions include session ID, equipment code, alarm code, status, risk level, and created time.
- Required actions include approval queue items, blocked checklist items, high-risk sessions, and safety blocked agent runs when present.

Safety constraints:

- Dashboard must not present equipment-control actions.
- High-risk items must preserve human review boundary.

Current status:
Implemented / Needs hardening. Dashboard route and backend summary exist, with tenant-scoped queries and operational cards. Further work should deepen incident timeline visibility and production observability.

### REQ-EQP-001 Equipment Registry

Description:
Users must browse Load Port / FOUP Clamp equipment and inspect equipment knowledge data.

User value:
Field engineers can start troubleshooting from equipment context rather than scattered records.

Acceptance criteria:

- Route `/equipment` renders a real equipment list/hub page.
- Equipment list/detail APIs are tenant-scoped.
- Equipment detail exposes alarms, I/O points, and EtherCAT devices.
- List supports pagination, filtering, and stable sorting.

Safety constraints:

- Equipment pages are read-only.
- No equipment mutation or machine-state workflow is exposed.

Current status:
Implemented / Needs hardening. Backend list/detail APIs, OpenAPI coverage, frontend hub route, and contract-aware data handling exist. Future work should add richer equipment history and read-only connector metadata.

### REQ-INC-001 Active Incidents

Description:
Users must view active equipment troubleshooting incidents and their lifecycle state.

User value:
Operations teams can track open work across diagnosis, checklist, report, approval, and audit history.

Acceptance criteria:

- Route `/active-incidents` renders a real incident hub page.
- Incident lifecycle state is first-class and tenant-scoped.
- Incident rows link to diagnosis sessions, checklist runs, report drafts, approvals, alarm events, and audit history where available.
- Incident list supports pagination, filtering, and stable sorting.

Safety constraints:

- Incident state changes must not trigger equipment actions.
- Sensitive transitions must be RBAC-protected and audit logged.

Current status:
Implemented / Needs hardening. First-class incidents, lifecycle transitions, linking behavior, active incident hub page, and tests exist. Future work should add an incident timeline view and richer operational assignment handling.

### REQ-DIAG-001 Diagnosis Session

Description:
Users must create and review diagnosis sessions with equipment, alarm code, symptom summary, log excerpt, EtherCAT state, I/O snapshot, recent action, status, and risk level.

User value:
Troubleshooting begins from a standardized situation snapshot.

Acceptance criteria:

- Authenticated field/senior/admin users can create and read sessions.
- Unknown equipment or cross-tenant equipment is rejected.
- Session list/detail queries are tenant-scoped and paginated where applicable.
- Symptom summary is required.
- Diagnosis session creation can link to an active incident using deterministic rules.

Safety constraints:

- Input may describe risky requests, but output must remain advisory and safe.
- Cross-tenant access attempts must be denied and audit logged where feasible.

Current status:
Implemented / Needs hardening. Backend API, detail route, incident linking, audit coverage, and pagination hardening exist. Future work should add broader operational search filters.

### REQ-AGENT-001 Deterministic Agent Analysis

Description:
The agent engine must analyze diagnosis sessions using deterministic rules over alarm code, symptom summary, EtherCAT state, I/O snapshot, recent action, and log excerpt.

User value:
Engineers receive reproducible, evidence-linked hypotheses without external AI dependency.

Acceptance criteria:

- Clamp command true with clamp done false produces clamp sensor misalignment or sensor failure hypothesis.
- EtherCAT PRE_OP / SAFE_OP issues produce slave communication/state transition hypothesis.
- FOUP door/interlock symptoms produce door sensor or interlock chain hypothesis.
- Insufficient evidence returns insufficient evidence status.
- Risky action requests are blocked and audit logged.

Safety constraints:

- No external AI or LLM calls.
- No equipment-control instructions.
- No safety mechanism defeat guidance.

Current status:
Implemented / Needs hardening. Deterministic backend engine, evidence links, safety guardrails, and tests exist. Future work should broaden rule coverage while preserving deterministic behavior.

### REQ-CHK-001 Checklist Execution

Description:
Users must create checklist runs from completed agent analysis and update checklist item status and field notes.

User value:
Field inspection work becomes structured, traceable, and report-ready.

Acceptance criteria:

- Checklist runs are created from latest completed agent run inspection plan items.
- Missing analysis or missing inspection plan returns a clear error.
- Item status supports TODO, IN_PROGRESS, DONE, BLOCKED, SKIPPED.
- Run status updates to COMPLETED or BLOCKED based on item statuses.
- Route `/checklists` renders a list/hub page and detail route `/checklist-runs/[checklistRunId]` renders run detail.

Safety constraints:

- Checklist items must remain inspection-oriented and read-only.
- Blocked items must preserve escalation path.

Current status:
Implemented / Needs hardening. Backend create/list/detail/update APIs, frontend list/detail routes, field notes, and E2E smoke coverage exist. Future work should add incident timeline aggregation.

### REQ-NOTE-001 Field Notes

Description:
Users must record field notes during checklist execution and preserve them for report and audit traceability.

User value:
Observed field evidence is captured where inspection work happens.

Acceptance criteria:

- Checklist item updates accept `field_note`.
- Field notes appear in report draft inspection summary where relevant.
- Future incident model can aggregate notes by incident.

Safety constraints:

- Field notes are descriptive records only.
- Notes must not become equipment instructions.

Current status:
Partially implemented / Needs hardening. Checklist item field notes and report draft consumption exist. Dedicated incident-level notes and timeline aggregation remain future release work.

### REQ-RPT-001 Report Draft

Description:
Users must create deterministic report drafts from diagnosis session, agent run, evidence, and checklist results.

User value:
Troubleshooting conclusions become consistent, reviewable operational records.

Acceptance criteria:

- Report draft creation requires completed agent analysis.
- Report draft creation requires a completed or blocked checklist run.
- Draft content is deterministic.
- Report detail route renders report content and status.
- Report list API supports pagination and filtering.

Safety constraints:

- Report content must not include unsafe maintenance actions.
- Final report requires human approval before operational closure.

Current status:
Implemented / Needs hardening. Backend create/list/detail/submit APIs, deterministic content generation, report detail route, and approval integration exist. Future work should add export packaging only after a separate safety and records policy review.

### REQ-APR-001 Approval Workflow

Description:
Senior/admin users must approve or reject submitted report drafts with audit logging.

User value:
Final troubleshooting conclusions remain human-reviewed.

Acceptance criteria:

- Field users can submit but cannot approve/reject.
- Senior/admin users can approve/reject submitted reports.
- Rejection requires a comment.
- Route `/approvals` renders an approval queue.
- Frontend role gating is advisory; backend RBAC is the source of truth.

Safety constraints:

- Approval permission must be enforced by backend auth roles.
- Approval decisions and denials must be audit logged.

Current status:
Implemented / Needs hardening. Approval queue, report detail actions, auth/me role handling, backend RBAC, and denial audit tests exist. Future work should add broader reviewer assignment and notification policy without email sending.

### REQ-AUD-001 Audit Console

Description:
Senior/admin users must review tenant-scoped audit events with practical filters.

User value:
Operations can reconstruct sensitive actions, denied permissions, report decisions, guardrail events, and incident transitions.

Acceptance criteria:

- Route `/audit-events` renders without 404.
- API supports event type, severity, resource type, limit, and offset filters.
- Field users are denied audit console access.
- Audit console access and permission denial are logged where feasible.

Safety constraints:

- Audit history is tenant-scoped.
- Audit records must not expose secrets.

Current status:
Implemented / Needs hardening. Audit console route, backend filters, paginated response handling, RBAC, and tests exist. Future work should add retention policy, actor/date filters, and export governance.

### REQ-SET-001 System Safety Settings

Description:
Users must view system safety settings such as external AI disabled, equipment control disabled, audit enabled, and role visibility.

User value:
Operators and reviewers can verify the system boundary from the UI.

Acceptance criteria:

- Route `/settings` renders a real safety settings page.
- API exposes read-only safety settings.
- The page shows external AI disabled, equipment control disabled, audit enabled, deterministic engine enabled, and RBAC visibility.

Safety constraints:

- Settings page must not enable equipment-control behavior.
- Any future mutable safety policy requires a separate admin workflow and audit design.

Current status:
Implemented / Needs hardening. Read-only safety settings API and page exist. Future work should add policy version management and deployment environment attestation.

### REQ-TEL-001 Read-Only Equipment Telemetry Ingestion

Description:
The backend must ingest equipment-originated alarm events, I/O snapshots, and EtherCAT status snapshots as inbound telemetry only.

User value:
Operational evidence from equipment context can be persisted and linked to incidents and diagnosis sessions.

Acceptance criteria:

- Alarm event ingestion persists severity, status, timestamps, source system, and raw payload.
- I/O snapshot ingestion persists observed input and observed output states as telemetry.
- EtherCAT status snapshot ingestion persists master state, link status, working counter, and error context.
- POST ingestion is restricted to senior/admin roles.
- List endpoints are paginated, filterable, and tenant-scoped.

Safety constraints:

- The adapter must not expose an outbound equipment channel.
- Command-like intent fields are rejected and audit logged.

Current status:
Implemented / Needs hardening. PR-23 added models, migrations, service guardrails, APIs, OpenAPI coverage, and tests. Future work should specify real connector adapters for read-only factory network operation.

### REQ-LIFE-001 Incident Lifecycle Case Management

Description:
The system must represent incidents as first-class operational cases linking alarm events, diagnosis sessions, checklist runs, report drafts, approvals, and audit events.

User value:
Field operations can manage a complete troubleshooting case rather than isolated workflow records.

Acceptance criteria:

- Incident statuses are controlled and explicit.
- Active alarm events deterministically link to an existing active incident or create a new open incident.
- Diagnosis sessions link to an existing active incident where appropriate.
- Senior-only lifecycle transitions are enforced.
- Link operations validate resource existence and tenant boundaries.

Safety constraints:

- Incident lifecycle updates do not send equipment actions.
- Senior-only transitions and denied updates are audit logged.

Current status:
Implemented / Needs hardening. PR-24 added first-class incidents, status transitions, linking, telemetry integration, seed coverage, OpenAPI, and tests. Future work should add a richer timeline and assignment workflow.

### REQ-RBAC-001 RBAC and Approval Enforcement

Description:
RBAC must be enforced consistently across approval decisions, incident lifecycle transitions, audit console access, and sensitive workflow actions.

User value:
Field engineers can work safely while senior/admin users retain authority for final decisions.

Acceptance criteria:

- Field users cannot approve or reject reports.
- Senior/admin users can approve or reject reports.
- Field users cannot perform senior-only incident transitions.
- Denied actions create audit records with useful context.
- Frontend role state comes from authenticated user context where available.

Safety constraints:

- Frontend gating is advisory only.
- Backend authorization remains the enforcement source of truth.

Current status:
Implemented / Needs hardening. PR-27 hardened report approval RBAC, incident senior-only denial tests, auth/me parsing, and frontend approval controls. Future work should add centralized policy documentation in API schemas.

### REQ-OPS-001 Performance and Reliability

Description:
Operational APIs and pages must avoid unbounded list behavior and support predictable request correlation and readiness checks.

User value:
Operational teams can rely on stable list behavior, trace requests, and verify service readiness.

Acceptance criteria:

- List endpoints use bounded default and maximum limits.
- Negative offset is rejected or normalized consistently by endpoint policy.
- Stable sort order is defined for operational lists.
- Request responses include `X-Request-ID`.
- Readiness endpoint exists and avoids external dependencies.

Safety constraints:

- Logs must not include raw payloads or unsafe operational detail.
- Readiness checks must not contact equipment.

Current status:
Implemented / Needs hardening. PR-25 added pagination hardening, indexes, request correlation, readiness endpoint, logging guardrails, OpenAPI coverage, and tests. Future work should add production metrics and alerting.

### REQ-FEAPI-001 Frontend API Contract Handling

Description:
Frontend pages must consume backend API contracts predictably and must not silently present deterministic reference data as live operational data.

User value:
Users can distinguish live backend records, empty results, loading state, and backend-unavailable degraded state.

Acceptance criteria:

- List helpers normalize paginated `{ items, total, limit, offset }` responses.
- Malformed list payloads are not treated as valid operational data.
- Backend errors surface visibly.
- Reference data is clearly labeled as degraded/non-live.
- Settings remains read-only and does not render editable safety controls.

Safety constraints:

- Degraded state must not enable privileged approval actions.
- UI must not expose equipment-control controls.

Current status:
Implemented / Needs hardening. PR-26 tightened API helper behavior, sidebar module pages, audit payload rendering, and settings read-only state. Future work should add browser acceptance coverage for degraded mode.

### REQ-CONTRACT-001 Contract, Schema, and Acceptance Traceability

Description:
OpenAPI, DB schema, route files, and acceptance documentation must remain aligned with the implemented operational workflow.

User value:
Product, engineering, and operations reviewers can verify implementation-backed acceptance status without relying on undocumented assumptions.

Acceptance criteria:

- OpenAPI contains key implemented endpoints for equipment, incidents, checklists, report drafts, approvals, safety settings, read-only telemetry, and readiness.
- DB schema contains key operational tables for telemetry, incidents, reports, approvals, and audit events.
- Frontend route files exist for all visible operational routes.
- Static acceptance tests verify core OpenAPI, DB, route, and documentation coverage.
- Release candidate documentation lists known limitations without claiming final production readiness.

Safety constraints:

- Contract coverage must not introduce speculative or equipment-control endpoints.
- Schema acceptance must not imply real equipment deployment is complete.

Current status:
Implemented / Needs hardening. PR-28 adds static acceptance checks and living documentation updates. Future work should add generated OpenAPI drift checks and migration replay CI.

### REQ-SAFE-001 Industrial Safety Boundary

Description:
The system must enforce read-only diagnostics and block unsafe instruction wording.

User value:
FabMind Agent remains suitable for field-operations troubleshooting without unsafe escalation.

Acceptance criteria:

- No external AI/LLM runtime dependency for deterministic analysis.
- No equipment-control routes.
- Risky action requests are blocked.
- Safety blocked events are audit logged.
- User-facing docs/UI avoid unsafe instruction wording.

Safety constraints:

- The platform must not suggest machine-control commands or safety mechanism defeat.

Current status:
Implemented / Needs hardening. Backend guardrails, equipment-data ingestion validation, language scans, read-only settings, and quality gates exist. Future work should add automated user-facing safety phrase checks in CI.

### REQ-NAV-001 Navigation Completeness

Description:
All visible navigation items must resolve to real product modules or be removed until implemented.

User value:
Users should not hit dead-end routes during operational workflow.

Acceptance criteria:

- Sidebar route smoke test covers every visible navigation item.
- No visible navigation item returns 404.
- Route labels match product module names.
- Module routes align with traceability matrix.

Safety constraints:

- Navigation must not expose unsupported control or maintenance actions.

Current status:
Implemented / Needs hardening. PR-21 implemented sidebar hub routes, and PR-22 hardened navigation smoke coverage. Local WSL browser execution remains limited; GitHub Actions Playwright remains the browser validation source.
