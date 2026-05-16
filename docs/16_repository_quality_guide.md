# Repository Quality Guide

This guide defines repository-level expectations for FabMind Agent as an industrial field-operations troubleshooting platform.

## 1. Repository Name

Canonical repository name:

```text
fabmind-agent
```

The repository name should stay aligned with the product identity: a read-only, evidence-based troubleshooting system for Load Port / FOUP Clamp / EtherCAT I/O workflows.

## 2. Public Information Boundary

The repository must not include sensitive or real company data.

Required constraints:

- Do not include real company names, customer names, or equipment identifiers.
- Use deterministic synthetic data only.
- Do not include recipes, yield data, process conditions, or site-specific maintenance history.
- Do not claim real equipment-control capability.
- Do not include secrets or environment-specific credentials.

## 3. README Expectations

The README must allow an engineering reviewer or operations stakeholder to understand the product quickly:

1. Product mission
2. Equipment scope
3. Safety boundaries
4. Operational workflow
5. Known completeness gaps
6. Architecture
7. Validation commands
8. Current implemented modules
9. Next implementation direction

## 4. CI Expectations

`.github/workflows/ci.yml` should cover:

- backend pytest
- frontend typecheck
- frontend build
- Playwright smoke or E2E checks
- OpenAPI contract consistency where feasible

## 5. Pull Request Expectations

PRs should remain single-purpose and traceable to requirement IDs.

Recommended PR title shape:

```text
PR-20 Backend Sidebar Module APIs
PR-21 Frontend Sidebar Module Completion
PR-22 Navigation / Contract / E2E Hardening
PR-23 Read-Only Equipment Data Adapter
PR-24 Incident Lifecycle / Case Management
```

Each PR should include:

- changed files
- requirement IDs covered
- test commands run
- migration notes when schema changes
- rollback notes for risky changes
- remaining risks

## 6. Documentation Artifacts

The repository should maintain:

- product requirements
- module traceability matrix
- industrial quality gate
- implementation roadmap
- operational workflow guide
- API contract summary
- failure cases and guardrails

## 7. External Review Checklist

- Does the product remain read-only?
- Are external AI calls absent from runtime-critical analysis?
- Are equipment-control actions prohibited?
- Are visible navigation routes implemented or explicitly tracked as missing?
- Are tests and CI checks present?
- Are all datasets synthetic and deterministic?
- Can an engineer run the documented validation commands?
