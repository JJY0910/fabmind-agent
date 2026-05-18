# Industrial Quality Gate

This quality gate applies to FabMind Agent PRs. It keeps the product aligned with field operations, read-only diagnostics, evidence-based troubleshooting, deterministic analysis, human approval, and auditability.

## Gate Status Legend

- **Pass**: Current implementation and tests satisfy the gate for the release-candidate baseline.
- **Pass / Needs hardening**: Current implementation satisfies the gate, with operational depth still planned.
- **Open**: The gate is not yet satisfied.
- **Future release**: The gate is intentionally deferred from the current release-candidate baseline.

## Quality Gate Matrix

| Gate | Status | Evidence | Related tests/docs | Remaining work |
|---|---|---|---|---|
| No visible navigation 404 | Pass | Sidebar routes exist for Dashboard, Equipment, Active Incidents, Checklists, Approvals, Audit Console, and Settings | `apps/web/tests/e2e/navigation-hardening.spec.ts`, docs/13 | GitHub Actions remains browser validation source |
| No unsafe user-facing wording | Pass / Needs hardening | README/docs/UI language is production-oriented and read-only | Product and safety scans in PR validation | Add CI-enforced scan in a future PR |
| No external AI/LLM runtime dependency | Pass | Deterministic agent engine provides core analysis without external calls | PR-07 tests, docs/12 | Continue guarding new analysis code |
| No equipment control | Pass | API/routes/settings expose diagnostics, telemetry ingestion, and workflow records only | OpenAPI safety tests, docs/17, docs/21 | Real connector spec must preserve inbound-only design |
| No command/control endpoint | Pass | OpenAPI contains no equipment-control route family | PR-23, PR-24, PR-25, PR-28 tests | Keep OpenAPI safety test active |
| Read-only telemetry ingestion only | Pass / Needs hardening | Alarm events, I/O snapshots, and EtherCAT status snapshots are stored as inbound telemetry | PR-23 tests, docs/17 | Real factory connector specification |
| Deterministic agent behavior | Pass / Needs hardening | Rule scenarios produce repeatable hypotheses and insufficient-evidence outcomes | PR-07 tests | Expand rule coverage while preserving determinism |
| Evidence traceability | Pass / Needs hardening | Hypotheses, checklist plans, reports, and audits reference stored workflow data | PR-07, PR-09, PR-10 tests | Stronger evidence completeness scoring |
| Incident lifecycle traceability | Pass / Needs hardening | Incidents link alarm events, diagnosis sessions, checklists, reports, approvals, and audit context | PR-24 tests, docs/18 | Timeline view and assignment workflow |
| Human approval | Pass | Final report approval/rejection is senior/admin controlled | PR-10, PR-27 tests | Reviewer assignment and SLA visibility |
| RBAC enforcement | Pass / Needs hardening | Field users denied final approval and senior-only incident transitions; denial audit context exists | PR-27 tests, docs/20 | Centralized policy matrix in API documentation |
| Audit logging | Pass / Needs hardening | Sensitive creation, analysis, checklist, report, approval, incident, telemetry, and denial events are logged | PR-03, PR-07, PR-09, PR-10, PR-11, PR-23, PR-24, PR-27 tests | Retention policy and actor/date search |
| API contract coverage | Pass / Needs hardening | OpenAPI covers implemented production endpoints and avoids speculative paths | PR-20, PR-23, PR-24, PR-25, PR-28 tests | Generated contract drift check in CI |
| DB/migration consistency | Pass / Needs hardening | Schema includes telemetry, incident, checklist, report, approval, and audit tables | PR-23, PR-24, PR-25 tests, docs/21 | Full migration replay smoke in CI |
| Pagination/filter/sort | Pass / Needs hardening | List endpoints use bounded limits, offsets, and stable ordering where practical | PR-20, PR-23, PR-24, PR-25 tests | Broader status/equipment/date filters |
| Frontend API contract handling | Pass / Needs hardening | Pages distinguish live API data, empty result, loading, and degraded reference state | PR-26 implementation, typecheck/build | Browser tests for degraded data mode |
| Request correlation ID | Pass | `X-Request-ID` is generated or preserved and included in responses | PR-25 tests | Structured log correlation across all services |
| Readiness endpoint | Pass | `/api/v1/health/ready` performs lightweight service readiness without equipment connectivity | PR-25 tests | Deployment probe wiring |
| CI checks | Pass / Needs hardening | Local pytest/typecheck/build/diff checks are required; Playwright runs in GitHub Actions | docs/15, docs/21 | Add acceptance test job for PR-28 static checks |
| End-to-end operational flow acceptance | Pass / Needs hardening | Backend acceptance test connects telemetry, incident, diagnosis, checklist, report, approval, and audit records | PR-29 test, docs/22 | Browser-level full-flow acceptance and release packaging |
| Deployment/containerization | Future release | No deployment packaging is claimed in the current acceptance baseline | docs/15, docs/21 | PR-30 packaging and release notes |
| Observability/metrics | Future release | Current baseline has request IDs, readiness, logs, and audit records, but no metrics or alerting | docs/19, docs/21 | Metrics, dashboards, and alert policy |
| Incident timeline UI | Future release | Incidents exist as first-class cases, but timeline visualization is not a dedicated module | docs/18, docs/21 | Incident timeline read model and UI |
| Real equipment connector specification | Future release | Telemetry adapter is read-only and implementation-backed; real connector specification is not complete | docs/17, docs/21 | Inbound connector contract and offline replay policy |
| Offline factory network execution mode | Future release | No external runtime dependency is preserved, but offline execution packaging is not complete | docs/15, docs/21 | Offline installation, backup, and restore guidance |

## PR Review Checklist

Before merge, the PR owner must answer:

- Which requirement IDs are covered?
- Which module traceability rows changed?
- Which user-facing routes changed?
- Which API contract entries changed?
- Which safety boundary was reviewed?
- Which audit events were added or preserved?
- Which validation commands passed?
- Are any visible navigation gaps introduced or left unresolved?
- Does the PR keep equipment integration read-only?
- Does the PR avoid broad feature expansion outside Load Port / FOUP Clamp / EtherCAT I/O?

## Release-Candidate Gate Position

The current system meets the release-candidate acceptance baseline for implemented modules, subject to known limitations documented in `docs/21_release_candidate_acceptance_audit.md`. This is not a final production readiness claim; it is an implementation-backed acceptance status for the current scope.
