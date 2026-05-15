# AGENTS.md - FabMind Agent Development Rules

이 파일은 Codex, Antigravity, Copilot, Cursor 등 코딩 에이전트가 반드시 따라야 하는 프로젝트 운영 규칙입니다.

## 0. Product Identity

FabMind Agent is a graduation-grade, production-style, on-premise, read-only, evidence-first Agentic AI troubleshooting platform for semiconductor Load Port / FOUP Clamp / EtherCAT I/O equipment.

It is **not**:

- a generic chatbot
- a toy demo
- an unsafe equipment-control system
- a cloud-first data upload tool
- a universal semiconductor fault solver

## 1. Non-Negotiable Constraints

1. Scope is fixed to Load Port / FOUP Clamp / EtherCAT I/O.
2. No real equipment control commands.
3. No external AI API by default.
4. Every diagnosis claim must be linked to evidence.
5. Every risky recommendation must be blocked or require senior approval.
6. Deterministic rule engine must work without LLM.
7. All tenant-scoped data must include tenant_id.
8. Every backend route must have typed request/response schemas.
9. Every PR must include tests or a clear reason why tests are not applicable.
10. Never create duplicate planning folders or alternative project roots.

## 2. Canonical Repository Structure

```text
fabmind-agent/
├─ AGENTS.md
├─ README.md
├─ apps/
│  ├─ web/
│  └─ api/
├─ packages/
│  └─ shared-contracts/
├─ db/
│  ├─ migrations/
│  └─ seeds/
├─ infra/
├─ contracts/
├─ docs/
├─ prompts/
├─ quality/
├─ scripts/
└─ .github/
```

Do not create:

- `final_pack/`
- `v2_pack/`
- `new_project/`
- duplicated `src/src`
- duplicated `app/app`

## 3. Coding Standards

### Backend

- Use FastAPI.
- Use SQLAlchemy 2 style.
- Use Alembic for migrations.
- Use Pydantic v2 models.
- Prefix API routes with `/api/v1`.
- Write pytest tests for domain logic.
- Keep agent deterministic core in `apps/api/app/domain/agent/`.

### Frontend

- Use Next.js App Router.
- Use TypeScript strict mode.
- Use feature-based folders.
- No untyped `any` unless justified in code comments.
- UI must include loading, empty, error, insufficient evidence, and success states.

### Contracts

- API must match `contracts/openapi.yaml`.
- Sample data must match `contracts/sample_data_contract.md`.
- Frontend DTOs must match backend Pydantic schemas.

## 4. Agentic AI Rules

Agent workflow:

```text
input_normalization
→ alarm_lookup
→ io_signal_interpretation
→ ethercat_state_interpretation
→ evidence_retrieval
→ deterministic_rule_scoring
→ safety_guardrail
→ hypothesis_generation
→ inspection_plan_generation
→ report_draft_generation
→ audit_event_recording
```

LLM may be used only for:

- Korean explanation polishing
- report wording
- summary rewriting
- query expansion

LLM must not be the sole source of:

- root cause ranking
- safety judgment
- approval decision
- equipment action

## 5. Testing Requirements

Minimum tests:

- API health check
- tenant isolation
- RBAC check
- seed data integrity
- deterministic rule scenarios
- insufficient evidence behavior
- risky action guardrail
- report approval flow
- audit log creation
- Playwright golden path E2E

## 6. Git / PR Rules

Each PR must have:

- single responsibility
- issue/task ID
- changed files list
- test commands run
- screenshots for UI PRs
- migration notes for DB PRs
- rollback notes for risky changes

Branch naming:

```text
feature/pr-03-db-seed
feature/pr-07-diagnosis-agent
fix/evidence-link-null-state
quality/playwright-golden-path
```

## 7. Definition of Done

A task is done only when:

1. Code compiles.
2. Tests pass.
3. UI states are handled.
4. API contract is updated if needed.
5. README/docs are updated if usage changes.
6. No fabricated semiconductor data is presented as real company data.
7. No unsafe action is recommended without guardrail.

## 8. Response Format for Agents

When completing work, report:

```text
Summary:
Files changed:
Commands run:
Test result:
Screenshots/artifacts:
Remaining risks:
Next recommended PR:
```
