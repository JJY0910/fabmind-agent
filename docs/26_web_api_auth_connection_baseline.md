# Web/API Auth Connection Baseline

## Scope

PR-34 records the current web-to-API authentication and live-data baseline for operational pages. It does not add product features, does not weaken backend authentication, and does not change the read-only equipment boundary.

This note covers:

- Dashboard
- Equipment Registry
- Active Incidents
- Checklist Runs
- Approval Queue
- Audit Console
- System Safety Settings

## Current Frontend API Calls

The frontend uses `apps/web/src/lib/api.ts` as the centralized API helper. The visible operational pages call these helpers:

| Page | Route | Helper |
| --- | --- | --- |
| Dashboard | `/` | `fetchDashboardSummary` |
| Equipment Registry | `/equipment` | `fetchEquipmentList` |
| Active Incidents | `/active-incidents` | `fetchIncidentList` |
| Checklist Runs | `/checklists` | `fetchChecklistRunList` |
| Approval Queue | `/approvals` | `fetchApprovalQueue`, `fetchCurrentUser` |
| Audit Console | `/audit-events` | `fetchAuditEvents` |
| System Safety Settings | `/settings` | `fetchSystemSafetySettings` |

Detail workflow pages also use the same helper for diagnosis sessions, checklist runs, report drafts, and report approval actions.

## Current Backend Auth Mechanism

The backend enforces bearer authentication with FastAPI `HTTPBearer(auto_error=False)` in `apps/api/app/api/v1/deps.py`.

- Missing credentials return `HTTP 401` with `Missing bearer token`.
- Invalid JWTs return `HTTP 401` with `Invalid bearer token`.
- Valid tokens are decoded with `JWT_SECRET`.
- The token subject and tenant claim must match an active user.
- Route access is enforced by role checks for `FIELD_ENGINEER`, `SENIOR_ENGINEER`, and `ADMIN`.
- Denied role access is audited and returns `HTTP 403`.

Token issuance already exists at `POST /api/v1/auth/login`, and current-user role visibility exists at `GET /api/v1/auth/me`.

## Frontend Token Source

The frontend currently reads an access token from `localStorage` key `fabmind_access_token` and sends it as:

```text
Authorization: Bearer <access-token>
```

No browser sign-in/session persistence flow currently writes that key. Because of that, directly opened operational pages can correctly reach the API base URL but still receive `HTTP 401: Missing bearer token`.

PR-34 does not hardcode a bearer token, does not introduce a public secret environment variable, and does not relax backend authentication.

## Failure Modes

The centralized web API helper now classifies API failures while preserving existing page fallback behavior:

- `success`: API response is parsed and rendered as live data.
- `unauthorized`: backend returned `HTTP 401`, commonly `Missing bearer token`.
- `forbidden`: backend returned `HTTP 403`.
- `network`: browser could not reach the API service.
- `invalid-json`: API response could not be parsed as JSON.
- `fallback data in use`: page-specific deterministic reference data remains visible with the existing warning banner.

The fallback warning banners are intentional until a browser sign-in/session flow is added.

## Safety Boundaries

This baseline preserves the existing safety model:

- No equipment control.
- No equipment write commands.
- No external AI/LLM runtime dependency.
- No auth weakening.
- No hardcoded bearer token.
- No OpenAPI or database schema change.
- Operational pages remain scoped to Load Port / FOUP Clamp / EtherCAT I/O.

## Recommended Next Step

The next implementation pass should add a small browser sign-in/session flow that calls `POST /api/v1/auth/login`, stores the returned access token through an explicit local development session mechanism, validates it through `GET /api/v1/auth/me`, and clears it on sign-out or token failure.

That follow-up should include focused frontend coverage for:

- authenticated live-data rendering,
- missing-token fallback banners,
- invalid-token failure handling,
- senior/admin approval visibility,
- field-user restricted approval behavior.
