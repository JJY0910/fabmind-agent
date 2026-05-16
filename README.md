# FabMind Agent

**FabMind Agent** is a portfolio-grade, evidence-based Agentic AI troubleshooting platform specifically designed for semiconductor **Load Port / FOUP Clamp / EtherCAT I/O** workflows.

## Portfolio Summary
FabMind Agent bridges the gap between generic AI chatbots and the strict safety, security, and accountability requirements of semiconductor manufacturing environments. Rather than attempting to autonomously control machinery, this system acts as a field-inspired, **read-only troubleshooting copilot**. It connects HMI alarms, I/O states, and EtherCAT diagnostics to a deterministic rule engine, presenting field engineers with evidence-backed hypotheses, safety-gated inspection checklists, and a human-in-the-loop senior approval workflow. This is a rare, advanced portfolio-grade implementation showcasing a realistic application of AI in mission-critical industrial domains.

## Target Equipment Scope
- **Load Port / FOUP Clamp**: Focuses on physical interlock failures, sensor misalignments, and mechanical tolerances.
- **EtherCAT I/O**: Focuses on network state discrepancies (e.g., PRE-OP vs OP state), slave dropouts, and I/O signal mismatches.

## What Problem It Solves
In modern fabs, troubleshooting equipment requires referencing hundreds of pages of manuals, verifying live I/O states, and digging through scattered maintenance logs. Junior engineers often lack the domain expertise to connect a single alarm to a root cause, while senior engineers spend excessive time reviewing repetitive incident reports. FabMind Agent solves this by standardizing the intake (Situation Snapshot), automatically linking manuals to symptoms (Evidence Graph), and generating actionable checklists that must pass senior human approval before being formally closed.

## Safety Boundaries (What It Does NOT Do)
- **NO Equipment Control**: This system is strictly read-only. It cannot send motion commands or alter physical states.
- **NO Interlock Bypass**: It will never suggest overriding safety interlocks, forcing I/O outputs, or executing unsafe maintenance actions.
- **NO Autonomous Action**: It does not replace the Senior Engineer. Every agent-generated report requires human approval.
- **YES to Documentation & Triage**: It supports evidence gathering, checklist generation, report drafting, and full auditability.

## Architecture

- **Frontend (Next.js)**: A dark industrial SaaS UI built with TypeScript and Tailwind CSS. It uses deterministic fallback fixtures for seamless portfolio demonstrations without requiring a live backend connection.
- **Backend (FastAPI)**: Provides the REST API contract for report drafting, checklist management, diagnosis sessions, and immutable audit logs.
- **Database (PostgreSQL + pgvector)**: Handles transactional state (`schema.sql`) for sessions, runs, and approvals, prepared for vector similarity search of manuals.
- **Agent Engine**: A deterministic, rule-based engine ensuring all hypotheses and recommendations are securely backed by documented evidence, strictly avoiding LLM hallucinations.

## Golden Path Demo Flow
The platform is designed to be demonstrated sequentially through the following workflow:
1. **[Dashboard](http://localhost:3000/)**: Triage incoming alarms via the Operations Center.
2. **[Diagnosis Session](http://localhost:3000/diagnosis-sessions/LP-01-SESSION)**: Review the Agent's analysis, confidence levels, and linked evidence.
3. **[Checklist Run](http://localhost:3000/checklist-runs/RUN-LP-01)**: Execute field inspection tasks and record field notes.
4. **[Report Draft & Approval](http://localhost:3000/report-drafts/RPT-LP-01)**: Submit the final root cause analysis for Senior Engineer approval.
5. **[Audit Console](http://localhost:3000/audit-events)**: Review the immutable ledger of all system and user actions.

## Tech Stack
- **Frontend**: Next.js (App Router), TypeScript, Tailwind CSS, shadcn/ui, Playwright
- **Backend**: FastAPI, SQLAlchemy, Alembic, pytest
- **Database**: PostgreSQL (pgvector), Redis, MinIO
- **Infrastructure**: WSL2, Docker Desktop

## Repository Structure
- `/apps/web/`: Frontend Next.js application
- `/apps/api/`: Backend FastAPI application
- `/contracts/`: OpenAPI specification (`openapi.yaml`)
- `/db/`: Database schema (`schema.sql`)
- `/docs/`: Project documentation and architecture specs

## How to Validate

**Frontend Checks:**
```bash
cd apps/web
npm run typecheck
npm run build
```

**Backend Tests:**
```bash
cd apps/api
.venv/bin/pytest
```

## Implemented Milestones
- [x] PR-04: UI Design System & App Shell
- [x] PR-08: Agent Analysis UI
- [x] PR-09: Checklist Runner Contract & DB Schema
- [x] PR-10: Final Report & Approval Architecture
- [x] PR-11: FastAPI Skeleton & Mock API
- [x] PR-12: Dashboard & Audit Console UI
- [x] PR-13: Frontend-Backend API Integration
- [x] PR-14: Checklist Runner & Field Note UI
- [x] PR-15: Final Report Generation & Approval UI
- [x] PR-16: Golden Path Demo Flow Polish
- [x] PR-17: Portfolio Documentation & README Polish
