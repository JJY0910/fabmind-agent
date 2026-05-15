# 요구정의서

## 1. 목표

FabMind Agent의 목표는 반도체 Load Port / FOUP Clamp 장비군에서 발생하는 대표 장애를 현장 엔지니어가 빠르게 분석하고 보고할 수 있도록 돕는 것이다. 제품은 실제 Fab 연결을 전제로 하지 않고, 보안과 안전을 위해 읽기 전용 진단·교육·보고 시스템으로 설계한다.

## 2. 성공 기준

졸업작품 기준 10점 만점 프로젝트가 되기 위한 최소 성공 기준은 다음과 같다.

1. 하나의 Golden Path가 끊기지 않고 동작한다.
2. AI 분석 결과는 근거와 함께 표시된다.
3. 위험 조치는 자동 권고하지 않고 승인 플로우를 요구한다.
4. LLM 없이도 deterministic rule engine으로 시연이 가능하다.
5. GitHub CI에서 backend, frontend, E2E 테스트가 실행된다.
6. README와 발표 자료만 봐도 문제-제약-해결-차별점이 이해된다.

## 3. 사용자 역할

| 역할 | 설명 | 권한 |
|---|---|---|
| Field Engineer | 현장 엔지니어 | 진단 생성, 체크리스트 수행, 보고서 초안 작성 |
| Senior Engineer | 선임 엔지니어 | 보고서 승인/반려, 위험 조치 검토 |
| Admin | 관리자 | 장비/알람/I/O/문서/사용자 관리 |
| Reviewer | 심사위원/회사 담당자 | 데모 데이터 기반 읽기 전용 체험 |

## 4. 기능 요구사항

### FR-01 인증/RBAC

- 사용자는 역할별 권한을 가진다.
- seed user는 field, senior, admin 3개를 제공한다.
- 승인 API는 senior/admin만 접근 가능하다.

### FR-02 Equipment Knowledge Base

- Load Port 장비 목록을 제공한다.
- 장비에는 equipment family, site, line, station, vendor, model, revision이 있다.
- 장비 상세 화면은 알람 코드, I/O point, EtherCAT slave, 문서 chunk, 최근 진단 이력을 보여준다.

### FR-03 Diagnosis Session

- 사용자는 장비, 알람 코드, 증상, DI/DO 상태, EtherCAT 상태, 로그, 최근 작업을 입력한다.
- 입력은 Situation Snapshot으로 정규화되어 저장된다.
- 상태는 CREATED, ANALYZING, COMPLETED, INSUFFICIENT_EVIDENCE, FAILED 중 하나다.

### FR-04 Agentic Analysis

- 입력 정규화, 알람 조회, I/O 해석, EtherCAT 상태 해석, 근거 검색, 규칙 점수화, 안전 가드레일, 가설 생성, 점검 계획 생성, 보고서 초안 생성을 단계별로 수행한다.
- 각 단계는 agent_steps에 기록된다.
- 분석 결과는 가설, confidence band, evidence link, risk level을 포함한다.

### FR-05 Evidence Graph

- 모든 원인 후보는 최소 1개 이상의 근거를 가져야 한다.
- 근거 유형은 ALARM_CODE, IO_POINT, ETHERCAT_DEVICE, MANUAL_CHUNK, MAINTENANCE_CASE, RULE_TRACE 중 하나다.
- 근거가 부족하면 INSUFFICIENT_EVIDENCE 상태를 보여준다.

### FR-06 Checklist

- Agent는 점검 절차를 단계별로 생성한다.
- 각 단계는 priority, required_role, safety_level, expected_observation을 포함한다.
- 사용자는 체크리스트 완료/스킵/메모를 기록할 수 있다.

### FR-07 Report Builder

- 보고서는 발생 일시, 장비명, 이상 증상, 추정 원인, 조치 내용, 재발 방지, 근거 요약, 담당자 의견을 포함한다.
- AI 작성 영역과 엔지니어 수정 영역을 구분한다.
- 보고서는 DRAFT, PENDING_APPROVAL, APPROVED, REJECTED 상태를 가진다.

### FR-08 Approval Flow

- Field engineer는 승인 요청을 생성할 수 있다.
- Senior engineer는 승인/반려할 수 있다.
- 결정 사유는 필수다.
- 모든 승인 이벤트는 audit_events에 기록된다.

### FR-09 Audit Console

- 진단 생성, AI 분석 실행, 보고서 생성, 승인/반려, 위험 조치 차단, 권한 오류를 감사로그로 기록한다.
- 검색 필터: event_type, actor, resource_type, date range, severity.

### FR-10 Demo Scenario Runner

- 시연 안정성을 위해 20개 이상의 seed scenario를 제공한다.
- Scenario A, B, C는 반드시 E2E 테스트에 포함한다.

## 5. 비기능 요구사항

| 항목 | 요구사항 |
|---|---|
| 보안 | 외부 AI API 기본 비활성화, tenant isolation, RBAC, audit log |
| 안정성 | LLM 없이 Golden Path 시연 가능 |
| 성능 | seed data 기준 agent analysis 3초 이내 |
| 설명가능성 | 모든 hypothesis에 evidence link 표시 |
| 유지보수성 | API contract, schema, seed, prompt가 분리되어야 함 |
| 포트폴리오성 | GitHub README, CI badge, demo script, screenshots 포함 |
