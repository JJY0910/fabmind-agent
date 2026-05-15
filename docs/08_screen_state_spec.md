# 화면별 상태 정의

모든 화면은 성공 상태만 만들면 안 된다. 현업형 UI는 데이터 없음, 로딩, 실패, 권한 없음, 근거 부족, 위험 차단 상태를 명확히 보여야 한다.

## 공통 상태

| 상태 | 의미 | UI 요구사항 |
|---|---|---|
| loading | 데이터 로딩 중 | skeleton 또는 spinner |
| empty | 표시할 데이터 없음 | 빈 상태 설명 + 다음 행동 버튼 |
| error | API 실패 | 오류 메시지 + retry |
| forbidden | 권한 없음 | 역할 기준 안내 |
| success | 정상 데이터 표시 | 핵심 액션 버튼 |

## Dashboard

| 상태 | 표시 |
|---|---|
| loading | metric card skeleton |
| empty | 아직 진단 세션 없음, 새 진단 시작 CTA |
| success | active diagnosis, pending approvals, high risk sessions, recent audit |

## Equipment Detail

| 상태 | 표시 |
|---|---|
| no_alarm_data | 알람 코드 미등록 안내 |
| no_io_data | I/O point 미등록 안내 |
| success | equipment info, alarms, I/O, EtherCAT, docs, recent sessions |

## New Diagnosis

| 상태 | 표시 |
|---|---|
| invalid_alarm | 선택 장비와 알람 코드 불일치 |
| missing_io | 필수 DI/DO 상태 누락 |
| success | submit 가능 |

## Agent Analysis

| 상태 | 표시 |
|---|---|
| analyzing | agent timeline running |
| insufficient_evidence | 근거 부족, 추가 입력 요청 |
| safety_blocked | 위험 조치 차단 banner |
| completed | hypotheses + evidence + inspection plan |
| failed | 분석 실패 원인 + retry |

## Checklist Runner

| 상태 | 표시 |
|---|---|
| pending | 시작 전 |
| in_progress | 일부 완료 |
| completed | 모든 필수 step 완료 |
| blocked | senior approval 필요 |

## Report Builder

| 상태 | 표시 |
|---|---|
| draft | field 수정 가능 |
| pending_approval | 수정 제한, senior 검토 대기 |
| approved | 승인 정보 표시 |
| rejected | 반려 사유와 수정 CTA |
