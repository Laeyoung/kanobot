<div align="center">
  <img src="kanobot_logo.png" alt="kanobot" width="500">
  <h1>kanobot: 초경량 개인 AI 어시스턴트</h1>
  <p>
    <a href="https://pypi.org/project/kanobot-ai/"><img src="https://img.shields.io/pypi/v/kanobot-ai" alt="PyPI"></a>
    <a href="https://pepy.tech/project/kanobot-ai"><img src="https://static.pepy.tech/badge/kanobot-ai" alt="Downloads"></a>
    <img src="https://img.shields.io/badge/python-≥3.11-blue" alt="Python">
    <img src="https://img.shields.io/badge/license-MIT-green" alt="License">
    <a href="./COMMUNICATION.md"><img src="https://img.shields.io/badge/Feishu-Group-E9DBFC?style=flat&logo=feishu&logoColor=white" alt="Feishu"></a>
    <a href="./COMMUNICATION.md"><img src="https://img.shields.io/badge/WeChat-Group-C5EAB4?style=flat&logo=wechat&logoColor=white" alt="WeChat"></a>
    <a href="https://discord.gg/MnCvHqpUGB"><img src="https://img.shields.io/badge/Discord-Community-5865F2?style=flat&logo=discord&logoColor=white" alt="Discord"></a>
  </p>
  <p>
    <a href="./README.md">English</a> | <b>한국어</b>
  </p>
</div>

🐈 **kanobot**은 [Clawdbot](https://github.com/openclaw/openclaw)에서 영감을 받은 **초경량** 개인 AI 어시스턴트입니다.

⚡️ 단 **~4,000줄**의 코드로 핵심 에이전트 기능을 제공합니다 — Clawdbot의 430,000줄 대비 **99% 더 작습니다**.

## 📢 소식

- **2026-02-01** 🎉 kanobot 출시! 🐈 kanobot을 사용해 보세요!

## kanobot의 주요 특징:

🪶 **초경량**: 약 4,000줄의 코드 — Clawdbot 대비 99% 작으면서도 핵심 기능을 모두 제공합니다.

🔬 **연구 친화적**: 깔끔하고 읽기 쉬운 코드로, 연구 목적의 이해·수정·확장이 용이합니다.

⚡️ **빠른 속도**: 최소한의 풋프린트로 빠른 시작, 낮은 리소스 사용량, 빠른 반복 개발이 가능합니다.

💎 **간편한 사용**: 원클릭 배포로 바로 시작할 수 있습니다.

## 🏗️ 아키텍처

<p align="center">
  <img src="kanobot_arch.png" alt="kanobot 아키텍처" width="800">
</p>

## ✨ 기능

<table align="center">
  <tr align="center">
    <th><p align="center">📈 24시간 실시간 시장 분석</p></th>
    <th><p align="center">🚀 풀스택 소프트웨어 엔지니어</p></th>
    <th><p align="center">📅 스마트 일정 관리</p></th>
    <th><p align="center">📚 개인 지식 어시스턴트</p></th>
  </tr>
  <tr>
    <td align="center"><p align="center"><img src="case/search.gif" width="180" height="400"></p></td>
    <td align="center"><p align="center"><img src="case/code.gif" width="180" height="400"></p></td>
    <td align="center"><p align="center"><img src="case/scedule.gif" width="180" height="400"></p></td>
    <td align="center"><p align="center"><img src="case/memory.gif" width="180" height="400"></p></td>
  </tr>
  <tr>
    <td align="center">탐색 • 인사이트 • 트렌드</td>
    <td align="center">개발 • 배포 • 확장</td>
    <td align="center">일정 • 자동화 • 정리</td>
    <td align="center">학습 • 기억 • 추론</td>
  </tr>
</table>

## 📦 설치

**소스에서 설치** (최신 기능, 개발용 권장)

```bash
git clone https://github.com/HKUDS/kanobot.git
cd kanobot
pip install -e .
```

**[uv](https://github.com/astral-sh/uv)로 설치** (안정, 빠름)

```bash
uv tool install kanobot-ai
```

**PyPI에서 설치** (안정)

```bash
pip install kanobot-ai
```

## 🚀 빠른 시작

> [!TIP]
> `~/.kanobot/config.json`에 API 키를 설정하세요.
> API 키 발급: [OpenRouter](https://openrouter.ai/keys) (LLM) · [Brave Search](https://brave.com/search/api/) (선택 사항, 웹 검색용)
> 비용을 줄이려면 모델을 `minimax/minimax-m2`로 변경할 수도 있습니다.

**1. 초기화**

```bash
kanobot onboard
```

**2. 설정** (`~/.kanobot/config.json`)

```json
{
  "providers": {
    "openrouter": {
      "apiKey": "sk-or-v1-xxx"
    }
  },
  "agents": {
    "defaults": {
      "model": "anthropic/claude-opus-4-5"
    }
  },
  "tools": {
    "web": {
      "search": {
        "apiKey": "BSA-xxx"
      }
    }
  }
}
```

**3. 대화**

```bash
kanobot agent -m "2+2는 뭐야?"
```

이게 끝입니다! 2분 만에 AI 어시스턴트를 사용할 수 있습니다.

## 🖥️ 로컬 모델 (vLLM)

vLLM 또는 OpenAI 호환 서버를 사용하여 자체 로컬 모델로 kanobot을 실행할 수 있습니다.

**1. vLLM 서버 시작**

```bash
vllm serve meta-llama/Llama-3.1-8B-Instruct --port 8000
```

**2. 설정** (`~/.kanobot/config.json`)

```json
{
  "providers": {
    "vllm": {
      "apiKey": "dummy",
      "apiBase": "http://localhost:8000/v1"
    }
  },
  "agents": {
    "defaults": {
      "model": "meta-llama/Llama-3.1-8B-Instruct"
    }
  }
}
```

**3. 대화**

```bash
kanobot agent -m "로컬 LLM에서 안녕!"
```

> [!TIP]
> 인증이 필요 없는 로컬 서버의 경우 `apiKey`는 아무 비어있지 않은 문자열이면 됩니다.

## 💬 채팅 앱

텔레그램이나 왓츠앱을 통해 언제 어디서나 kanobot과 대화하세요.

| 채널 | 설정 난이도 |
|------|------------|
| **Telegram** | 쉬움 (토큰만 필요) |
| **WhatsApp** | 보통 (QR 스캔) |

<details>
<summary><b>Telegram</b> (권장)</summary>

**1. 봇 생성**
- 텔레그램에서 `@BotFather`를 검색합니다
- `/newbot`을 전송하고 안내에 따릅니다
- 토큰을 복사합니다

**2. 설정**

```json
{
  "channels": {
    "telegram": {
      "enabled": true,
      "token": "YOUR_BOT_TOKEN",
      "allowFrom": ["YOUR_USER_ID"]
    }
  }
}
```

> 텔레그램에서 `@userinfobot`을 통해 사용자 ID를 확인할 수 있습니다.

**3. 실행**

```bash
kanobot gateway
```

</details>

<details>
<summary><b>WhatsApp</b></summary>

**Node.js ≥18**이 필요합니다.

**1. 기기 연결**

```bash
kanobot channels login
# WhatsApp → 설정 → 연결된 기기에서 QR을 스캔하세요
```

**2. 설정**

```json
{
  "channels": {
    "whatsapp": {
      "enabled": true,
      "allowFrom": ["+1234567890"]
    }
  }
}
```

**3. 실행** (터미널 두 개)

```bash
# 터미널 1
kanobot channels login

# 터미널 2
kanobot gateway
```

</details>

## ⚙️ 설정

설정 파일: `~/.kanobot/config.json`

### 프로바이더

> [!NOTE]
> Groq는 Whisper를 통한 무료 음성 전사 기능을 제공합니다. 설정하면 텔레그램 음성 메시지가 자동으로 텍스트로 변환됩니다.

| 프로바이더 | 용도 | API 키 발급 |
|-----------|------|------------|
| `openrouter` | LLM (권장, 모든 모델 접근 가능) | [openrouter.ai](https://openrouter.ai) |
| `anthropic` | LLM (Claude 직접 연결) | [console.anthropic.com](https://console.anthropic.com) |
| `openai` | LLM (GPT 직접 연결) | [platform.openai.com](https://platform.openai.com) |
| `groq` | LLM + **음성 전사** (Whisper) | [console.groq.com](https://console.groq.com) |
| `gemini` | LLM (Gemini 직접 연결) | [aistudio.google.com](https://aistudio.google.com) |

<details>
<summary><b>전체 설정 예시</b></summary>

```json
{
  "agents": {
    "defaults": {
      "model": "anthropic/claude-opus-4-5"
    }
  },
  "providers": {
    "openrouter": {
      "apiKey": "sk-or-v1-xxx"
    },
    "groq": {
      "apiKey": "gsk_xxx"
    }
  },
  "channels": {
    "telegram": {
      "enabled": true,
      "token": "123456:ABC...",
      "allowFrom": ["123456789"]
    },
    "whatsapp": {
      "enabled": false
    }
  },
  "tools": {
    "web": {
      "search": {
        "apiKey": "BSA..."
      }
    }
  }
}
```

</details>

## CLI 레퍼런스

| 명령어 | 설명 |
|--------|------|
| `kanobot onboard` | 설정 및 워크스페이스 초기화 |
| `kanobot agent -m "..."` | 에이전트와 대화 |
| `kanobot agent` | 대화형 채팅 모드 |
| `kanobot gateway` | 게이트웨이 시작 |
| `kanobot status` | 상태 표시 |
| `kanobot channels login` | WhatsApp 연결 (QR 스캔) |
| `kanobot channels status` | 채널 상태 표시 |

<details>
<summary><b>예약 작업 (Cron)</b></summary>

```bash
# 작업 추가
kanobot cron add --name "daily" --message "좋은 아침!" --cron "0 9 * * *"
kanobot cron add --name "hourly" --message "상태 확인" --every 3600

# 작업 목록
kanobot cron list

# 작업 제거
kanobot cron remove <job_id>
```

</details>

## 🐳 Docker

> [!TIP]
> `-v ~/.kanobot:/root/.kanobot` 플래그는 로컬 설정 디렉토리를 컨테이너에 마운트하여, 컨테이너를 재시작해도 설정과 워크스페이스가 유지되도록 합니다.

컨테이너에서 kanobot을 빌드하고 실행합니다:

```bash
# 이미지 빌드
docker build -t kanobot .

# 설정 초기화 (최초 1회)
docker run -v ~/.kanobot:/root/.kanobot --rm kanobot onboard

# 호스트에서 설정 파일을 편집하여 API 키 추가
vim ~/.kanobot/config.json

# 게이트웨이 실행 (Telegram/WhatsApp 연결)
docker run -v ~/.kanobot:/root/.kanobot -p 18790:18790 kanobot gateway

# 또는 단일 명령 실행
docker run -v ~/.kanobot:/root/.kanobot --rm kanobot agent -m "안녕!"
docker run -v ~/.kanobot:/root/.kanobot --rm kanobot status
```

## 📁 프로젝트 구조

```
kanobot/
├── agent/          # 🧠 핵심 에이전트 로직
│   ├── loop.py     #    에이전트 루프 (LLM ↔ 도구 실행)
│   ├── context.py  #    프롬프트 빌더
│   ├── memory.py   #    영구 메모리
│   ├── skills.py   #    스킬 로더
│   ├── subagent.py #    백그라운드 작업 실행
│   └── tools/      #    내장 도구 (spawn 포함)
├── skills/         # 🎯 번들 스킬 (github, weather, tmux...)
├── channels/       # 📱 WhatsApp 연동
├── bus/            # 🚌 메시지 라우팅
├── cron/           # ⏰ 예약 작업
├── heartbeat/      # 💓 주기적 웨이크업
├── providers/      # 🤖 LLM 프로바이더 (OpenRouter 등)
├── session/        # 💬 대화 세션
├── config/         # ⚙️ 설정
└── cli/            # 🖥️ 명령어
```

## 🤝 기여 및 로드맵

PR을 환영합니다! 코드베이스는 의도적으로 작고 읽기 쉽게 유지하고 있습니다. 🤗

**로드맵** — 항목을 선택하고 [PR을 열어주세요](https://github.com/HKUDS/kanobot/pulls)!

- [x] **음성 전사** — Groq Whisper 지원 (Issue #13)
- [ ] **멀티모달** — 이미지, 음성, 비디오 인식
- [ ] **장기 기억** — 중요한 맥락을 잊지 않는 메모리
- [ ] **향상된 추론** — 다단계 계획 및 반성
- [ ] **추가 연동** — Discord, Slack, 이메일, 캘린더
- [ ] **자기 개선** — 피드백과 실수로부터 학습

### 기여자

<a href="https://github.com/HKUDS/kanobot/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=HKUDS/kanobot" />
</a>


## ⭐ Star 히스토리

<div align="center">
  <a href="https://star-history.com/#HKUDS/kanobot&Date">
    <picture>
      <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/svg?repos=HKUDS/kanobot&type=Date&theme=dark" />
      <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/svg?repos=HKUDS/kanobot&type=Date" />
      <img alt="Star History Chart" src="https://api.star-history.com/svg?repos=HKUDS/kanobot&type=Date" style="border-radius: 15px; box-shadow: 0 0 30px rgba(0, 217, 255, 0.3);" />
    </picture>
  </a>
</div>

<p align="center">
  <em>방문해 주셔서 감사합니다 ✨ kanobot!</em><br><br>
  <img src="https://visitor-badge.laobi.icu/badge?page_id=HKUDS.kanobot&style=for-the-badge&color=00d4ff" alt="Views">
</p>


<p align="center">
  <sub>kanobot은 교육, 연구 및 기술 교류 목적으로만 사용됩니다</sub>
</p>
