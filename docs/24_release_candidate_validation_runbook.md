# Release Candidate Validation Runbook

## Purpose

This runbook defines the local and CI validation procedure for the FabMind Agent v0.2.0 release candidate. The goal is to confirm the operational acceptance baseline without adding product features or changing runtime behavior.

## Preconditions

- Work from the repository root.
- Start from a clean `main` branch that is up to date with `origin/main`.
- Create the release-candidate branch only after the clean baseline is confirmed.
- Keep equipment integration read-only and keep scope limited to Load Port / FOUP Clamp / EtherCAT I/O.

## 1. Clean Repo Verification

```bash
git status --short --branch
git checkout main
git pull origin main
git status --short --branch
git checkout -b pr-30-release-candidate-v0-2-0-packaging
```

Expected output:

- `main` is clean before branch creation.
- `origin/main` is up to date.
- The working branch is `pr-30-release-candidate-v0-2-0-packaging`.

## 2. Backend Validation Commands

```bash
cd apps/api
.venv/bin/pytest tests/test_pr30_release_candidate_packaging.py
.venv/bin/pytest
```

Expected output:

- Targeted PR-30 static release packaging checks pass.
- Full backend pytest suite passes.
- The final pytest line records the current passing test count for release notes.

## 3. Frontend Validation Commands

```bash
cd apps/web
npm run typecheck
npm run build
```

Expected output:

- TypeScript strict validation succeeds.
- Next.js production build succeeds.
- No runtime UI behavior changes are required for this PR.

If Windows `npm` is picked up from WSL PATH and native package resolution fails, rerun with the WSL Node/NVM path. Do not change project code for that environment issue.

WSL/NVM fallback:

```bash
cd apps/web
PATH=/home/abcde/.nvm/versions/node/v20.20.2/bin:$PATH npm run typecheck
PATH=/home/abcde/.nvm/versions/node/v20.20.2/bin:$PATH npm run build
```

## 4. Diff Check

```bash
cd ~/projects/fabmind-agent
git diff --check
```

Expected output:

- No whitespace errors.
- Diff is limited to release notes, validation runbook, README/roadmap/audit documentation, and the static PR-30 packaging test.

## 5. Product Language Scan

Run the repository's restricted product-language grep from the PR validation checklist against:

- `apps/web/src`
- `README.md`
- `docs`

```bash
cd ~/projects/fabmind-agent
grep -RniE "[d]emo|[p]ortfolio|[p]rofessor|[i]nterviewer|[p]resentation|[t]oy|[f]ake|[m]ock-only|[s]imulator" apps/web/src README.md docs || true
```

Expected output:

- No matches.
- If a match appears in user-facing documentation or UI, revise the wording before merge.

## 6. Safety Phrase Scan

Run the repository's restricted safety-phrase grep from the PR validation checklist against:

- `README.md`
- `docs`
- `apps/web/src`
- `apps/api/app`
- `apps/api/tests`

```bash
cd ~/projects/fabmind-agent
grep -RniE "[L]octite|re[-]tighten|force[[:space:]]output|write[[:space:]]output|bypass[[:space:]]interlock|override[[:space:]]interlock|servo[[:space:]]on|autonomous[[:space:]]repair|autonomous[[:space:]]equipment[[:space:]]control|강제[[:space:]]on" README.md docs apps/web/src apps/api/app apps/api/tests || true
```

Expected output:

- No unsafe wording in README, docs, frontend UI, OpenAPI summaries, or normal API response text.
- Existing backend guardrail code and backend negative tests may contain blocked-intent wording only when asserting that unsafe requests are rejected.

## 7. GitHub Actions Checks

GitHub Actions remains the Playwright source of truth for browser validation.

Required checks:

- Backend tests.
- Frontend typecheck.
- Frontend build.
- Playwright smoke.

Expected output:

- All required CI jobs pass on the PR branch.
- Playwright artifacts are available from GitHub Actions if browser validation fails.

## 8. Known WSL Ubuntu 26.04 Playwright Limitation

Local browser execution in WSL Ubuntu 26.04 may be constrained by browser dependency and display environment behavior. Treat GitHub Actions Playwright as the authoritative browser validation result for release-candidate gating.

Local backend and frontend non-browser checks should still run successfully.

## 9. Cleanup Generated Files

```bash
cd ~/projects/fabmind-agent
rm -f apps/web/tsconfig.tsbuildinfo
git restore apps/web/next-env.d.ts 2>/dev/null || true
rm -rf apps/web/.next
find apps/api -type d -name "__pycache__" -prune -exec rm -rf {} +
rm -rf apps/api/.pytest_cache
```

Expected output:

- Generated build/test artifacts are removed.
- Source changes remain limited to PR-30 packaging files.

## 10. Merge/Cleanup Procedure

Before requesting merge:

- Confirm the branch contains no runtime application behavior changes.
- Confirm release notes and this runbook reflect the latest validation result.
- Confirm product-language and safety-phrase scans have no user-facing matches.
- Confirm known limitations are still documented.
- Confirm there is no final deployment certification claim.

After merge:

- Delete the PR branch through the repository hosting UI or standard branch cleanup flow.
- Keep release-candidate documentation in `docs/` as the baseline record.
- Use the next backlog item to continue hardening rather than expanding PR-30 scope.

## 11. Release Decision Checklist

- [ ] Release notes identify FabMind Agent v0.2.0 Release Candidate.
- [ ] Release status is release candidate / operational acceptance baseline.
- [ ] Scope remains Load Port / FOUP Clamp / EtherCAT I/O.
- [ ] No equipment-control capability is introduced.
- [ ] No external AI/LLM runtime dependency is introduced.
- [ ] Deterministic rule engine remains the source of core analysis.
- [ ] Human approval remains required for final report decisions.
- [ ] Audit logging remains documented and validated.
- [ ] Backend targeted PR-30 pytest passes.
- [ ] Full backend pytest passes and count is recorded.
- [ ] Frontend typecheck and build pass.
- [ ] GitHub Actions Playwright result is reviewed.
- [ ] Known limitations and next backlog remain visible.
