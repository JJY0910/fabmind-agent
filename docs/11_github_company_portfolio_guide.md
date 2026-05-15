# GitHub 회사 공개/포트폴리오 가이드

## 1. Repository 이름

추천:

```text
fabmind-agent
```

대체:

```text
semiconductor-troubleshooting-agent
loadport-ai-troubleshooter
fabmind-agentic-maintenance
```

## 2. 공개 범위

취업 포트폴리오라면 public repository가 유리하다. 단, 다음은 반드시 지킨다.

- 실제 회사명/장비명/고객사 데이터 사용 금지
- 모든 데이터는 synthetic demo data라고 명시
- 보안상 민감한 레시피, 수율, 공정 조건 표현 금지
- “실제 장비 제어 가능”이라고 과장 금지

## 3. README 구성

README는 회사 담당자가 3분 안에 이해해야 한다.

필수 섹션:

1. One-liner
2. Problem
3. Constraints
4. Solution
5. Architecture image
6. Key screenshots
7. Golden Path demo
8. Tech stack
9. How to run
10. Test/CI
11. What I learned
12. Future roadmap

## 4. GitHub Actions

`.github/workflows/ci.yml`로 다음을 실행한다.

- backend tests
- frontend typecheck/lint
- Playwright smoke or E2E
- OpenAPI contract check

## 5. Pull Request 기록

회사 입장에서 PR 기록은 개발 습관을 보여준다. 한 번에 대량 commit하지 말고 PR 단위로 나눈다.

추천 PR 제목:

```text
PR-00 Initialize monorepo scaffold
PR-01 Add CI and quality gate
PR-02 Add domain models and deterministic seed data
PR-07 Implement deterministic diagnosis agent
PR-08 Build agent analysis screen with evidence drawer
PR-10 Add report approval workflow and audit logs
```

## 6. GitHub Pages 또는 Portfolio Landing

완성 후 `/docs` 또는 별도 `portfolio/` 폴더에 정적 소개 페이지를 둔다.

포함:

- 프로젝트 소개
- 화면 캡처
- 5분 데모 영상 링크
- GitHub repository 링크
- 발표 PDF 링크

## 7. 회사 지원 시 첨부 문장

```text
FabMind Agent는 반도체 Load Port / FOUP Clamp 장애 대응을 위한 온프레미스·읽기 전용·근거 기반 Agentic AI 트러블슈팅 플랫폼입니다. 단순 챗봇이 아니라 알람, DI/DO, EtherCAT, 매뉴얼 근거, 정비 이력, 승인, 감사로그를 하나의 진단 workflow로 연결했습니다. 실제 반도체 현장의 보안·장비 이질성·안전 책임을 고려해 외부 데이터 반출 없이 동작하는 구조로 설계했습니다.
```

## 8. Git 명령 순서

```bash
# 저장소 초기화
 git init
 git add .
 git commit -m "PR-00 initialize FabMind Agent repository"

# GitHub에서 빈 repo 생성 후
 git branch -M main
 git remote add origin https://github.com/<YOUR_ID>/fabmind-agent.git
 git push -u origin main

# 작업 브랜치 예시
 git checkout -b feature/pr-02-db-seed
 git add .
 git commit -m "PR-02 add domain models and seed data"
 git push -u origin feature/pr-02-db-seed
```

## 9. GitHub 연결 후 체크

- README가 바로 보이는가?
- CI badge가 있는가?
- Actions가 green인가?
- PR 기록이 남아 있는가?
- screenshots가 깨지지 않는가?
- 민감 정보가 없는가?
- 회사 사람이 실행할 수 있는가?
