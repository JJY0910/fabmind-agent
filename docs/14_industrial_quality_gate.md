# Industrial Quality Gate

This quality gate applies to future FabMind Agent PRs. It is intended to prevent drift into shallow work and to keep the product aligned with field operations, read-only diagnostics, evidence-based troubleshooting, deterministic analysis, human approval, and auditability.

## 1. Product Boundary Gate

A PR fails the gate if it violates any of the following:

- Scope expands beyond Load Port / FOUP Clamp / EtherCAT I/O without an approved requirements update.
- Runtime-critical analysis depends on external AI or LLM calls.
- The product exposes equipment-control behavior.
- The product recommends state-changing maintenance actions.
- The product weakens the human approval boundary for final reports.
- The PR introduces real company data, customer data, or site-specific operational data.

## 2. Navigation Gate

Required checks:

- No visible navigation 404.
- Every visible sidebar item maps to a real product module.
- If a module is not implemented, remove it from visible navigation or implement a real route before merging.
- Route labels must match the module named in the traceability matrix.
- Active Incidents must use required route `/active-incidents`, not an untracked alternate path.

Required future test:

- A Playwright sidebar smoke test must click each visible navigation item and assert no 404 page is rendered.

## 3. Safety Language Gate

Required checks:

- No unsafe instruction wording in user-facing docs or UI.
- No interlock bypass instructions.
- No output forcing instructions.
- No servo command instructions.
- No wording that implies the system can repair equipment without human decision.
- Risky input examples may appear only as blocked-policy examples or negative tests.

Review expectation:

- If unsafe phrases appear in backend negative tests or policy-block examples, they must be clearly intentional and must assert blocked behavior.
- User-facing operational content should describe safe read-only verification, escalation, approval, and audit logging.

## 4. Agent Behavior Gate

Required checks:

- Deterministic agent behavior must be reproducible.
- Every hypothesis must link to evidence.
- Insufficient evidence must produce an explicit insufficient-evidence status.
- Risky action requests must produce a safety-blocked result and audit event.
- The agent must not be the sole source of safety decisions.
- Final report conclusions must remain human-approved.

## 5. Evidence Traceability Gate

Required checks:

- Diagnosis hypotheses must trace to alarm, I/O, EtherCAT, rule trace, or stored evidence.
- Checklist items must trace to inspection plan items or evidence codes where available.
- Report drafts must derive from stored diagnosis, agent analysis, evidence, and checklist results.
- Audit events must link to resource type and resource ID where feasible.

## 6. Audit Gate

Sensitive actions must be audit logged:

- login success/failure
- permission denial
- diagnosis session creation and detail access where feasible
- agent analysis start/completion/blocked result
- checklist run creation
- checklist item status updates
- report draft creation/submission
- approval/rejection decisions
- audit console access
- future incident lifecycle transitions
- future safety setting changes

## 7. API Contract Gate

Required checks:

- Every backend route has typed request/response schemas.
- `contracts/openapi.yaml` is updated when API behavior changes.
- API routes remain under `/api/v1`.
- Tenant-scoped data is filtered by `tenant_id`.
- Field/senior/admin permissions are enforced in backend dependencies.
- 401, 403, 404, and validation errors are covered where relevant.

## 8. Test Coverage Gate

Minimum test expectations:

- backend pytest for new route behavior
- tenant isolation test for tenant-scoped reads
- RBAC test for sensitive routes
- audit event creation test for sensitive actions
- deterministic rule scenario tests when agent behavior changes
- frontend typecheck/build for UI PRs
- Playwright route smoke or E2E checks for navigation and workflow PRs

## 9. Performance and Reliability Gate

List endpoints and list UIs must be designed for operational scale:

- list endpoints must support pagination
- filtering by status, equipment, severity, or resource type where relevant
- stable sort order
- avoid unbounded list rendering
- predictable loading states
- predictable empty states
- predictable error states
- bounded default limits for audit and operational history
- CI checks must pass before merge

Initial performance expectations:

- Default list page size should be bounded.
- Queries should remain tenant-scoped and indexed where schema support exists.
- Dashboard summary should avoid unbounded detail loading.
- Frontend list pages should avoid rendering unlimited rows.

## 10. PR Review Checklist

Before merge, the PR owner must answer:

- Which requirement IDs are covered?
- Which module traceability rows changed?
- Which user-facing routes changed?
- Which API contract entries changed?
- Which safety boundary was reviewed?
- Which audit events were added or preserved?
- Which validation commands passed?
- Are any visible navigation gaps introduced or left unresolved?
