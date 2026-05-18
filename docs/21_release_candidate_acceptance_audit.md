# Release Candidate Acceptance Audit

## 1. Audit Purpose

This document records the PR-28 system acceptance audit for FabMind Agent after PR-20 through PR-27. It establishes an operational acceptance baseline for the current implementation-backed scope.

This is a release candidate audit assessment, not a final production readiness claim. It records implementation-backed acceptance status, known limitations, and next release backlog items.

## 2. Release Candidate Scope

Included capabilities:

- Dashboard summary
- Equipment registry and equipment knowledge
- Active incident lifecycle
- Diagnosis sessions
- Deterministic agent analysis
- Checklist execution and field notes
- Report drafts
- Approval queue and senior/admin approval workflow
- Audit console
- System safety settings
- Read-only equipment telemetry ingestion
- Backend pagination, request correlation, readiness, and logging guardrails
- Frontend API contract handling and degraded state visibility
- RBAC hardening for approvals and incident transitions
- End-to-end operational flow acceptance coverage

Excluded capabilities:

- Real equipment control
- External AI or LLM calls in runtime-critical analysis
- PDF export
- Email sending
- Broad semiconductor equipment domains beyond Load Port / FOUP Clamp / EtherCAT I/O
- Final production deployment certification

## 3. Acceptance Criteria

| Criterion | Acceptance status | Evidence |
|---|---|---|
| Visible navigation routes resolve | Accepted / Needs continued CI validation | `/`, `/equipment`, `/active-incidents`, `/checklists`, `/approvals`, `/audit-events`, `/settings` route files exist; PR-22 Playwright smoke coverage |
| OpenAPI covers implemented backend contracts | Accepted / Needs automated drift check | `contracts/openapi.yaml` includes equipment, incidents, checklists, report drafts, approvals, safety settings, telemetry, dashboard, audit, auth, and health paths |
| DB schema supports operational workflow | Accepted / Needs migration replay in CI | `db/schema.sql` includes telemetry, incidents, diagnosis, agent, checklist, report, approval, policy, and audit tables |
| No equipment-control API surface | Accepted | OpenAPI path scan and system safety settings confirm read-only boundary |
| Deterministic analysis works without external AI | Accepted / Needs broader rules | PR-07 rule coverage and no external runtime dependency |
| Evidence traceability is present | Accepted / Needs completeness scoring | evidence_links, inspection_plan_items, checklist_items, report_drafts, and audit_events are persisted |
| Human approval is enforced | Accepted / Needs reviewer workflow depth | report approval endpoints and PR-27 RBAC tests |
| Auditability is present | Accepted / Needs retention policy | audit_events table and audit tests across sensitive workflows |
| Pagination/reliability hardening exists | Accepted / Needs load validation | PR-25 pagination, index, request ID, and readiness tests |
| Frontend degraded data state is explicit | Accepted / Needs browser coverage | PR-26 API helper and page handling |
| Backend operational flow connects records end to end | Accepted / Needs browser coverage | PR-29 acceptance test links telemetry, incident, diagnosis, checklist, report, approval, and audit trail |

## 4. Implemented Capability Map

| Capability | Current status | Main route/API | Data source |
|---|---|---|---|
| Dashboard | Implemented / Needs hardening | `/`, `GET /api/v1/dashboard/summary` | workflow aggregate tables |
| Equipment Registry | Implemented / Needs hardening | `/equipment`, `GET /api/v1/equipment` | equipment, alarms, I/O points, EtherCAT devices |
| Active Incidents | Implemented / Needs hardening | `/active-incidents`, `GET /api/v1/incidents` | equipment_incidents |
| Diagnosis Sessions | Implemented / Needs hardening | `/diagnosis-sessions/[sessionId]`, diagnosis session APIs | diagnosis_sessions |
| Deterministic Agent Analysis | Implemented / Needs hardening | analyze endpoint | agent_runs, hypotheses, evidence links |
| Checklists | Implemented / Needs hardening | `/checklists`, checklist APIs | checklist_runs, checklist_items |
| Report Drafts | Implemented / Needs hardening | `/report-drafts/[reportDraftId]`, report draft APIs | report_drafts |
| Approvals | Implemented / Needs hardening | `/approvals`, approval endpoints | report_approvals |
| Audit Console | Implemented / Needs hardening | `/audit-events`, `GET /api/v1/audit-events` | audit_events |
| Settings / Safety Policy | Implemented / Needs hardening | `/settings`, `GET /api/v1/system/safety-settings` | read-only policy constants |
| Telemetry Adapter | Implemented / Needs hardening | `/api/v1/equipment-data/*` | equipment telemetry tables |
| RBAC Enforcement | Implemented / Needs hardening | auth/me, approval, incident APIs | users, roles, audit_events |
| Reliability Baseline | Implemented / Needs hardening | request middleware, readiness endpoint | app middleware and schema indexes |
| Operational Flow Acceptance | Implemented / Needs hardening | backend acceptance test | telemetry, incident, diagnosis, checklist, report, approval, audit records |

## 5. Route Coverage

| Route | Status |
|---|---|
| `/` | Implemented |
| `/equipment` | Implemented |
| `/active-incidents` | Implemented |
| `/checklists` | Implemented |
| `/approvals` | Implemented |
| `/audit-events` | Implemented |
| `/settings` | Implemented |
| `/diagnosis-sessions/[sessionId]` | Implemented |
| `/checklist-runs/[checklistRunId]` | Implemented |
| `/report-drafts/[reportDraftId]` | Implemented |

## 6. API Coverage

Key implemented OpenAPI paths:

- `/api/v1/equipment`
- `/api/v1/incidents`
- `/api/v1/checklist-runs`
- `/api/v1/report-drafts`
- `/api/v1/approvals`
- `/api/v1/system/safety-settings`
- `/api/v1/equipment-data/alarm-events`
- `/api/v1/equipment-data/io-snapshots`
- `/api/v1/equipment-data/ethercat-status-snapshots`
- `/api/v1/dashboard/summary`
- `/api/v1/audit-events`
- `/api/v1/auth/me`
- `/api/v1/health/ready`

Contract safety result:
The OpenAPI contract should contain implemented read-only workflow, telemetry, health, and approval endpoints only. It must not contain equipment-control path families.

## 7. DB and Migration Coverage

Key schema objects:

- equipment registry: `equipment`, `equipment_families`, `alarm_codes`, `io_points`, `ethercat_devices`
- telemetry: `equipment_alarm_events`, `equipment_io_snapshots`, `equipment_ethercat_status_snapshots`
- workflow: `diagnosis_sessions`, `agent_runs`, `agent_steps`, `diagnosis_hypotheses`, `evidence_links`, `inspection_plan_items`
- checklist/report/approval: `checklist_runs`, `checklist_items`, `report_drafts`, `report_approvals`
- incident lifecycle: `equipment_incidents`
- safety/audit: `policy_violations`, `audit_events`

Acceptance status:
Schema coverage is implementation-backed. Full migration replay across a fresh environment remains a recommended release-candidate hardening item.

## 8. Test Coverage

Backend tests cover:

- health
- auth/RBAC/audit
- equipment knowledge
- diagnosis sessions
- deterministic agent rules
- checklist runner
- report builder and approval
- dashboard and audit console
- sidebar module APIs
- read-only telemetry adapter
- incident lifecycle
- performance/reliability
- RBAC approval hardening
- PR-28 static acceptance checks
- PR-29 end-to-end operational flow acceptance

Frontend validation covers:

- TypeScript typecheck
- production build
- Playwright navigation/workflow checks in GitHub Actions

## 9. Safety Boundary Verification

Safety baseline:

- Equipment integration is read-only.
- Telemetry ingestion is inbound only.
- Deterministic analysis does not call external AI services.
- Risky intent in analysis or telemetry ingestion is blocked or requires senior/admin review.
- Final reports require human approval.
- Settings expose policy visibility without editable equipment controls.
- OpenAPI path checks guard against equipment-control route families.

## 10. RBAC Verification

Current policy:

- Field users can participate in operational workflow but cannot approve/reject final reports.
- Senior/admin users can approve/reject submitted reports.
- Field users cannot perform senior-only incident lifecycle transitions.
- Senior/admin users can perform senior-only incident lifecycle transitions according to the status matrix.
- Audit events record important denials and decisions with resource context where feasible.

Frontend behavior:
Frontend controls reflect authenticated role state conservatively. Unknown or malformed current-user responses do not enable privileged actions.

## 11. Operational Workflow Summary

Current workflow:

1. Read-only telemetry or seeded equipment context identifies an equipment condition.
2. An active incident links alarm events and diagnosis context.
3. A diagnosis session captures the operational snapshot.
4. Deterministic analysis produces evidence-linked hypotheses and inspection plan items.
5. A checklist run structures field inspection and field notes.
6. A deterministic report draft summarizes evidence and inspection results.
7. Senior/admin approval or rejection records the final decision.
8. Audit events preserve sensitive workflow activity and denials.

## 12. Known Limitations

- Browser E2E validation depends on GitHub Actions because local WSL browser execution is constrained in this environment.
- PR-29 validates the backend operational flow; browser-level full-flow acceptance remains future work.
- Incident timeline visualization is not yet a dedicated module.
- Field notes are checklist-item scoped; incident-level note aggregation remains future work.
- Read-only real equipment connector specification is not complete.
- Deployment/container packaging is not yet acceptance-tested.
- Observability is limited to request IDs, readiness, logging guardrails, and audit records; metrics and alerting remain future work.
- Migration replay is covered by conventional migrations and tests but not yet by a dedicated CI migration replay job.

## 13. Next Release Backlog

- Release Candidate v0.2.0 Packaging / Release Notes
- Observability / incident timeline hardening
- Read-only real equipment connector specification
- Offline factory network execution mode

## 14. Release Decision Status

Decision:
Conditionally acceptable as an operational acceptance baseline for the current release-candidate scope.

Conditions:

- All PR-28 validation commands must pass.
- Product language scan must have no matches.
- Safety phrase scan must have no user-facing docs/UI matches.
- Static acceptance checks must pass.
- Known limitations must remain documented and must not be represented as final production readiness.
