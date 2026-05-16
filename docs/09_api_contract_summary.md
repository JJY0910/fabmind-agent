# API Contract Summary

상세 계약은 `contracts/openapi.yaml`을 기준으로 한다.

## 핵심 API

| Method | Path | 설명 |
|---|---|---|
| GET | /api/v1/health | health check |
| POST | /api/v1/auth/login | user login |
| GET | /api/v1/equipment | equipment list |
| GET | /api/v1/equipment/{id} | equipment detail aggregate |
| POST | /api/v1/diagnosis-sessions | diagnosis create |
| GET | /api/v1/diagnosis-sessions/{id} | session aggregate detail |
| POST | /api/v1/diagnosis-sessions/{id}/run-agent | run deterministic agent |
| GET | /api/v1/diagnosis-sessions/{id}/agent-runs/latest | latest agent result |
| POST | /api/v1/checklist-runs/{id}/steps/{step_id}/complete | complete checklist step |
| POST | /api/v1/reports | create report draft |
| POST | /api/v1/reports/{id}/request-approval | request approval |
| POST | /api/v1/approval-requests/{id}/approve | approve |
| POST | /api/v1/approval-requests/{id}/reject | reject |
| GET | /api/v1/audit-events | audit event search |

## 공통 ErrorResponse

```json
{
  "error_code": "VALIDATION_ERROR",
  "message": "Human readable message",
  "details": {},
  "request_id": "req_..."
}
```

## Session Aggregate Response

`GET /api/v1/diagnosis-sessions/{id}`는 frontend 편의를 위해 다음을 한 번에 반환한다.

```text
session
input_snapshot
equipment
agent_run
agent_steps
hypotheses
evidence_links
inspection_plan
checklist_run
report
approval_status
audit_summary
```

이렇게 해야 Agent Analysis 화면이 API 여러 개에 의존하지 않고 안정적으로 렌더링된다.
