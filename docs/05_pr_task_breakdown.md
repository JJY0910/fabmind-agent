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
- GitHub portfolio readiness

검수:

- CI green
- demo script 성공
- README에 screenshots 포함
- 10점 scorecard 기준 충족
