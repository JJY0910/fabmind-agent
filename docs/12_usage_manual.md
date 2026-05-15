# 사용법 - Antigravity + Codex + GitHub

## 1. 개발 환경 준비

Windows PowerShell 관리자 권한:

```powershell
wsl --install
```

설치 후 재부팅하고 Ubuntu를 실행한다.

Docker Desktop 설치 후 Settings에서 WSL2 backend를 켠다.

## 2. 프로젝트 시작 순서

```bash
# WSL Ubuntu terminal
mkdir -p ~/projects
cd ~/projects
# GitHub repo가 있으면 clone, 없으면 zip 압축 해제
cd fabmind-agent
cp infra/.env.example infra/.env
docker compose -f infra/docker-compose.yml up -d
```

## 3. Antigravity 사용 순서

1. 프로젝트 폴더를 Antigravity에서 연다.
2. `AGENTS.md`를 먼저 읽게 한다.
3. `docs/06_antigravity_missions.md`의 Mission 0부터 넣는다.
4. 한 mission이 끝날 때마다 브라우저 screenshot을 받는다.
5. UI 변경은 반드시 loading/empty/error/success 상태를 포함시킨다.

## 4. Codex 사용 순서

1. Codex에서 repo를 연다.
2. 먼저 “Read AGENTS.md and inspect repository”를 시킨다.
3. PR 단위로 backend/DB/test를 구현시킨다.
4. Codex가 수정한 뒤 반드시 테스트 명령을 실행시킨다.
5. 실패하면 실패 로그를 그대로 붙여서 수정시킨다.

## 5. 추천 반복 루프

```text
Antigravity: UI 또는 scaffold 구현
→ Codex: backend/API/test 구현
→ Antigravity: 브라우저 연결 검증
→ Codex: contract mismatch 수정
→ GitHub PR 생성
→ CI 통과 확인
```

## 6. 하루 개발 루틴

1. 오늘 할 PR 하나만 고른다.
2. 관련 문서 1개와 prompt 1개만 사용한다.
3. 구현 후 테스트를 실행한다.
4. README 또는 docs를 업데이트한다.
5. commit을 남긴다.
6. 다음 PR로 넘어간다.

## 7. 절대 금지

- “전체 다 만들어줘”라고 시키기
- prompt 여러 개를 한 번에 넣기
- 실패 로그를 무시하고 다음 기능으로 넘어가기
- UI만 예쁘게 만들고 API/테스트를 미루기
- LLM 응답에만 의존해서 rule engine 생략하기
