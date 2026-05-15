# FabMind Agent

**FabMind Agent**는 반도체 **Load Port / FOUP Clamp / EtherCAT I/O** 장비군의 장애 대응을 위해 설계한 **온프레미스·읽기 전용·근거 기반 Agentic AI 트러블슈팅 플랫폼**입니다.

이 프로젝트는 범용 챗봇이 아닙니다. 장비 알람, EtherCAT 상태, DI/DO 신호, 매뉴얼 근거, 정비 이력, 승인 흐름, 감사 로그를 하나의 진단 세션으로 묶어 **신입/현장 엔지니어의 원인 추정, 점검 절차 수립, 보고서 작성**을 지원합니다.

## 한 줄 가치

> 반도체 현장의 보안·호환성·안전 책임 문제를 우회하지 않고, **내부망 + 읽기 전용 + 사람 승인 + 근거 추적**으로 정면 설계한 트러블슈팅 AI 시스템.

## 독자성

FabMind Agent의 독자성은 “AI가 모든 장비를 알아서 고친다”가 아니라 아래 5개를 하나의 완성된 제품 흐름으로 묶는 데 있습니다.

1. **Situation Snapshot Contract**: HMI 알람, EtherCAT state, DI/DO, 최근 작업, 로그를 표준 진단 입력으로 정규화
2. **Safety-Gated Deterministic Triage**: 위험 조치는 차단하고, 판단은 규칙/근거 기반으로 수행
3. **Evidence Graph / Evidence Ledger**: 모든 원인 후보와 점검 단계에 근거 문서·알람·I/O·정비 이력을 연결
4. **Agent Timeline UI**: AI가 어떤 단계로 판단했는지 화면에서 재현 가능하게 표시
5. **Human Approval + Audit Trail**: AI 결과는 조치 명령이 아니라 승인 가능한 보고서/점검안으로만 남김

## Golden Path

```text
로그인
→ Dashboard
→ Equipment 선택
→ New Diagnosis 생성
→ Agent Analysis 실행
→ 원인 후보 TOP 3 + 근거 표시
→ 점검 체크리스트 생성
→ 보고서 초안 생성
→ Senior 승인/반려
→ Audit Log 기록
```

## 실행 원칙

- 외부 AI API 기본 사용 금지
- 실제 장비 제어 기능 금지
- Load Port / FOUP Clamp / EtherCAT I/O 범위만 지원
- LLM 없이도 deterministic rule engine으로 시연 가능해야 함
- 모든 AI성 출력에는 Evidence ID가 있어야 함
- GitHub CI가 통과하지 않으면 완료로 보지 않음

## 기술 스택

- Frontend: Next.js + TypeScript + Tailwind + shadcn 스타일 컴포넌트
- Backend: FastAPI + SQLAlchemy + Alembic
- Database: PostgreSQL + pgvector
- Storage: MinIO
- Queue/Cache: Redis
- Testing: pytest + Playwright
- Dev: Windows + WSL2 + Docker Desktop
- Agent Tools: Antigravity for UI/browser verification, Codex for backend/refactor/test/code review

## 빠른 시작

```bash
# 1. 저장소 클론
 git clone <your-repo-url> fabmind-agent
 cd fabmind-agent

# 2. WSL2 Ubuntu에서 실행 권장
 cp infra/.env.example infra/.env
 docker compose -f infra/docker-compose.yml up -d

# 3. API
 cd apps/api
 uv sync
 uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 4. Web
 cd ../web
 npm install
 npm run dev
```

접속:

- Web: http://localhost:3000
- API: http://localhost:8000/docs
- Health: http://localhost:8000/api/v1/health

## 졸업작품 발표 핵심 문장

> 실제 반도체 현장은 보안, 장비 이질성, 안전 책임 때문에 범용 AI 자동분석이 어렵습니다. 그래서 FabMind Agent는 특정 장비군을 대상으로 내부망, 읽기 전용, 근거 기반, 사람 승인 구조를 적용했습니다.

## 회사/면접관에게 보여줄 때

이 저장소에서 가장 먼저 보게 할 파일:

1. `README.md`
2. `docs/00_project_one_page.md`
3. `docs/01_requirements_definition.md`
4. `docs/02_decision_rationale.md`
5. `docs/04_golden_path_spec.md`
6. `docs/10_scorecard_10_of_10.md`
7. `.github/workflows/ci.yml`
