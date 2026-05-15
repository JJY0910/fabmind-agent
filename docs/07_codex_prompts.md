# Codex Prompts

Codex는 backend, DB, 계약, 테스트, 리팩터링, 코드리뷰에 집중시킨다.

## Prompt 0 - Repository Review

```text
Read AGENTS.md and inspect the repository.

Do not implement yet.
Report:
1. current structure
2. missing files
3. violated constraints
4. next recommended PR
5. exact files to modify
```

## Prompt 1 - Backend Domain Seed

```text
Implement PR-02 Database Models and Seeds.

Create SQLAlchemy models, Pydantic schemas, Alembic migration, and deterministic seed script for:
- tenants
- users
- roles
- sites
- lines
- equipment_families
- equipment
- alarm_codes
- io_points
- ethercat_devices
- document_chunks
- diagnosis_scenarios
- audit_events

Constraints:
- every tenant-scoped table has tenant_id
- seed users: field, senior, admin
- at least 30 alarm codes
- at least 60 I/O points
- at least 20 diagnosis scenarios
- fixed deterministic codes, no random scenario names

Tests:
- seed creation
- equipment list query
- tenant isolation
- audit event creation

Run pytest and report results.
```

## Prompt 2 - Deterministic Agent Engine

```text
Implement PR-07 Deterministic Agent Engine.

Build:
- input normalization
- alarm lookup
- I/O interpretation
- EtherCAT interpretation
- evidence retrieval
- rule scoring
- safety guardrail
- hypothesis generation
- inspection plan generation

Do not use external LLM.

Required scenarios:
A. LP-CLAMP-014 clamp done sensor not detected
B. ECAT-STATE-021 slave PRE-OP
C. risky action request blocked

Every hypothesis must have:
- rank
- title
- reasoning
- confidence_band
- evidence_ids
- recommended_next_checks

Tests:
- Scenario A top hypothesis sensor misalignment
- Scenario B top hypothesis EtherCAT config/link issue
- Scenario C returns POLICY_BLOCKED_RISKY_ACTION
- insufficient evidence returns INSUFFICIENT_EVIDENCE
```

## Prompt 3 - API Contract Alignment

```text
Compare backend routes with contracts/openapi.yaml.

Fix mismatches for:
- request body names
- response fields
- error response schema
- auth requirements
- status codes

Add tests for:
- 401 unauthenticated
- 403 forbidden
- 404 missing resource
- 422 validation failure

Do not change product scope.
```

## Prompt 4 - Code Review Hardening

```text
Act as a strict reviewer.

Review for:
- tenant isolation leaks
- missing audit logs
- unsafe recommendations
- hallucinated evidence
- untyped frontend data
- inconsistent status enums
- tests that only check happy path
- dead code
- duplicated folders

Return a prioritized fix list, then implement the top 5 fixes.
Run tests.
```
