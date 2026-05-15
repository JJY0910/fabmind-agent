from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Literal

Confidence = Literal["HIGH", "MEDIUM", "LOW"]

RISKY_KEYWORDS = ["인터락 무시", "강제", "bypass", "override", "force output", "forced op", "강제 출력"]

@dataclass(frozen=True)
class Hypothesis:
    rank: int
    title: str
    reasoning: str
    confidence_band: Confidence
    evidence_ids: List[str]

@dataclass(frozen=True)
class AgentResult:
    status: str
    safety_result: str
    hypotheses: List[Hypothesis]


def run_deterministic_triage(alarm_code: str, symptom_text: str, ethercat_state: str, io_snapshot: Dict[str, bool]) -> AgentResult:
    lowered = symptom_text.lower()
    if any(keyword.lower() in lowered for keyword in RISKY_KEYWORDS):
        return AgentResult(
            status="SAFETY_BLOCKED",
            safety_result="POLICY_BLOCKED_RISKY_ACTION",
            hypotheses=[
                Hypothesis(
                    rank=1,
                    title="위험 조치 요청 감지",
                    reasoning="인터락 무시, 강제 출력, override 계열 요청은 AI가 직접 절차를 제공할 수 없습니다.",
                    confidence_band="HIGH",
                    evidence_ids=["SAFETY-POLICY-001"],
                )
            ],
        )

    if alarm_code == "LP-CLAMP-014" and io_snapshot.get("DO_CLAMP_SOL") is True and io_snapshot.get("DI_CLAMP_DONE") is False:
        return AgentResult(
            status="COMPLETED",
            safety_result="SAFE_READ_ONLY",
            hypotheses=[
                Hypothesis(
                    rank=1,
                    title="Clamp 완료 센서 위치 이탈 또는 감도 불량",
                    reasoning="Clamp command 출력은 ON이지만 clamp done 입력이 OFF입니다. 최근 센서 브라켓 조정 이력이 있다면 센서 정렬 또는 감도 문제가 우선입니다.",
                    confidence_band="HIGH",
                    evidence_ids=["LP-CLAMP-014", "DO_CLAMP_SOL", "DI_CLAMP_DONE", "MAN-LP-CLAMP-001"],
                ),
                Hypothesis(
                    rank=2,
                    title="Clamp 기구부 stroke 미완료",
                    reasoning="출력은 정상이나 완료 입력이 없으므로 기구부 걸림 또는 stroke 부족 가능성이 있습니다.",
                    confidence_band="MEDIUM",
                    evidence_ids=["LP-CLAMP-014", "MAN-LP-CLAMP-001"],
                ),
            ],
        )

    if alarm_code == "ECAT-STATE-021" or ethercat_state in {"PRE_OP", "SAFE_OP"}:
        return AgentResult(
            status="COMPLETED",
            safety_result="APPROVAL_REQUIRED_FOR_FORCE_ACTION",
            hypotheses=[
                Hypothesis(
                    rank=1,
                    title="EtherCAT slave 설정/주소/링크 문제",
                    reasoning="Slave가 OP로 전환되지 않는 상태입니다. PRE_OP/SAFE_OP에서는 링크, station alias, ESI mismatch, cable 이력을 우선 확인합니다.",
                    confidence_band="HIGH",
                    evidence_ids=["ECAT-STATE-021", "MAN-ECAT-STATE-001"],
                )
            ],
        )

    return AgentResult(
        status="INSUFFICIENT_EVIDENCE",
        safety_result="SAFE_READ_ONLY",
        hypotheses=[],
    )
