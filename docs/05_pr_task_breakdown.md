# PR 단위 개발 실행 계획

이 계획은 Antigravity와 Codex를 동시에 쓰더라도 코드가 꼬이지 않도록 PR 단위로 쪼갠 실행 순서다.

## Phase 0 - Foundation

### PR-00 Repository Foundation

Owner: Antigravity

목표:

- canonical monorepo scaffold 생성
- Next.js/FastAPI 기본 실행
- Docker Compose 구성
- health endpoint 구현

검수:

- `docker compose -f infra/docker-compose.yml up -d` 성공
- `/api/v1/health` 200
- Web login placeholder 표시
- README 실행 방법 존재

### PR-01 CI / Quality Gate

Owner: Codex

목표:

- GitHub Actions CI 추가
- backend pytest, frontend typecheck, lint, Playwright smoke 준비
- quality gate script 작성

검수:

- `.github/workflows/ci.yml` 존재
- CI가 push/pull_request에서 실행
- 실패 시 어떤 job이 실패했는지 명확

## Phase 1 - Domain Foundation

### PR-02 Database Models and Seeds

Owner: Codex

목표:

- tenant, user, role, equipment, alarm, io_points, ethercat_devices, documents, diagnosis_sessions 테이블 구현
- deterministic seed 생성

검수:

- seed user 3명
- alarm code 30개 이상
- I/O point 60개 이상
- scenario 20개 이상
- tenant isolation 테스트 통과

### PR-03 Auth/RBAC/Audit

Owner: Codex

목표:

- role 기반 권한 처리
- audit event 기록

검수:

- field는 승인 API 접근 불가
- senior는 approve/reject 가능
- 권한 실패도 audit 기록

## Phase 2 - Equipment Knowledge UX

### PR-04 UI Design System and App Shell

Owner: Antigravity

목표:

- dark industrial SaaS theme
- sidebar/topbar/layout
- card, badge, table, timeline, evidence drawer 기본 컴포넌트

검수:

- 반응형 레이아웃
- empty/loading/error state
- 접근 가능한 contrast
- screenshot artifact 제공

### PR-05 Equipment Knowledge Pages

Owner: Antigravity + Codex

목표:

- equipment list/detail API + UI
- 알람, I/O, EtherCAT, 문서 근거 표시

검수:

- LP-01 상세에서 연결 데이터 확인 가능
- table filter/search 가능

## Phase 3 - Agentic Diagnosis Core

### PR-06 Diagnosis Session API

Owner: Codex

목표:

- diagnosis session create/read/list
- situation snapshot 저장
- validation rules

검수:

- invalid alarm code 422
- insufficient snapshot 저장 가능
- session detail aggregate API 제공

### PR-07 Deterministic Agent Engine

Owner: Codex

목표:

- rule engine 구현
- hypothesis ranking
- evidence link 생성
- insufficient evidence 처리

검수:

- Scenario A/B/C unit test 통과
- LLM 없이 결과 생성
- 모든 hypothesis에 evidence 존재

### PR-08 Agent Analysis UI

Owner: Antigravity

목표:

- agent timeline
- hypothesis cards
- evidence drawer
- risk banner
- insufficient evidence UI

검수:

- Scenario A/B/C 브라우저 시연 가능
- screenshot/video artifact 제공

## Phase 4 - Checklist / Report / Approval

### PR-09 Checklist Runner

Owner: Codex + Antigravity

목표:

- inspection plan 생성
- checklist run API/UI
- 완료/스킵/메모 기록

검수:

- checklist step 상태 변경
- audit 기록

### PR-10 Report Builder and Approval

Owner: Codex + Antigravity

목표:

- report draft 생성
- engineer edit area
- senior approval/rejection

검수:

- field 승인요청 가능
- senior 승인/반려 가능
- report status 변경
- audit 기록

## Phase 5 - Finish Quality

### PR-11 Dashboard and Audit Console

Owner: Antigravity

목표:

- active diagnosis, high risk, pending approvals, recent audit 표시

검수:

- dashboard에서 Golden Path 상태 추적 가능

### PR-12 E2E Test and Final Polish

Owner: Codex + Antigravity

목표:

- Playwright E2E
- UI polish
- final README/screenshots
- repository readiness

검수:

- CI green
- workflow script 성공
- README에 screenshots 포함
- 10점 scorecard 기준 충족

## Phase 6 - Industrial Product Rebaseline

### PR-19 Industrial Product Rebaseline / Requirements Traceability

Owner: Codex

목표:

- README와 운영 문서를 production-oriented field operations language로 재정렬
- visible sidebar navigation 404를 제품 완성도 gap으로 명시
- requirements, traceability matrix, industrial quality gate, implementation roadmap 작성
- Load Port / FOUP Clamp / EtherCAT I/O, read-only diagnostics, deterministic rule engine, human approval, auditability 경계 재확인

검수:

- `docs/12_product_requirements_v1.md` 존재
- `docs/13_module_traceability_matrix.md` 존재
- `docs/14_industrial_quality_gate.md` 존재
- `docs/15_implementation_roadmap_v2.md` 존재
- README에서 운영 제품 포지셔닝 확인 가능
- visible navigation gap이 Missing / Needs implementation으로 추적됨
- language cleanup scan과 safety phrase scan 결과 확인

### PR-20 Backend Sidebar Module APIs

Owner: Codex

목표:

- sidebar hub pages가 사용할 backend list APIs 구현
- equipment, incidents, checklist runs, report approvals, safety settings의 tenant-scoped list endpoint 제공
- pagination, filtering, stable sorting 반영
- OpenAPI와 pytest coverage 추가

검수:

- `GET /api/v1/equipment`
- `GET /api/v1/incidents`
- `GET /api/v1/checklist-runs`
- `GET /api/v1/report-drafts` 또는 `GET /api/v1/approvals`
- `GET /api/v1/system/safety-settings`
- pytest 통과
- OpenAPI contract 업데이트

### PR-21 Frontend Sidebar Module Completion

Owner: Antigravity + Codex

목표:

- visible sidebar navigation이 실제 product module route로 연결되도록 구현
- `/equipment`, `/active-incidents`, `/checklists`, `/approvals`, `/settings` hub pages 추가
- backend contract가 존재하는 경우 API 연결, 아직 없는 경우 deterministic contract-shaped fallback 사용

검수:

- visible sidebar navigation 404 없음
- 각 hub page loading/empty/error/success 상태 제공
- unsafe instruction wording 없음
- frontend typecheck/build 통과

### PR-22 Navigation / Contract / E2E Hardening

Owner: Codex + Antigravity

목표:

- visible sidebar navigation smoke test
- no 404 test
- route ID visibility test
- GitHub Actions Playwright를 browser validation source of truth로 정리

검수:

- GitHub Actions Playwright green
- local WSL Ubuntu 26.04 Chromium limitation 문서화
- route/contract mismatch 없음

### PR-23 Read-Only Equipment Data Adapter

Owner: Codex

목표:

- alarm event ingestion
- I/O snapshot ingestion
- EtherCAT status snapshot ingestion
- read-only adapter abstraction
- equipment control disabled by design

검수:

- ingestion data는 tenant-scoped
- no equipment-control API
- adapter unit tests 통과

### PR-24 Incident Lifecycle / Case Management

Owner: Codex + Antigravity

목표:

- incident status model
- diagnosis/checklist/report/approval/audit linkage
- operational state transitions
- active incident hub API/UI 기반 완성

검수:

- incident lifecycle tests
- tenant isolation
- audit events for sensitive state transitions

### PR-25 Performance / Reliability Hardening

Owner: Codex + Antigravity

목표:

- pagination
- filters
- stable sorting
- loading/error states
- structured logging
- correlation IDs

검수:

- unbounded list rendering 없음
- list APIs support pagination/filtering
- CI checks pass

### PR-26 RBAC / Approval Hardening

Owner: Codex + Antigravity

목표:

- approval permissions tied to auth roles
- no UI-only role simulation
- audit logs for approval decisions
- senior/admin approval boundary 강화

검수:

- field cannot approve via UI or API
- senior/admin approval tests
- permission denied audit tests

### PR-27 Release Candidate v0.2.0

Owner: Codex + Antigravity

목표:

- no visible 404
- all checks pass
- no unsafe wording
- documented operational workflow

검수:

- frontend typecheck/build 통과
- backend pytest 통과
- GitHub Actions Playwright 통과
- requirements traceability reviewed
