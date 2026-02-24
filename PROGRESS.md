# Nanobot 개발 진행 사항 (Development Progress)

> 현재 버전: **v0.1.3.post4** | 최초 릴리스: 2026-02-01 | 라이선스: MIT

---

## 프로젝트 개요

**Nanobot**은 초경량 개인 AI 어시스턴트 프레임워크로, Clawdbot 대비 99% 작은 코드베이스(~4,000줄)를 목표로 설계되었습니다. 멀티 채널(Telegram, WhatsApp), 멀티 LLM 프로바이더를 지원하며 Python 3.11+ 기반으로 동작합니다.

---

## 개발 타임라인

### Day 1 — 2026-02-01: 프로젝트 초기 설정 및 핵심 기능 구현

- **프로젝트 초기화**: 초기 커밋 및 "hello world" 릴리스
- **README 작성 및 개선**: 프로젝트 소개, 로고, 문서 정비
- **서브 에이전트 시스템 추가** (`feat: add sub-agent system`)
  - 백그라운드 태스크를 별도 에이전트로 실행하는 구조 도입
- **Telegram 마크다운 지원** (`feat(telegram): markdown support`)
  - Telegram 채널에서 마크다운 형식 메시지 렌더링
- **스킬 메타데이터 통일** (`fix: unify skill metadata format`)
- **Zhipu API 지원 추가** (`feat: add Zhipu API support and set glm-4.7-flash as default model`)
  - Zhipu(智普) AI의 GLM 모델 연동
- **릴리스**: v0.1.3.post2 → v0.1.3.post3
- **커뮤니티**: Feishu & WeChat 그룹 링크 추가, PyPI 다운로드 카운트 배지 추가

### Day 2 — 2026-02-02: 다양한 프로바이더 및 배포 환경 지원

- **vLLM/로컬 LLM 지원** (`feat: add vLLM/local LLM support`) — PR #4
  - 로컬 서버에서 실행되는 LLM과의 연동 지원
- **게이트웨이 포트 변경** (`chore: change default gateway port to 18790`) — PR #8
  - OpenClaw와의 포트 충돌 방지
- **Gemini 프로바이더 지원** (`feat: add Gemini provider support`)
  - Google Gemini 모델 연동
- **Telegram 이미지 인식** (`feat: add vision support for image recognition in Telegram`)
  - Telegram에서 이미지를 받아 비전 모델로 분석하는 기능
- **Docker 지원** (`feat: add Dockerfile with uv-based installation`) — PR #18
  - uv 기반 Dockerfile 작성
  - Docker 빌드/실행 문서화
  - 의존성 캐싱 레이어 최적화
  - bridge 디렉토리 스텁 생성 및 git 설치 이슈 수정
- **도구 실행 로깅 개선** (`feat: improve tool execution logging`) — Issue #10 해결
- **uv 설치 방법 문서화** (`docs: add uv installation instructions`) — Issue #5 해결
- **음성 전사 지원** (`feat: add voice transcription support with groq`) — Issue #13 해결
  - Groq Whisper API를 이용한 음성→텍스트 변환
- **기본 명령어 변경** (`feat: change default command to status`)
- **Amazon Bedrock 지원** (`feat: add Amazon Bedrock support`) — PR #21
- **web_fetch URL 검증 강화** (`feat: improve web_fetch URL validation and security`) — PR #22
  - URL 유효성 검사 및 보안 개선
- **Heartbeat 토큰 매칭 수정** (`fix: correct heartbeat token matching logic`) — PR #23
- **스케줄 리마인더 기능 강화** (`feat: enhance scheduled reminders`)
- **Telegram 발신자 ID 처리 개선** (`feat: enhance sender ID handling in Telegram channel`)
- **도구 파라미터 검증 및 테스트** (`Validate tool params and add tests`) — PR #30
  - 도구 스키마 유효성 검증 로직 추가
  - `tests/test_tool_validation.py` 테스트 추가
- **exec 도구 안전장치 추가** (`Harden exec tool with safety guard`)
  - 명령어 실행 시 보안 가드 적용
- **비전 코드 단순화** (`simplify vision support code`)

### Day 3 — 2026-02-03: PR 병합 및 문서 정비

- **다수의 PR 병합 및 통합**:
  - PR #17: Groq 음성 전사 지원 병합
  - PR #18: Dockerfile 및 설치 가이드 병합
  - PR #21: Amazon Bedrock 지원 병합
  - PR #22: web_fetch URL 보안 강화 병합
  - PR #23: Heartbeat 토큰 매칭 수정 병합
  - PR #26: Telegram 채널 상태 명령어 수정 병합
  - PR #32: Zhipu AI 모델 prefix 수정 병합
  - PR #43: 뉴스 날짜 수정 (2025 → 2026) 병합
- **Groq API 키 의존성 주입 리팩토링** (`refactor: use explicit dependency injection for groq_api_key`)
- **문서 개선**:
  - README에 프로바이더 정보 및 Docker 예제 추가
  - GitHub Alerts 형식으로 노트/팁 통일
  - 설치 방법 개선
  - README에 면책조항(disclaimer) 추가
  - Discord 커뮤니티 링크 추가
  - 문서 구조 최적화

### Day 4 — 2026-02-04: 안정화 및 릴리스

- **status 명령어 수정** (`fix: status command now respects workspace from config`) — PR #27
  - 설정 파일의 workspace 경로를 올바르게 참조하도록 수정
- **exec 도구 파라미터 검증 및 안전장치** (`feat: add parameter validation and safety guard for exec tool`) — PR #30
- **파라미터 검증 로직 단순화** (`refactor: simplify parameter validation logic`)
- **문서 오류 수정** (`docs: fix incorrect references and add missing tool docs`)
- **bridge 경로 수정** (`fix: correct bridge path for pip-installed package`)
  - pip 설치 시 WhatsApp bridge 경로가 올바르게 설정되도록 수정
- **v0.1.3.post4 릴리스** (`bump version to 0.1.3.post4`)

---

## 주요 기능 목록

### 핵심 기능
| 기능 | 설명 |
|------|------|
| 에이전트 루프 | LLM ↔ 도구 실행을 반복하는 핵심 처리 루프 |
| 서브 에이전트 | 백그라운드에서 독립적인 태스크를 처리하는 에이전트 |
| 영속 메모리 | 일별 메모리 + 장기 메모리 (MEMORY.md) |
| 스킬 시스템 | 마크다운 기반 확장 가능한 스킬 (GitHub, Weather, tmux 등) |
| 세션 관리 | 채널/채팅별 대화 기록 저장 (JSONL) |
| 크론/하트비트 | 예약 작업 및 주기적 태스크 실행 |

### 도구 (Tools)
| 도구 | 설명 |
|------|------|
| `read_file` / `write_file` / `edit_file` | 파일 시스템 조작 |
| `list_dir` | 디렉토리 목록 조회 |
| `exec` | 셸 명령어 실행 (안전장치 포함) |
| `web_search` | Brave API 기반 웹 검색 |
| `web_fetch` | URL 콘텐츠 가져오기 (보안 검증 포함) |
| `send_message` | 채팅 채널에 메시지 전송 |
| `spawn` | 서브 에이전트 생성 |

### 지원 LLM 프로바이더
| 프로바이더 | 추가 시점 |
|-----------|----------|
| OpenRouter | 초기 릴리스 |
| Anthropic (Claude) | 초기 릴리스 |
| OpenAI | 초기 릴리스 |
| Zhipu AI (GLM) | 2026-02-01 |
| vLLM / 로컬 LLM | 2026-02-02 |
| Google Gemini | 2026-02-02 |
| Groq | 2026-02-02 |
| Amazon Bedrock | 2026-02-02 |

### 지원 채널
| 채널 | 설명 |
|------|------|
| Telegram | 마크다운, 이미지 인식, 음성 전사 지원 |
| WhatsApp | Baileys 기반 Node.js bridge 연동 |

---

## 병합된 주요 Pull Requests

| PR | 제목 | 날짜 |
|----|------|------|
| #4 | vLLM/로컬 LLM 지원 추가 | 2026-02-02 |
| #8 | 게이트웨이 포트 충돌 수정 | 2026-02-02 |
| #14 | uv 설치 방법 추가 | 2026-02-02 |
| #17 | Groq 음성 전사 지원 | 2026-02-03 |
| #18 | Dockerfile 및 Docker 가이드 | 2026-02-03 |
| #21 | Amazon Bedrock 지원 | 2026-02-03 |
| #22 | web_fetch URL 보안 강화 | 2026-02-03 |
| #23 | Heartbeat 토큰 매칭 수정 | 2026-02-03 |
| #26 | Telegram 채널 상태 명령어 수정 | 2026-02-03 |
| #27 | status 명령어 workspace 수정 | 2026-02-04 |
| #30 | exec 도구 안전장치 강화 | 2026-02-04 |
| #32 | Zhipu AI 모델 prefix 수정 | 2026-02-04 |
| #43 | 뉴스 날짜 수정 (2025→2026) | 2026-02-03 |

---

## 해결된 Issues

| Issue | 내용 |
|-------|------|
| #5 | uv 설치 방법 문서화 |
| #10 | 도구 실행 로깅 개선 |
| #13 | 음성 전사 지원 (Groq Whisper) |

---

## 버전 이력

| 버전 | 날짜 | 주요 변경 |
|------|------|----------|
| v0.1.3.post2 | 2026-02-01 | 서브 에이전트, Telegram 마크다운, Zhipu AI 지원 |
| v0.1.3.post3 | 2026-02-01 | 스킬 메타데이터 통일 |
| v0.1.3.post4 | 2026-02-04 | Docker, 다중 프로바이더, 보안 강화, bridge 경로 수정 |

---

## 기술 스택

- **Python 3.11+**: 핵심 에이전트 프레임워크
- **Node.js 20+**: WhatsApp bridge (Baileys)
- **주요 의존성**: LiteLLM, Typer, Pydantic, python-telegram-bot, websockets, httpx, loguru, rich, croniter, readability-lxml
- **빌드**: hatchling (pyproject.toml)
- **테스트**: pytest, pytest-asyncio
- **린터**: ruff
- **배포**: Docker, pip, uv

---

## 프로젝트 구조

```
kanobot/
├── nanobot/                 # 메인 Python 패키지 (~4,000줄)
│   ├── agent/               # 에이전트 코어 (루프, 컨텍스트, 메모리, 스킬, 도구)
│   ├── channels/            # 채팅 채널 (Telegram, WhatsApp)
│   ├── providers/           # LLM 프로바이더 (LiteLLM 기반)
│   ├── session/             # 세션 관리
│   ├── bus/                 # 메시지 라우팅
│   ├── config/              # 설정 (Pydantic 스키마)
│   ├── cron/                # 예약 작업
│   ├── heartbeat/           # 주기적 태스크
│   ├── skills/              # 확장 스킬 (GitHub, Weather, tmux 등)
│   ├── cli/                 # CLI 인터페이스 (Typer)
│   └── utils/               # 유틸리티
├── bridge/                  # WhatsApp bridge (Node.js/TypeScript)
├── workspace/               # 워크스페이스 템플릿
├── tests/                   # 테스트
├── pyproject.toml           # 패키지 설정
├── Dockerfile               # Docker 빌드
└── README.md                # 프로젝트 문서
```

---

## 외부 기여자 참여 현황

- **ZhihaoZhang97**: vLLM 지원 (PR #4)
- **Neutralmilkzzz**: 포트 충돌 수정 (PR #8)
- **pve**: uv 설치 방법 (PR #14)
- **kiplangatkorir**: 도구 스키마 검증 (PR #30 내 PR #1)
- **pjperez**: Zhipu AI prefix 수정 (PR #32)
- **tlguszz1010**: 날짜 수정 (PR #43)
