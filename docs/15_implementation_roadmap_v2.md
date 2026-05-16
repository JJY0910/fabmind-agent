# Implementation Roadmap v2

This roadmap starts from PR-19 and focuses on closing industrial product completeness gaps without changing the safety boundary. Future work must remain read-only, deterministic, evidence-based, tenant-scoped, and human-in-the-loop.

## PR-20 Backend Sidebar Module APIs

Goal:
Create backend list APIs required by visible sidebar modules so frontend hub pages can use real contracts.

Required scope:

- `GET /api/v1/equipment`
- `GET /api/v1/incidents`
- `GET /api/v1/checklist-runs`
- `GET /api/v1/report-drafts` or `GET /api/v1/approvals`
- `GET /api/v1/system/safety-settings`
- OpenAPI updates
- pytest coverage

Implementation notes:

- Keep all queries tenant-scoped.
- Add pagination and stable sort order to list APIs.
- Support filtering by status, equipment, severity, or resource type where relevant.
- Incidents may initially derive from diagnosis sessions, but the contract must support future incident lifecycle.
- Safety settings must be read-only and show external AI disabled, equipment control disabled, audit enabled, and RBAC visibility.

Exit criteria:

- Backend tests pass.
- OpenAPI reflects every route.
- No equipment-control endpoints are introduced.

## PR-21 Frontend Sidebar Module Completion

Goal:
Implement all visible sidebar hub pages so operational users do not hit 404 routes.

Required routes:

- `/equipment`
- `/active-incidents`
- `/checklists`
- `/approvals`
- `/settings`

Implementation notes:

- Update sidebar Active Incidents href from `/incidents` to `/active-incidents`.
- Use real API integration where backend contract exists.
- Use deterministic contract-shaped fallback only when a backend contract is present but local API is unavailable.
- Each hub page must include loading, empty, error, and success states.
- Do not add feature modules outside the existing product direction.

Exit criteria:

- No visible navigation item returns 404.
- Frontend typecheck and build pass.
- No unsafe instruction wording appears in UI.

## PR-22 Navigation / Contract / E2E Hardening

Goal:
Make navigation and workflow coverage enforceable in CI.

Required scope:

- visible sidebar navigation smoke test
- no 404 test
- route ID visibility test
- OpenAPI/frontend DTO consistency review
- GitHub Actions Playwright source of truth

Implementation notes:

- Local WSL Ubuntu 26.04 does not support Chromium through Playwright reliably in this environment, so GitHub Actions Playwright must be treated as the browser validation source of truth.
- Local checks should still run typecheck/build and any non-browser unit checks.

Exit criteria:

- GitHub Actions Playwright passes.
- Sidebar smoke test covers every visible navigation item.
- Route labels and required route IDs match the traceability matrix.

## PR-23 Read-Only Equipment Data Adapter

Goal:
Introduce a read-only adapter layer for equipment-related diagnostic snapshots.

Required scope:

- alarm event ingestion
- I/O snapshot ingestion
- EtherCAT status snapshot ingestion
- read-only adapter abstraction
- no equipment control

Implementation notes:

- Adapter inputs must be explicitly read-only data snapshots.
- No command, write, motion, or state-change method should exist in the interface.
- Store or normalize input records in tenant-scoped structures.
- Preserve deterministic analysis compatibility.

Exit criteria:

- Adapter tests cover alarm, I/O, and EtherCAT snapshot ingestion.
- No equipment-control method exists.
- Safety boundary is documented in code and docs.

## PR-24 Incident Lifecycle / Case Management

Goal:
Add incident lifecycle support so active operational work is tracked across diagnosis, checklist, report, approval, and audit history.

Required scope:

- incident status model
- links diagnosis/checklist/report/approval/audit
- operational state transitions
- active incident hub API/UI integration

Implementation notes:

- Incident states should be explicit and auditable.
- Diagnosis sessions should remain source evidence, not be overwritten by incident state.
- Transitions such as opened, in review, blocked, awaiting approval, resolved, and closed should be evaluated against safety and approval rules.

Exit criteria:

- Incident lifecycle tests pass.
- Tenant isolation tests pass.
- Sensitive state transitions create audit events.

## PR-25 Performance / Reliability Hardening

Goal:
Make list-heavy operational screens reliable under realistic usage.

Required scope:

- pagination
- filters
- stable sorting
- loading/error states
- structured logging
- correlation IDs

Implementation notes:

- Dashboard and list endpoints should avoid unbounded queries.
- UI lists should avoid unbounded rendering.
- Filters should include status/equipment/severity where relevant.
- Errors should be visible, bounded, and operationally understandable.

Exit criteria:

- API defaults use bounded limits.
- Frontend lists render predictably.
- CI checks pass.

## PR-26 RBAC / Approval Hardening

Goal:
Strengthen role-bound approval behavior across backend and frontend.

Required scope:

- approval permissions tied to auth roles
- no UI-only role simulation
- audit logs for approval decisions
- field user cannot approve through UI or API
- senior/admin approval path verified

Implementation notes:

- Backend remains source of truth for permissions.
- UI must reflect role state from authenticated user context.
- Permission denied outcomes must be visible and audit logged where feasible.

Exit criteria:

- RBAC tests pass.
- Approval E2E covers field denial and senior/admin decision.
- Audit events exist for approval decisions and denied access.

## PR-27 Release Candidate v0.2.0

Goal:
Establish a release candidate that satisfies the PR-19 rebaseline.

Required scope:

- no visible 404
- all checks pass
- no unsafe wording
- documented operational workflow
- requirements traceability reviewed
- industrial quality gate reviewed

Exit criteria:

- `npm run typecheck` passes.
- `npm run build` passes.
- backend pytest passes.
- GitHub Actions Playwright passes.
- language cleanup scan has no unresolved outward-facing product-positioning issues.
- safety phrase scan has no unsafe user-facing wording.
