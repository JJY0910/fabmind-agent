# RBAC and Approval Hardening

## Purpose

PR-27 hardens FabMind Agent approval and incident authority boundaries so the web UI, API authorization, audit trail, and operational workflow present one consistent policy.

## RBAC Policy Matrix

| Capability | Field engineer | Senior engineer | Admin |
| --- | --- | --- | --- |
| Read equipment, incidents, checklist runs, reports, and dashboard data | Allowed | Allowed | Allowed |
| Submit a draft report for approval | Allowed | Allowed | Allowed |
| Approve or reject a final report | Denied | Allowed | Allowed |
| Create incident cases from read-only evidence | Allowed | Allowed | Allowed |
| Move incidents through early operational states | Limited | Allowed | Allowed |
| Move incidents to APPROVED, CLOSED, or CANCELLED | Denied | Allowed | Allowed |
| Read audit console | Denied | Allowed | Allowed |

## Approval Authority

Report approval and rejection are enforced by backend RBAC. The frontend may hide or disable controls for users without authority, but the backend remains the source of truth for every decision.

Approval decisions require:

- an authenticated user
- role `SENIOR_ENGINEER` or `ADMIN`
- a submitted report draft
- tenant-scoped access to the report

Denied approval attempts are recorded as security audit events with the actor, route, method, role, allowed roles, and route parameters.

## Incident Lifecycle Authority

Field engineers may perform early operational transitions that support triage and checklist execution. Senior engineers and admins are required for senior-only lifecycle states such as approval, closure, or cancellation.

Denied senior-only incident transitions create `INCIDENT_UPDATE_DENIED` audit events with the current status, requested target status, and actor role.

## Frontend Authorization Boundary

The web UI reads `/api/v1/auth/me` to identify the current user role. If role information is unavailable, approval controls default to a restricted state and display that approval permissions are unavailable.

Frontend checks are advisory. They improve operator clarity but never replace backend RBAC enforcement.

## Audit Behavior

Sensitive approval and incident actions must produce audit records:

- report submission
- report approval
- report rejection
- approval or rejection denied by RBAC
- incident status changes
- incident close
- incident update denied by RBAC

Audit payloads should include resource identifiers and actor context where available.

## Safety Boundary

FabMind Agent remains a read-only, evidence-based troubleshooting platform. RBAC hardening does not introduce equipment-control capability, external AI execution, PDF export, email sending, or any equipment state-changing workflow.
