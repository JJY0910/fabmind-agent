# End-to-End Operational Flow Acceptance

## Purpose

This document describes the PR-29 backend acceptance coverage for the current FabMind Agent operational workflow. The acceptance test verifies that read-only telemetry, incident lifecycle, diagnosis, checklist execution, report approval, and audit trail records connect into a coherent operational case flow.

This is integration acceptance coverage for the current release-candidate scope. It does not add product modules or claim final production deployment readiness.

## Tested Operational Flow

The backend acceptance test covers:

1. A senior/admin user ingests a read-only alarm event for Load Port / FOUP Clamp context.
2. The telemetry adapter persists the alarm event and links it to an active incident.
3. A field user creates a diagnosis session for the same equipment and alarm context.
4. The incident links to the diagnosis session.
5. Deterministic analysis creates evidence-linked analysis output.
6. A checklist run is created from the analysis and completed with field notes.
7. The checklist run links back to the incident.
8. A report draft is created from the diagnosis session and completed checklist.
9. The report draft is submitted and approved by a senior user.
10. The approval links back to the incident.
11. The incident transitions through the senior-controlled lifecycle toward closure.
12. Audit records confirm the operational path.

## Entities Involved

- `equipment_alarm_events`
- `equipment_incidents`
- `diagnosis_sessions`
- `agent_runs`
- `checklist_runs`
- `checklist_items`
- `report_drafts`
- `report_approvals`
- `audit_events`

## Expected Audit Events

The acceptance test verifies representative audit coverage for:

- `EQUIPMENT_ALARM_EVENT_INGESTED`
- `INCIDENT_LINKED_TO_ALARM_EVENT`
- `DIAGNOSIS_SESSION_CREATED`
- `INCIDENT_LINKED_TO_DIAGNOSIS`
- `AGENT_ANALYSIS_COMPLETED`
- `CHECKLIST_RUN_CREATED`
- `CHECKLIST_ITEM_COMPLETED`
- `REPORT_DRAFT_CREATED`
- `REPORT_DRAFT_SUBMITTED`
- `REPORT_DRAFT_APPROVED`
- `INCIDENT_LINKED_TO_CHECKLIST`
- `INCIDENT_LINKED_TO_REPORT`
- `INCIDENT_LINKED_TO_APPROVAL`
- `INCIDENT_STATUS_CHANGED`
- `INCIDENT_CLOSED`
- `RBAC_PERMISSION_DENIED`

## RBAC Expectations

- Field users can create diagnosis sessions, execute checklist work, and submit report drafts.
- Field users cannot approve or reject final reports.
- Senior/admin users can approve or reject submitted reports.
- Senior/admin users control final incident lifecycle transitions.
- Denied approval and rejection attempts must be audit logged with report draft context.

## Read-Only Equipment Boundary

The PR-29 acceptance coverage verifies that:

- OpenAPI paths do not expose equipment-control route families.
- System safety settings remain read-only.
- Equipment-data endpoints remain limited to telemetry `GET` and `POST`.
- The operational case flow never requires an equipment state-changing endpoint.

## Intentionally Not Covered

- Browser workflow automation; GitHub Actions Playwright remains the browser validation source.
- Deployment packaging.
- Real factory connector implementation.
- Offline installation and backup procedures.
- Metrics and alerting.
- Dedicated incident timeline UI.

## Remaining Gaps

- Dedicated incident timeline and assignment workflow.
- Full migration replay in CI.
- Real read-only connector specification.
- Offline factory network execution profile.
- Release Candidate v0.2.0 packaging and release notes.
