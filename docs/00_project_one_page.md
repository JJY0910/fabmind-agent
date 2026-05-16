# FabMind Agent One Page

## Project Name

FabMind Agent

## Category

Semiconductor equipment troubleshooting / Agentic AI / Smart factory software

## Problem

반도체 장비 현장에서는 장애 발생 시 알람 코드, HMI 메시지, EtherCAT 통신 상태, DI/DO 신호, 매뉴얼, 과거 정비 이력을 동시에 해석해야 한다. 신입 엔지니어는 이 정보를 빠르게 연결하기 어렵고, 선임 엔지니어의 암묵지가 문서화되지 않는 문제가 있다.

## Constraints

- 회사마다 장비 구조와 알람 체계가 다름
- 실제 Fab 데이터는 외부 반출이 어려움
- AI가 직접 장비를 제어하면 안전·책임 문제가 큼
- 단순 챗봇은 근거와 재현성이 부족함

## Solution

FabMind Agent는 Load Port / FOUP Clamp / EtherCAT I/O 장비군을 대상으로, 고객사 내부망에서 동작하는 읽기 전용 Agentic AI 트러블슈팅 플랫폼이다. AI는 알람, DI/DO, EtherCAT 상태, 매뉴얼 근거, 정비 이력을 기반으로 원인 후보, 점검 순서, 보고서 초안을 생성하고, 선임 승인과 감사로그를 통해 현업형 통제를 제공한다.

## Why This Is Different

대부분의 범용 AI 도구는 대화형 답변에 머문다. FabMind Agent는 다음을 모두 포함한다.

- 표준 진단 입력 계약
- 규칙 기반 원인 추론
- 근거 그래프
- 에이전트 타임라인
- 위험 조치 차단
- 보고서 승인
- 감사로그
- GitHub CI 기반 품질 검증

## Target Users

- 반도체 장비 신입 엔지니어
- 유지보수 협력사 엔지니어
- 장비 교육센터
- 장비 자동화/SI 기업
- 운영 품질/시스템 검토자

## Core Operational Scenario

FOUP Clamp 완료 센서가 감지되지 않는 상황에서, 사용자가 알람 코드와 DI/DO 상태를 입력하면 FabMind Agent가 센서 정렬 불량을 1순위 원인으로 제시하고, 근거 문서와 I/O 상태를 연결하여 점검 체크리스트와 보고서 초안을 생성한다.
