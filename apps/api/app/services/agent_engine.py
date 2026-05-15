from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from sqlalchemy.orm import Session

from app.domain.agent.rules import RISKY_KEYWORDS
from app.models import AgentRun, AgentStep, DiagnosisHypothesis, DiagnosisSession, EvidenceLink, InspectionPlanItem
from app.services.audit import create_audit_event


AGENT_STEP_NAMES = [
    "input_normalization",
    "alarm_lookup",
    "io_signal_interpretation",
    "ethercat_state_interpretation",
    "evidence_retrieval",
    "deterministic_rule_scoring",
    "safety_guardrail",
    "hypothesis_generation",
    "inspection_plan_generation",
]

RISK_ORDER = {"LOW": 1, "MEDIUM": 2, "HIGH": 3, "CRITICAL": 4}


@dataclass(frozen=True)
class EvidenceSpec:
    source_type: str
    source_code: str
    title: str
    excerpt: str
    relevance_reason: str


@dataclass(frozen=True)
class HypothesisSpec:
    rank: int
    title: str
    reasoning: str
    confidence_band: str
    risk_level: str
    evidence_codes: list[str]
    recommended_next_checks: list[str]


@dataclass(frozen=True)
class InspectionPlanSpec:
    item_order: int
    title: str
    instruction: str
    expected_observation: str | None
    safety_level: str
    evidence_codes: list[str]


@dataclass(frozen=True)
class AnalysisPlan:
    status: str
    safety_result: str
    session_status: str
    risk_level: str
    steps: list[dict[str, Any]]
    hypotheses: list[HypothesisSpec]
    inspection_plan_items: list[InspectionPlanSpec]


EVIDENCE_CATALOG: dict[str, EvidenceSpec] = {
    "LP-CLAMP-014": EvidenceSpec(
        source_type="alarm_code",
        source_code="LP-CLAMP-014",
        title="Clamp done signal missing after clamp command",
        excerpt="The alarm describes a clamp command state where the expected clamp done input is not detected.",
        relevance_reason="The session alarm directly matches the clamp completion failure rule.",
    ),
    "DO_CLAMP_SOL": EvidenceSpec(
        source_type="io_point",
        source_code="DO_CLAMP_SOL",
        title="Clamp solenoid command output",
        excerpt="The clamp command output indicates that the controller requested clamp motion.",
        relevance_reason="A true command output narrows the fault toward feedback, sensor, or mechanical completion.",
    ),
    "DI_CLAMP_DONE": EvidenceSpec(
        source_type="io_point",
        source_code="DI_CLAMP_DONE",
        title="Clamp done feedback input",
        excerpt="The clamp done input should turn true after successful clamp completion.",
        relevance_reason="A false done input while command is true is the core mismatch in the clamp rule.",
    ),
    "MAN-LP-CLAMP-001": EvidenceSpec(
        source_type="procedure",
        source_code="MAN-LP-CLAMP-001",
        title="Load Port clamp inspection guidance",
        excerpt="Read-only inspection should focus on clamp sensor alignment, bracket condition, cable seating, and stroke evidence.",
        relevance_reason="The inspection guidance supports non-control checks for clamp feedback failures.",
    ),
    "ECAT-STATE-021": EvidenceSpec(
        source_type="alarm_code",
        source_code="ECAT-STATE-021",
        title="EtherCAT state transition fault",
        excerpt="The alarm indicates that an EtherCAT slave did not reach the expected operational state.",
        relevance_reason="The session alarm or EtherCAT state matches the communication/state transition rule.",
    ),
    "ETHERCAT_STATE": EvidenceSpec(
        source_type="session_input",
        source_code="ETHERCAT_STATE",
        title="Reported EtherCAT state",
        excerpt="PRE_OP and SAFE_OP are transitional states and do not represent a fully operational slave.",
        relevance_reason="The reported state is used as direct evidence for the EtherCAT rule.",
    ),
    "MAN-ECAT-STATE-001": EvidenceSpec(
        source_type="procedure",
        source_code="MAN-ECAT-STATE-001",
        title="EtherCAT read-only communication checks",
        excerpt="Read-only checks include link LEDs, cable seating, expected slave order, station alias, and configuration mismatch review.",
        relevance_reason="The inspection guidance supports non-control checks before any recovery action.",
    ),
    "LP-DOOR-007": EvidenceSpec(
        source_type="alarm_code",
        source_code="LP-DOOR-007",
        title="FOUP door or interlock chain symptom",
        excerpt="Door closed and interlock chain signals must be consistent before clamp or transfer steps proceed.",
        relevance_reason="Door or interlock symptoms match the FOUP door/interlock rule.",
    ),
    "DI_DOOR_CLOSED": EvidenceSpec(
        source_type="io_point",
        source_code="DI_DOOR_CLOSED",
        title="FOUP door closed feedback input",
        excerpt="The door closed input is expected to reflect the physical door closed condition.",
        relevance_reason="A false or suspect door feedback input supports a door sensor/interlock hypothesis.",
    ),
    "SAFETY-POLICY-001": EvidenceSpec(
        source_type="safety_policy",
        source_code="SAFETY-POLICY-001",
        title="No bypass or forced machine-control guidance",
        excerpt="The system must block bypass, override, forced output, and interlock-defeating instructions.",
        relevance_reason="The detected text requests or implies an unsafe action that must be blocked.",
    ),
}


def analyze_diagnosis_session(
    db: Session,
    *,
    session: DiagnosisSession,
    actor_user_id: uuid.UUID,
) -> AgentRun:
    create_audit_event(
        db,
        tenant_id=session.tenant_id,
        actor_user_id=actor_user_id,
        event_type="AGENT_ANALYSIS_STARTED",
        resource_type="diagnosis_session",
        resource_id=session.id,
        severity="INFO",
        payload={"alarm_code": session.alarm_code, "mode": "DETERMINISTIC"},
    )

    session.status = "ANALYZING"
    plan = build_analysis_plan(session)
    run = AgentRun(
        tenant_id=session.tenant_id,
        session_id=session.id,
        status=plan.status,
        mode="DETERMINISTIC",
        safety_result=plan.safety_result,
        completed_at=datetime.now(UTC),
    )
    db.add(run)
    db.flush()

    for step in plan.steps:
        db.add(
            AgentStep(
                tenant_id=session.tenant_id,
                agent_run_id=run.id,
                step_order=step["step_order"],
                name=step["name"],
                status=step["status"],
                summary=step["summary"],
                details=step["details"],
            )
        )

    for hypothesis_spec in plan.hypotheses:
        hypothesis = DiagnosisHypothesis(
            tenant_id=session.tenant_id,
            agent_run_id=run.id,
            rank=hypothesis_spec.rank,
            title=hypothesis_spec.title,
            reasoning=hypothesis_spec.reasoning,
            confidence_band=hypothesis_spec.confidence_band,
            risk_level=hypothesis_spec.risk_level,
            recommended_next_checks=hypothesis_spec.recommended_next_checks,
        )
        db.add(hypothesis)
        db.flush()
        for evidence_code in hypothesis_spec.evidence_codes:
            evidence = _evidence_for_code(evidence_code)
            db.add(
                EvidenceLink(
                    tenant_id=session.tenant_id,
                    hypothesis_id=hypothesis.id,
                    source_type=evidence.source_type,
                    source_code=evidence.source_code,
                    title=evidence.title,
                    excerpt=evidence.excerpt,
                    relevance_reason=evidence.relevance_reason,
                )
            )

    for item in plan.inspection_plan_items:
        db.add(
            InspectionPlanItem(
                tenant_id=session.tenant_id,
                agent_run_id=run.id,
                item_order=item.item_order,
                title=item.title,
                instruction=item.instruction,
                expected_observation=item.expected_observation,
                safety_level=item.safety_level,
                evidence_codes=item.evidence_codes,
            )
        )

    session.status = plan.session_status
    session.risk_level = _max_risk(session.risk_level, plan.risk_level)

    if plan.status == "SAFETY_BLOCKED":
        create_audit_event(
            db,
            tenant_id=session.tenant_id,
            actor_user_id=actor_user_id,
            event_type="AGENT_RISKY_ACTION_BLOCKED",
            resource_type="diagnosis_session",
            resource_id=session.id,
            severity="SECURITY",
            payload={"safety_result": plan.safety_result},
        )
    elif plan.status == "INSUFFICIENT_EVIDENCE":
        create_audit_event(
            db,
            tenant_id=session.tenant_id,
            actor_user_id=actor_user_id,
            event_type="AGENT_ANALYSIS_INSUFFICIENT_EVIDENCE",
            resource_type="diagnosis_session",
            resource_id=session.id,
            severity="WARNING",
            payload={"alarm_code": session.alarm_code},
        )

    create_audit_event(
        db,
        tenant_id=session.tenant_id,
        actor_user_id=actor_user_id,
        event_type="AGENT_ANALYSIS_COMPLETED",
        resource_type="agent_run",
        resource_id=run.id,
        severity="INFO" if plan.status == "COMPLETED" else "WARNING",
        payload={"status": plan.status, "safety_result": plan.safety_result},
    )
    db.flush()
    return run


def build_analysis_plan(session: DiagnosisSession) -> AnalysisPlan:
    risky_match = _find_risky_keyword(session)
    if risky_match is not None:
        hypothesis = HypothesisSpec(
            rank=1,
            title="Unsafe action request blocked",
            reasoning=(
                "The session text includes a bypass, override, forced-output, or interlock-defeating request. "
                "The deterministic engine blocks machine-control guidance and returns only advisory safety handling."
            ),
            confidence_band="HIGH",
            risk_level="CRITICAL",
            evidence_codes=["SAFETY-POLICY-001"],
            recommended_next_checks=[
                "Stop using the requested unsafe action path.",
                "Escalate to a senior engineer before any recovery action is attempted.",
                "Collect read-only alarm, I/O, and EtherCAT evidence for a safer diagnosis.",
            ],
        )
        return AnalysisPlan(
            status="SAFETY_BLOCKED",
            safety_result="POLICY_BLOCKED_RISKY_ACTION",
            session_status="CLOSED",
            risk_level="CRITICAL",
            steps=_steps(
                matched_rules=["SAFETY_BLOCKED"],
                step_status="BLOCKED",
                summary="Risky action text was detected and blocked before hypothesis generation.",
                details={"matched_keyword": risky_match},
            ),
            hypotheses=[hypothesis],
            inspection_plan_items=[
                InspectionPlanSpec(
                    item_order=1,
                    title="Escalate unsafe request",
                    instruction="Record the unsafe request context and escalate to a senior engineer for review.",
                    expected_observation="A senior review path is opened without bypass or forced-control instructions.",
                    safety_level="APPROVAL_REQUIRED",
                    evidence_codes=["SAFETY-POLICY-001"],
                )
            ],
        )

    hypotheses: list[HypothesisSpec] = []
    inspection_items: list[InspectionPlanSpec] = []

    if _is_clamp_sensor_mismatch(session):
        hypotheses.append(
            HypothesisSpec(
                rank=len(hypotheses) + 1,
                title="Clamp done sensor misalignment or sensor failure",
                reasoning=(
                    "LP-CLAMP-014 is present while DO_CLAMP_SOL is true and DI_CLAMP_DONE is false. "
                    "That evidence points first to clamp done feedback alignment, sensitivity, cabling, or sensor failure."
                ),
                confidence_band="HIGH",
                risk_level="MEDIUM",
                evidence_codes=["LP-CLAMP-014", "DO_CLAMP_SOL", "DI_CLAMP_DONE", "MAN-LP-CLAMP-001"],
                recommended_next_checks=[
                    "Inspect the clamp done sensor LED and mounting alignment without commanding motion.",
                    "Check sensor cable seating and bracket movement evidence.",
                    "Compare clamp done feedback with the physical clamp state.",
                ],
            )
        )
        inspection_items.append(
            InspectionPlanSpec(
                item_order=len(inspection_items) + 1,
                title="Read-only clamp sensor inspection",
                instruction="Inspect the clamp done sensor LED, mounting bracket, and cable seating while keeping the tool in a safe non-control state.",
                expected_observation="A misaligned sensor, loose bracket, disconnected cable, or missing feedback condition is identified.",
                safety_level="CAUTION",
                evidence_codes=["LP-CLAMP-014", "DO_CLAMP_SOL", "DI_CLAMP_DONE"],
            )
        )

    if _is_ethercat_state_issue(session):
        hypotheses.append(
            HypothesisSpec(
                rank=len(hypotheses) + 1,
                title="EtherCAT slave communication or state transition problem",
                reasoning=(
                    "The reported EtherCAT state is PRE_OP or SAFE_OP, or the ECAT-STATE-021 alarm is present. "
                    "This indicates the slave has not reached OP and should be investigated through read-only communication evidence."
                ),
                confidence_band="HIGH",
                risk_level="HIGH",
                evidence_codes=["ECAT-STATE-021", "ETHERCAT_STATE", "MAN-ECAT-STATE-001"],
                recommended_next_checks=[
                    "Review EtherCAT slave state, link LED, cable seating, and expected slave order.",
                    "Compare configured station alias and device identity against the expected configuration.",
                    "Escalate before any reset, force, or recovery action.",
                ],
            )
        )
        inspection_items.append(
            InspectionPlanSpec(
                item_order=len(inspection_items) + 1,
                title="Read-only EtherCAT communication review",
                instruction="Review slave state, link indicators, cable seating, configured alias, and device identity without issuing recovery commands.",
                expected_observation="A link, identity, address, or configuration mismatch is confirmed or ruled out.",
                safety_level="APPROVAL_REQUIRED",
                evidence_codes=["ECAT-STATE-021", "ETHERCAT_STATE"],
            )
        )

    if _is_door_or_interlock_issue(session):
        hypotheses.append(
            HypothesisSpec(
                rank=len(hypotheses) + 1,
                title="FOUP door sensor or interlock chain issue",
                reasoning=(
                    "The symptom, alarm, or I/O snapshot references a FOUP door or interlock condition. "
                    "The first safe explanation is an inconsistent door feedback or interlock chain signal."
                ),
                confidence_band="MEDIUM",
                risk_level="HIGH",
                evidence_codes=["LP-DOOR-007", "DI_DOOR_CLOSED", "SAFETY-POLICY-001"],
                recommended_next_checks=[
                    "Inspect door closed feedback and interlock chain status in read-only diagnostics.",
                    "Check for mechanical obstruction or sensor alignment evidence.",
                    "Do not bypass the interlock chain.",
                ],
            )
        )
        inspection_items.append(
            InspectionPlanSpec(
                item_order=len(inspection_items) + 1,
                title="Read-only FOUP door and interlock inspection",
                instruction="Inspect door closed feedback, interlock chain indicators, and visible obstruction evidence without bypassing the safety chain.",
                expected_observation="Door feedback, interlock signal, or mechanical obstruction evidence explains the symptom.",
                safety_level="APPROVAL_REQUIRED",
                evidence_codes=["LP-DOOR-007", "DI_DOOR_CLOSED", "SAFETY-POLICY-001"],
            )
        )

    if not hypotheses:
        return AnalysisPlan(
            status="INSUFFICIENT_EVIDENCE",
            safety_result="SAFE_READ_ONLY",
            session_status="INSUFFICIENT_EVIDENCE",
            risk_level=session.risk_level,
            steps=_steps(
                matched_rules=[],
                step_status="NEEDS_MORE_EVIDENCE",
                summary="No deterministic rule had enough matching evidence to produce a hypothesis.",
                details={"required_inputs": ["alarm_code", "ethercat_state", "io_snapshot", "log_excerpt"]},
            ),
            hypotheses=[],
            inspection_plan_items=[
                InspectionPlanSpec(
                    item_order=1,
                    title="Collect minimum diagnostic evidence",
                    instruction="Collect the current alarm, EtherCAT state, relevant DI/DO snapshot, and a short log excerpt before rerunning analysis.",
                    expected_observation="The next analysis has enough evidence to match a deterministic rule.",
                    safety_level="NORMAL",
                    evidence_codes=[],
                )
            ],
        )

    risk_level = _highest_risk([hypothesis.risk_level for hypothesis in hypotheses])
    return AnalysisPlan(
        status="COMPLETED",
        safety_result="APPROVAL_REQUIRED_FOR_FORCE_ACTION" if risk_level in {"HIGH", "CRITICAL"} else "SAFE_READ_ONLY",
        session_status="ANALYSIS_READY",
        risk_level=risk_level,
        steps=_steps(
            matched_rules=[hypothesis.title for hypothesis in hypotheses],
            step_status="COMPLETED",
            summary="Deterministic rules matched the session evidence and produced ranked hypotheses.",
            details={"hypothesis_count": len(hypotheses)},
        ),
        hypotheses=hypotheses,
        inspection_plan_items=inspection_items,
    )


def _steps(
    *,
    matched_rules: list[str],
    step_status: str,
    summary: str,
    details: dict[str, Any],
) -> list[dict[str, Any]]:
    steps: list[dict[str, Any]] = []
    for index, name in enumerate(AGENT_STEP_NAMES, start=1):
        steps.append(
            {
                "step_order": index,
                "name": name,
                "status": step_status,
                "summary": summary if name in {"deterministic_rule_scoring", "safety_guardrail"} else f"{name} completed.",
                "details": {"matched_rules": matched_rules, **details},
            }
        )
    return steps


def _is_clamp_sensor_mismatch(session: DiagnosisSession) -> bool:
    return (
        session.alarm_code == "LP-CLAMP-014"
        and _io_value(session, "DO_CLAMP_SOL") is True
        and _io_value(session, "DI_CLAMP_DONE") is False
    )


def _is_ethercat_state_issue(session: DiagnosisSession) -> bool:
    state = (session.ethercat_state or "").upper()
    return session.alarm_code == "ECAT-STATE-021" or state in {"PRE_OP", "SAFE_OP"}


def _is_door_or_interlock_issue(session: DiagnosisSession) -> bool:
    combined_text = _combined_text(session)
    return (
        session.alarm_code == "LP-DOOR-007"
        or "door" in combined_text
        or "interlock" in combined_text
        or _io_value(session, "DI_DOOR_CLOSED") is False
    )


def _find_risky_keyword(session: DiagnosisSession) -> str | None:
    combined_text = _combined_text(session)
    for keyword in RISKY_KEYWORDS:
        if keyword.lower() in combined_text:
            return keyword
    return None


def _combined_text(session: DiagnosisSession) -> str:
    return " ".join(
        value.lower()
        for value in [session.symptom_summary, session.log_excerpt, session.recent_action]
        if value
    )


def _io_value(session: DiagnosisSession, code: str) -> bool | None:
    snapshot = session.io_snapshot or {}
    if code in snapshot:
        return snapshot[code]
    lowered_code = code.lower()
    for key, value in snapshot.items():
        if key.lower() == lowered_code:
            return value
    return None


def _evidence_for_code(code: str) -> EvidenceSpec:
    return EVIDENCE_CATALOG.get(
        code,
        EvidenceSpec(
            source_type="session_input",
            source_code=code,
            title=code,
            excerpt=f"Session input referenced {code}.",
            relevance_reason="The deterministic rule referenced this session input.",
        ),
    )


def _highest_risk(levels: list[str]) -> str:
    if not levels:
        return "LOW"
    return max(levels, key=lambda level: RISK_ORDER[level])


def _max_risk(existing: str, candidate: str) -> str:
    return existing if RISK_ORDER[existing] >= RISK_ORDER[candidate] else candidate
