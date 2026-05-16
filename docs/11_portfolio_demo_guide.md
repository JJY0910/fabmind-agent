# Portfolio Demo Guide: FabMind Agent

This guide is designed for presenting the FabMind Agent to professors, interviewers, or technical reviewers. It highlights the core value propositions, the strict safety boundaries, and the step-by-step walkthrough of the application.

## 1. The Core Pitch
**"FabMind Agent is a field-inspired, read-only Agentic AI troubleshooting copilot for semiconductor manufacturing."**

When demonstrating, emphasize that real-world manufacturing cannot tolerate AI hallucinations or autonomous, unchecked equipment control. Explain how this project addresses those constraints by acting as an **Evidence-Based Copilot** rather than an autonomous actor.

## 2. Key Talking Points
- **Strict Safety Boundaries**: The system is strictly read-only. It explicitly blocks risky actions (like bypassing interlocks or forcing outputs) via a simulated policy engine.
- **Evidence Graph**: Every hypothesis the Agent presents is visually tied to a specific manual excerpt, alarm code, or I/O state. There are no "black box" decisions.
- **Human-in-the-Loop**: The AI assists junior engineers in gathering data and forming a checklist, but a Senior Engineer must formally approve the final report before the incident is closed.
- **Immutable Audit Trail**: All actions—from agent analysis to human approval—are logged in an immutable audit table.

## 3. Step-by-Step Walkthrough

Follow this sequence to show the complete Golden Path:

1. **The Dashboard (`/`)**
   - Point out the "Golden Path Demo" panel.
   - Mention the dark industrial SaaS UI, designed to reduce eye strain in manufacturing environments.
   - Show the metrics tracking active diagnoses, pending approvals, and guardrail blocks.
   - **Action**: Click "Start Golden Path".

2. **Diagnosis Session (`/diagnosis-sessions/LP-01-SESSION`)**
   - Highlight the **Situation Snapshot**: The I/O state (`DO_CLAMP_SOL=TRUE`, `DI_CLAMP_DONE=FALSE`).
   - Show the **Agent Timeline**: Explain how the deterministic engine processed the snapshot.
   - Point out the **Top Hypotheses** and click on the linked **Evidence**.
   - **Action**: Click "Continue to Checklist Run" via the top-right Stepper UI.

3. **Checklist Runner (`/checklist-runs/RUN-LP-01`)**
   - Explain that this is the execution phase. The Field Engineer follows the Agent's recommended inspection plan.
   - Show how the UI requires status updates (`DONE`, `BLOCKED`) and allows for field notes.
   - **Action**: Explain that the engineer has physically verified the sensor misalignment and click "Continue to Report Draft".

4. **Report & Approval (`/report-drafts/RPT-LP-01`)**
   - Show the drafted report consolidating the root cause and recommended actions.
   - Demonstrate the **Role Gate Simulator** (top right). 
   - Show that a Field Engineer cannot approve the report. Switch the role to **Senior Engineer** to unlock the Approve/Reject workflow.
   - **Action**: Click "Approve Report", then click "View in Audit Console".

5. **Audit Console (`/audit-events`)**
   - Show the immutable ledger. Point out `POLICY_BLOCKED` events where the system prevented unsafe actions in the past.
   - Conclude the demo by emphasizing accountability and traceability.

## 4. Answering Common Questions

**Q: Does this use an LLM?**
A: In this deterministic portfolio implementation, the core logic relies on a mock rule-based engine and fallback fixtures to guarantee safety and repeatable demos. In a production state, an LLM would strictly be used for semantic search (RAG over manuals) or natural language translation, never for autonomous decision-making.

**Q: Can it fix the machine automatically?**
A: No. FabMind Agent is strictly read-only by design. Semiconductor equipment operates under intense safety regulations (e.g., SEMI S2). Automatically actuating cylinders or forcing EtherCAT states without human verification risks severe physical damage or operator injury.
