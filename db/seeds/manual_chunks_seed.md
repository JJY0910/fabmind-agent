---
evidence_id: MAN-LP-CLAMP-001
type: MANUAL_CHUNK
title: Clamp Done Sensor Check
related_alarm: LP-CLAMP-014
---
When clamp command is issued and clamp done input is not detected, inspect sensor LED, bracket alignment, cable connection, and mechanical clamp stroke. Do not force clamp motion while interlock condition is unclear.

---
evidence_id: MAN-ECAT-STATE-001
type: MANUAL_CHUNK
title: EtherCAT Slave State Troubleshooting
related_alarm: ECAT-STATE-021
---
If a slave remains in PRE_OP or SAFE_OP, verify link LED, station alias, ESI file compatibility, slave scan result, and cable connection history before attempting any forced transition.

---
evidence_id: SAFETY-POLICY-001
type: SAFETY_POLICY
title: Interlock and Forced Output Policy
related_alarm: ALL
---
Interlock bypass, forced output, safety door override, and direct actuator movement must not be recommended by the AI system. The system may suggest read-only inspection and require senior approval for risky procedures.
