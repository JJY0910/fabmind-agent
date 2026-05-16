# Antigravity Mission Prompts

Antigravity는 UI, 브라우저 검증, 화면 품질, 사용성 확인에 집중시킨다. 전체를 한 번에 맡기지 말고 PR 단위로 맡긴다.

## Mission 0 - Repository Foundation

```text
You are building FabMind Agent.

Goal: initialize an executable monorepo scaffold for an industrial troubleshooting platform.

Canonical structure:
apps/web
apps/api
packages/shared-contracts
db/migrations
db/seeds
infra
contracts
docs
quality
scripts
.github

Create:
1. Next.js + TypeScript frontend in apps/web
2. FastAPI backend in apps/api
3. Docker Compose in infra/docker-compose.yml for PostgreSQL, Redis, MinIO
4. Root README with Windows + WSL2 instructions
5. /api/v1/health endpoint
6. Web login placeholder
7. No duplicate pack folders

Constraints:
- On-premise by default
- No external AI API by default
- Read-only troubleshooting system
- Load Port / FOUP Clamp / EtherCAT I/O scope only

After completion, report files changed, commands run, browser verification, and remaining issues.
```

## Mission 1 - High Quality UI Shell

```text
Build the FabMind Agent UI shell.

Design direction:
- high-end industrial SaaS
- dark navy/graphite background
- cyan/amber/red status accents
- semiconductor equipment dashboard feeling
- Korean interface
- no childish gradients

Required screens:
1. Login
2. Dashboard
3. Equipment list
4. Equipment detail
5. New diagnosis
6. Agent analysis
7. Checklist runner
8. Report builder
9. Approval queue
10. Audit console

Every screen must have loading, empty, error, and success states.
Do not connect unvalidated random data. Use deterministic seed contracts.
Capture screenshots after implementation.
```

## Mission 2 - Agent Analysis Screen

```text
Focus only on Agent Analysis screen.

This is the most important screen in the project.

Required UI zones:
- session header
- risk banner
- agent timeline
- top 3 hypothesis cards
- confidence band: HIGH / MEDIUM / LOW, not arbitrary decimals
- evidence drawer
- input snapshot panel
- inspection plan panel
- insufficient evidence state
- safety blocked state

Use Scenario A, B, C from docs/04_golden_path_spec.md.
Verify in browser.
```

## Mission 3 - Final E2E Workflow Verification

```text
Run the final operational workflow as a reviewer.

Check:
1. Login as field engineer
2. Open LP-01 equipment
3. Create Scenario A diagnosis
4. Run analysis
5. Open evidence drawer
6. Complete checklist steps
7. Generate report
8. Request approval
9. Login as senior engineer
10. Approve report
11. Confirm audit log

Capture screenshots and list any UX friction.
Do not mark complete until all steps are reproducible.
```
