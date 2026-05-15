# Sample Data Contract

모든 sample data는 synthetic demo data다. 실제 회사, 실제 장비, 실제 고객사 데이터를 사용하지 않는다.

## Alarm Code CSV

Columns:

```text
code,equipment_family,severity,title,description,primary_signal,recommended_first_check
```

## I/O Point CSV

Columns:

```text
code,equipment_code,direction,signal_type,description,normal_state,related_alarm
```

## Diagnosis Scenario JSON

Fields:

```text
scenario_id
title
equipment_code
alarm_code
symptom_text
ethercat_state
io_snapshot
recent_action
expected_top_cause
expected_safety_result
required_evidence_codes
```

## Manual Chunk MD

Manual chunks use frontmatter-like markers:

```text
---
evidence_id: MAN-LP-CLAMP-001
type: MANUAL_CHUNK
title: Clamp Done Sensor Check
related_alarm: LP-CLAMP-014
---
content...
```
