# Repository Structure

```text
fabmind-agent/
├─ AGENTS.md                         # agent rules for Codex/Antigravity
├─ README.md                         # company-facing project summary
├─ apps/
│  ├─ web/                           # Next.js frontend
│  │  ├─ src/app/
│  │  ├─ src/features/
│  │  ├─ src/components/
│  │  ├─ src/lib/
│  │  └─ tests/e2e/
│  └─ api/                           # FastAPI backend
│     ├─ app/main.py
│     ├─ app/api/v1/
│     ├─ app/domain/agent/
│     ├─ app/domain/evidence/
│     ├─ app/models/
│     ├─ app/schemas/
│     └─ tests/
├─ packages/
│  └─ shared-contracts/              # OpenAPI-generated DTOs or shared JSON schemas
├─ db/
│  ├─ migrations/
│  └─ seeds/
├─ infra/
│  ├─ docker-compose.yml
│  └─ .env.example
├─ contracts/
│  ├─ openapi.yaml
│  ├─ diagnosis_session.schema.json
│  ├─ agent_result.schema.json
│  └─ sample_data_contract.md
├─ docs/
├─ prompts/
├─ quality/
├─ scripts/
└─ .github/
   ├─ workflows/ci.yml
   ├─ ISSUE_TEMPLATE/
   └─ PULL_REQUEST_TEMPLATE.md
```

## 금지 구조

다음 구조는 만들지 않는다.

```text
old_pack/
new_pack/
backup_project/
fabmind_v2/
src/src/
app/app/
```

## 운영 원칙

- 문서와 실행 소스는 분리한다.
- 프롬프트는 prompts에 보관한다.
- 테스트 없이 기능 완료로 표시하지 않는다.
- UI 화면별 상태 정의는 docs/07_screen_state_spec.md를 기준으로 한다.
