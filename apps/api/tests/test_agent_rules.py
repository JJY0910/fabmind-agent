from app.domain.agent.rules import run_deterministic_triage


def test_scenario_a_clamp_sensor_misalignment():
    result = run_deterministic_triage(
        alarm_code="LP-CLAMP-014",
        symptom_text="FOUP clamp command 후 clamp done sensor가 들어오지 않음",
        ethercat_state="OP",
        io_snapshot={"DO_CLAMP_SOL": True, "DI_CLAMP_DONE": False, "DI_FOUP_PRESENT": True},
    )
    assert result.status == "COMPLETED"
    assert result.hypotheses[0].confidence_band == "HIGH"
    assert "센서" in result.hypotheses[0].title
    assert result.hypotheses[0].evidence_ids


def test_scenario_b_ethercat_preop():
    result = run_deterministic_triage(
        alarm_code="ECAT-STATE-021",
        symptom_text="EtherCAT slave 3번이 OP로 전환되지 않음",
        ethercat_state="PRE_OP",
        io_snapshot={},
    )
    assert result.status == "COMPLETED"
    assert "EtherCAT" in result.hypotheses[0].title
    assert result.safety_result == "APPROVAL_REQUIRED_FOR_FORCE_ACTION"


def test_scenario_c_risky_action_blocked():
    result = run_deterministic_triage(
        alarm_code="LP-CLAMP-014",
        symptom_text="인터락 무시하고 강제로 clamp 동작시키면 되지 않나요?",
        ethercat_state="OP",
        io_snapshot={"DO_CLAMP_SOL": False},
    )
    assert result.status == "SAFETY_BLOCKED"
    assert result.safety_result == "POLICY_BLOCKED_RISKY_ACTION"
    assert result.hypotheses[0].evidence_ids == ["SAFETY-POLICY-001"]
