# FabMind Agent v0.2.0 Release Candidate

## Release Identifier

FabMind Agent v0.2.0 Release Candidate

## Release Status

Status: release candidate / operational acceptance baseline.

This release candidate packages the current implementation-backed baseline for read-only diagnostics, evidence-based troubleshooting, deterministic rule analysis, human approval, and auditability. It does not certify final production deployment.

## Scope

FabMind Agent v0.2.0 RC is scoped to Load Port / FOUP Clamp / EtherCAT I/O troubleshooting workflow.

Included operational scope:

- Load Port equipment context and alarm-driven troubleshooting.
- FOUP Clamp sensor, door, presence, and interlock-related investigation.
- EtherCAT I/O state and signal mismatch interpretation.
- Tenant-scoped operational records for diagnosis, checklist, report, approval, and audit workflow.

Out of scope:

- Broad semiconductor equipment domains outside Load Port / FOUP Clamp / EtherCAT I/O.
- Equipment state-changing integration.
- External AI or LLM runtime dependency for deterministic analysis.
- Deployment/container certification.

## Major Capabilities

- Read-only equipment telemetry ingestion for alarm events, I/O snapshots, and EtherCAT status snapshots.
- Equipment incidents and case management.
- Diagnosis sessions with standardized operational snapshots.
- Deterministic agent analysis with evidence-linked hypotheses and inspection plans.
- Checklist runs with item status and field notes.
- Report drafts generated from deterministic analysis and checklist evidence.
- Senior/admin approval workflow for submitted reports.
- RBAC enforcement for approval and incident lifecycle decisions.
- Audit trail for sensitive workflow activity, denials, and decisions.
- Sidebar operational views for dashboard, equipment, incidents, checklists, approvals, audit events, and settings.
- Navigation, contract, and reliability hardening across backend and frontend surfaces.
- Backend/TestClient end-to-end operational flow acceptance covering telemetry, incident, diagnosis, checklist, report, approval, and audit records.

## Safety Boundaries

- No equipment control.
- No external AI/LLM runtime dependency for core analysis.
- No output forcing.
- No interlock bypass.
- No servo/reset/motion command path.
- Human approval is required for final report decisions.
- Deterministic rule output must remain evidence-linked.
- Equipment integration remains read-only and inbound.

## Validation Summary

Current PR-30 validation baseline:

- Backend targeted release packaging pytest: 8 passed.
- Backend full pytest count: 136 passed.
- Frontend typecheck: `npm run typecheck`.
- Frontend production build: `npm run build`.
- Repository whitespace check: `git diff --check`.
- GitHub Actions Playwright is the browser validation source of truth for navigation and workflow smoke coverage.

## Known Limitations

- Not connected to real fab equipment yet.
- Read-only adapter is ready, but the real connector specification remains future work.
- Browser full-flow acceptance remains future work.
- Deployment/containerization remains future work.
- Observability and incident timeline hardening remain future work.
- Migration replay CI remains future work.
- This release candidate is an operational acceptance baseline, not a final deployment certification.

## Next Release Backlog

- Deployment/containerization.
- Observability / incident timeline hardening.
- Read-only real equipment connector specification.
- Offline factory network execution mode.
- Browser full operational flow acceptance.
- Migration replay CI.
