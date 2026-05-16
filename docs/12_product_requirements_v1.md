# Product Requirements v1

## 1. Product Mission

FabMind Agent is a production-oriented field-operations troubleshooting platform for semiconductor Load Port / FOUP Clamp / EtherCAT I/O workflows. It supports read-only diagnostics, evidence-based troubleshooting, deterministic rule analysis, checklist execution, human approval, and auditability.

The product mission is to help field engineers and senior engineers make traceable troubleshooting decisions without introducing equipment-control risk.

## 2. Scope

In scope:

- Load Port operational troubleshooting
- FOUP Clamp sensor, door, presence, and interlock-related troubleshooting
- EtherCAT I/O state interpretation
- Tenant-scoped equipment knowledge
- Diagnosis sessions
- Deterministic agent analysis
- Inspection checklist execution
- Field notes tied to checklist work
- Deterministic report drafts
- Senior/admin approval workflow
- Audit console and audit events
- System safety settings visibility
- Requirements traceability

## 3. Non-Goals

Out of scope:

- Real equipment control
- PLC writes, motion commands, output forcing, or state-changing maintenance actions
- External AI or LLM calls in runtime-critical analysis
- PDF export
- Email sending
- Broad semiconductor fault coverage outside Load Port / FOUP Clamp / EtherCAT I/O
- Claims of self-repair or unsupervised maintenance decisions

## 4. Safety Boundaries

- The platform is read-only.
- The deterministic engine must not provide direct machine-control instructions.
- Risky action requests must be blocked or routed to senior/admin approval.
- Reports must remain human-approved.
- Every diagnosis claim must be evidence-linked.
- Sensitive actions and denied permissions must be audit logged.
- Synthetic data must not be represented as real company data.

## 5. Equipment Domain

### Load Port

The system tracks equipment code, line/site association, family, operational status, alarm codes, I/O points, and EtherCAT devices related to Load Port troubleshooting.

### FOUP Clamp

The system focuses on clamp command/feedback mismatch, FOUP present state, door closed state, clamp done state, related sensor alignment signals, and interlock chain context.

### EtherCAT I/O

The system interprets expected device state, observed diagnosis snapshot state, slave state transition problems, and I/O signal mismatches. It remains read-only and must not attempt to transition slave state.

## 6. Requirement Catalog

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
Implemented / Needs hardening. Dashboard route and backend summary exist; performance and E2E navigation hardening remain.

### REQ-EQP-001 Equipment Registry

Description:
Users must be able to browse Load Port / FOUP Clamp equipment and inspect equipment knowledge data.

User value:
Field engineers can start troubleshooting from equipment context rather than scattered records.

Acceptance criteria:

- Required route `/equipment` renders a real equipment list/hub page.
- Equipment list is tenant-scoped.
- Equipment detail exposes alarms, I/O points, and EtherCAT devices.
- List supports pagination, filtering, and stable sorting in future hardening.

Safety constraints:

- Equipment pages are read-only.
- No write/update/delete equipment operations are exposed through field workflow.

Current status:
Partially implemented. Backend equipment API exists. Visible sidebar route `/equipment` currently maps to a missing page / 404 and needs implementation.

### REQ-INC-001 Active Incidents

Description:
Users must be able to view active equipment troubleshooting incidents and their lifecycle state.

User value:
Operations teams can track open work across diagnosis, checklist, report, approval, and audit history.

Acceptance criteria:

- Required route `/active-incidents` renders a real incident hub page.
- Current active work is derived from diagnosis sessions until a dedicated incident lifecycle model is introduced.
- Incident rows link to diagnosis sessions, checklist runs, report drafts, approvals, and audit history where available.
- Sidebar route must match the required route.

Safety constraints:

- Incident state changes must not trigger equipment-control actions.
- Sensitive transitions must be audit logged.

Current status:
Missing. Visible navigation currently points to `/incidents`, which is missing and does not match required route `/active-incidents`.

### REQ-DIAG-001 Diagnosis Session

Description:
Users must create and review diagnosis sessions with equipment, alarm code, symptom summary, log excerpt, EtherCAT state, I/O snapshot, recent action, status, and risk level.

User value:
Troubleshooting begins from a standardized situation snapshot.

Acceptance criteria:

- Authenticated field/senior/admin users can create and read sessions.
- Unknown equipment or cross-tenant equipment is rejected.
- Session list/detail queries are tenant-scoped.
- Symptom summary is required.

Safety constraints:

- Input may describe risky requests, but output must remain advisory and safe.
- Cross-tenant access attempts must be denied and audit logged where feasible.

Current status:
Implemented / Needs hardening. Backend API and detail route exist; active incident lifecycle integration remains.

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
- No safety mechanism defeat instructions.

Current status:
Implemented / Needs hardening. Deterministic backend engine exists; broader evidence coverage and operational performance checks remain.

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
- Required route `/checklists` renders a list/hub page.

Safety constraints:

- Checklist items must remain inspection-oriented and read-only.
- Blocked items must preserve escalation path.

Current status:
Partially implemented. Backend and detail route `/checklist-runs/[checklistRunId]` exist. Visible sidebar route `/checklists` currently maps to a missing page / 404.

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
- Notes must not become machine commands.

Current status:
Partially implemented. Checklist item field notes exist; standalone incident-level notes are missing.

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
- Future report list route supports pagination and filtering.

Safety constraints:

- Report content must not include unsafe maintenance actions.
- Final report requires human approval before closure.

Current status:
Implemented / Needs hardening. Backend and detail route `/report-drafts/[reportDraftId]` exist; list/queue workflow remains incomplete.

### REQ-APR-001 Approval Workflow

Description:
Senior/admin users must approve or reject submitted report drafts with audit logging.

User value:
Final troubleshooting conclusions remain human-reviewed.

Acceptance criteria:

- Field users can submit but cannot approve/reject.
- Senior/admin users can approve/reject submitted reports.
- Rejection requires a comment.
- Required route `/approvals` renders an approval queue.

Safety constraints:

- Approval permission must be enforced by backend auth roles, not UI state alone.
- Approval decisions must be audit logged.

Current status:
Partially implemented. Backend approve/reject exists. Visible sidebar route `/approvals` currently maps to a missing page / 404.

### REQ-AUD-001 Audit Console

Description:
Senior/admin users must review tenant-scoped audit events with practical filters.

User value:
Operations can reconstruct sensitive actions, denied permissions, report decisions, and guardrail events.

Acceptance criteria:

- Route `/audit-events` renders without 404.
- API supports event type, severity, resource type, and limit filters.
- Field users are denied audit console access.
- Audit console access and permission denial are logged where feasible.

Safety constraints:

- Audit history is tenant-scoped.
- Audit records must not expose secrets.

Current status:
Implemented / Needs hardening. Audit console route and backend filter support exist; date range, actor, pagination, and retention policy remain future work.

### REQ-SET-001 System Safety Settings

Description:
Users must be able to view system safety settings such as external AI disabled, equipment control disabled, audit enabled, and role visibility.

User value:
Operators and reviewers can verify the system boundary from the UI.

Acceptance criteria:

- Required route `/settings` renders a real safety settings page.
- API exposes read-only safety settings.
- The page shows external AI disabled, equipment control disabled, audit enabled, and RBAC visibility.

Safety constraints:

- Settings page must not enable equipment-control behavior.
- Any future mutable settings require admin role and audit logging.

Current status:
Missing. Visible sidebar route `/settings` currently maps to a missing page / 404.

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
Partially implemented / Needs hardening. Backend guardrails exist; full language and navigation quality gate is introduced in PR-19.

### REQ-NAV-001 Navigation Completeness

Description:
All visible navigation items must resolve to real product modules or be removed until implemented.

User value:
Users should not hit dead-end routes during operational workflow.

Acceptance criteria:

- Sidebar route smoke test covers every visible navigation item.
- No visible navigation item returns 404.
- Route labels match product module names.
- Missing modules are implemented in PR-20/PR-21 or removed from visible navigation.

Safety constraints:

- Navigation must not expose unsupported control or maintenance actions.

Current status:
Missing / Needs implementation. Equipment, Active Incidents, Checklists, Approvals, and Settings currently have visible navigation gaps.
