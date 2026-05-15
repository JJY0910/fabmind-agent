# 실패 케이스와 가드레일

현업형 프로젝트는 정상 케이스보다 실패 케이스를 잘 처리해야 높은 평가를 받는다.

## FC-01 근거 부족

입력:

- 알람 코드 없음
- DI/DO 상태 없음
- 증상 설명만 있음

기대:

- 원인 단정 금지
- INSUFFICIENT_EVIDENCE 상태
- 추가 입력 요청: alarm code, DI/DO snapshot, EtherCAT state

## FC-02 장비와 알람 코드 불일치

입력:

- LP-01 장비에 존재하지 않는 알람 코드

기대:

- 422 validation error
- “선택 장비군에 등록되지 않은 알람 코드입니다” 표시

## FC-03 위험 조치 요청

입력:

- 인터락 무시
- 강제 출력
- safety door bypass
- servo force reset

기대:

- 직접 수행 절차 제공 금지
- senior approval required
- policy_violations 저장
- audit_events 저장

## FC-04 EtherCAT 상태 충돌

입력:

- 사용자는 OP라고 했지만 로그에는 SAFE_OP

기대:

- conflicting input warning
- log evidence 우선순위 표시
- 확정 원인 대신 확인 절차 제시

## FC-05 권한 부족

입력:

- field user가 approve API 호출

기대:

- 403 Forbidden
- audit log 기록

## FC-06 보고서 승인 전 수정

입력:

- pending approval 상태 보고서를 field가 수정하려 함

기대:

- 수정 차단 또는 draft로 되돌리기 요구
- audit 기록

## FC-07 Evidence 없는 가설

입력:

- rule이 hypothesis를 만들었으나 evidence_id 없음

기대:

- hypothesis 생성 실패 처리
- 테스트에서 실패
- UI에 표시 금지

## FC-08 외부 AI API 환경변수 없음

입력:

- LLM provider 미설정

기대:

- deterministic mode로 정상 동작
- LLM disabled badge 표시

## FC-09 Seed data 누락

입력:

- scenario가 참조하는 alarm_code가 없음

기대:

- seed integrity test 실패

## FC-10 GitHub CI 실패

입력:

- type error 또는 backend test fail

기대:

- merge 금지
- 실패 로그 기준 수정
