# 10점 만점 평가 기준표

이 문서는 완성 기준이다. 감으로 “괜찮다”가 아니라 아래 체크를 통과해야 10점 프로젝트로 본다.

## 1. 문제 정의 - 10점

| 기준 | 만점 조건 |
|---|---|
| 현장성 | 반도체 장비 장애 대응의 실제 문제를 설명한다 |
| 제약 인식 | 보안, 장비 이질성, 안전 책임을 명확히 언급한다 |
| 대상 구체성 | Load Port / FOUP Clamp로 범위를 고정한다 |

## 2. 기술 설계 - 10점

| 기준 | 만점 조건 |
|---|---|
| 아키텍처 | frontend/backend/db/agent/evidence/audit 구조가 분리됨 |
| 데이터 모델 | tenant, equipment, alarm, io, diagnosis, evidence, report, approval, audit 존재 |
| 계약 | OpenAPI, sample data, schema가 구현과 일치 |

## 3. Agentic AI - 10점

| 기준 | 만점 조건 |
|---|---|
| agent workflow | 입력 정규화부터 보고서까지 단계별 기록 |
| 근거성 | 모든 가설에 evidence_id 연결 |
| 안전성 | 위험 조치 차단 또는 승인 요구 |
| 재현성 | LLM 없이도 결과 재현 가능 |

## 4. UI/UX - 10점

| 기준 | 만점 조건 |
|---|---|
| 화면 완성도 | Dashboard, Equipment, Diagnosis, Agent, Checklist, Report, Approval, Audit 완성 |
| 상태 처리 | loading/empty/error/forbidden/insufficient/safety-blocked 처리 |
| 고급감 | 산업용 SaaS 수준의 정돈된 정보 밀도와 시각 계층 |

## 5. 개발 품질 - 10점

| 기준 | 만점 조건 |
|---|---|
| 테스트 | pytest + Playwright E2E 포함 |
| CI | GitHub Actions green |
| 문서 | README, 사용법, 운영 workflow script, architecture docs 포함 |
| Git 운영 | PR 단위 개발 기록이 남음 |

## 6. 운영 검증 - 10점

| 기준 | 만점 조건 |
|---|---|
| 재현성 | Golden Path가 5분 안에 안정적으로 재현 |
| 논리 | 왜 이 구조를 선택했는지 방어 가능 |
| 운영 관점 | README와 screenshots만 봐도 시스템 경계와 workflow가 이해 가능 |

## 탈락 조건

아래 중 하나라도 있으면 10점 불가.

- AI 답변에 근거가 없음
- 실제 장비 제어를 흉내내며 안전 가드레일 없음
- 프로젝트가 실행되지 않음
- README 사용법으로 재현 불가
- seed data가 랜덤이라 매번 결과가 달라짐
- UI가 성공 상태만 있고 실패 상태가 없음
- GitHub에 테스트/CI 흔적이 없음
