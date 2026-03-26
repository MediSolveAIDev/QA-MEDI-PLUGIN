# /setup - 프로젝트 온보딩 & 환경 설정

> 플러그인 설치 후 프로젝트별 환경 설정을 대화형으로 안내합니다.

---

## 1. 개요

- **역할**: 각 프로젝트 루트에서 실행하는 초기 세팅 가이드
- **실행 시점**: 프로젝트에서 `/init` 실행 후, 또는 설정 변경 시
- **목표**: `config/common.json`, `config/project.json`, `.env` 파일을 대화형으로 완성

---

## 2. 실행 모드

### 2.1 초기 세팅 (처음 설치 시)

```
사용자: /setup
```

아래 순서로 진행:

1. **공통 설정 확인** (`config/common.json`)
2. **프로젝트 설정** (`config/project.json`)
3. **API 키 확인** (`.env`)
4. **연결 테스트** (선택)
5. **설정 완료 요약**

### 2.2 프로젝트 추가

```
사용자: /setup new
```

- 현재 프로젝트 설정 변경 (`config/project.json`)
- 기존 템플릿 기반으로 대화형 입력

### 2.3 설정 변경

```
사용자: /setup update SAY
```

- 기존 프로젝트 설정 수정
- 변경할 항목만 선택적으로 업데이트

### 2.4 상태 확인

```
사용자: /setup check
```

- 모든 설정 파일의 빈 값/미설정 항목 스캔
- 연결 가능 여부 요약 리포트

---

## 3. 세팅 흐름

### Step 1: 공통 설정 (`config/common.json`)

대화형으로 아래 항목 수집:

```
🔧 공통 환경 설정을 시작합니다.

1. JIRA 설정
   - JIRA URL: (예: https://your-domain.atlassian.net)
   - JIRA 계정 이메일:

2. Confluence 설정
   - Confluence URL: (예: https://your-domain.atlassian.net/wiki)

3. GitHub 설정
   - Organization: (기본값: MediSolveAIDev)
   - Actions Repo:

4. Slack 알림 설정
   - Webhook URL: (파이프라인 진행 알림용)
     → 승인 전용 채널이 별도로 있으면 아래도 입력
   - 승인 전용 Webhook URL: (선택, 승인 요청만 별도 채널로)

```

**처리 규칙:**
- 입력된 값은 프로젝트 루트의 `config/common.json`에 즉시 반영
- 빈 값은 기존 값 유지 (엔터만 치면 스킵)
- URL 형식 기본 검증 (https:// 시작 여부)
- 다른 프로젝트에서 이미 설정한 common.json이 있으면 값을 복사할지 안내

### Step 2: 프로젝트 설정 (`config/project.json`)

현재 프로젝트 루트의 `config/project.json`을 대화형으로 채운다.

```
📁 현재 프로젝트 설정

1. 기본 정보
   - 현재 버전: (기본값: v1.4.0)
   - 플랫폼: (기본값: admin)

2. JIRA
   - 프로젝트 키: (예: CENSAY)
   - 보드 ID: (숫자)

3. Confluence
   - Space Key: (예: SAY)
   - 시나리오 페이지 ID:
   - TC 페이지 ID:
   - 리포트 페이지 ID:

4. Figma
   - File ID: (Figma URL에서 추출 가능)
     → URL 붙여넣으면 자동 추출: https://figma.com/file/{FILE_ID}/...

5. 자동화
   - 테스트 레포: (예: MediSolveAIDev/say-e2e-tests)
   - 스크립트 경로: (예: tests/)
   - 테스트 환경 URL: (예: https://dev-say.example.com)
   - 프레임워크: (기본값: pytest)
```

**처리 규칙:**
- Figma URL 붙여넣기 시 File ID 자동 추출
- Confluence URL 붙여넣기 시 Page ID 자동 추출
- 숫자 필드 형식 검증

### Step 3: API 키 확인 (`.env`)

```
🔑 API 키 설정을 확인합니다.

.env 파일 상태:
  ✅ CONFLUENCE_URL = https://xxx.atlassian.net
  ✅ CONFLUENCE_EMAIL = user@company.com
  ❌ CONFLUENCE_API_TOKEN = (미설정)
  ❌ FIGMA_ACCESS_TOKEN = (미설정)
  ❌ JIRA_API_TOKEN = (미설정)

미설정 항목이 3개 있습니다.
지금 입력하시겠습니까? (Y/N)
```

**처리 규칙:**
- `.env` 파일이 없으면 새로 생성하고 대화형으로 값을 입력받는다
- `.env`가 이미 있으면 빈 값만 표시하고 해당 항목만 입력받는다
- API 토큰 입력 시 마스킹 안내 (화면에 노출되므로 주의)
- `.env`는 `.gitignore`에 포함 확인

### Step 3-1: Google Sheets 인증 파일 확인

```
📋 Google Sheets 인증 파일을 확인합니다.

credentials/ 폴더 상태:
  ✅ credentials.json (OAuth 클라이언트 - 팀 공통)
  ❌ token.json (개인 인증 토큰 - 최초 실행 시 자동 생성)
```

**처리 규칙:**
- `credentials/credentials.json` 존재 여부 확인
- 파일이 있으면 ✅ 표시
- 파일이 없으면 아래 안내 출력:
  ```
  ⚠️ credentials/credentials.json 파일이 없습니다.

  아래 공유 드라이브에서 credentials.json을 다운로드해주세요:
  📂 QA_업무자료 > 1.QA 공유 자료 > 자동화 > 공통 환경변수 > 00.QA-agent 세팅용

  다운로드한 파일을 프로젝트 루트의 credentials/ 폴더에 저장해주세요.
  (폴더가 없으면 생성)
  ```
- `token.json`은 공유 불필요. 최초 Google Sheets 업로드 실행 시 브라우저 인증 팝업이 뜨고, 본인 Google 계정으로 로그인하면 자동 생성됨
- 파일 없어도 다음 단계로 진행 가능 (Google Sheets 업로드만 비활성)

### Step 3-2: Atlassian MCP 서버 확인 (JIRA/Confluence 연동)

```
🔗 Atlassian MCP 서버 연결을 확인합니다.

MCP 서버 상태:
  ✅ Atlassian MCP - 연결됨 (JIRA + Confluence 사용 가능)
  또는
  ❌ Atlassian MCP - 미설정
```

**Atlassian MCP 미설정 시 안내:**

```
⚠️ Atlassian MCP 서버가 설정되지 않았습니다.

JIRA 버그 관리(/report-bug) 및 Confluence 연동에 필요합니다.

📋 설정 방법:
  1. ~/.claude/.mcp.json 파일을 열어주세요
  2. mcpServers에 아래 내용을 추가하세요:

  "atlassian": {
    "command": "npx",
    "args": ["-y", "@anthropic/atlassian-mcp-server"],
    "env": {
      "ATLASSIAN_SITE_URL": "https://{your-domain}.atlassian.net",
      "ATLASSIAN_USER_EMAIL": "{jira-email}",
      "ATLASSIAN_API_TOKEN": "{jira-api-token}"
    }
  }

  ⚠️ 실제 패키지명은 npm 검색으로 확인 필요
     (커뮤니티: @anthropic/atlassian-mcp-server, mcp-remote-atlassian 등)

  3. Claude Code를 재시작하세요
  4. /setup check 로 연결 확인

⏭️ 지금 건너뛸 수 있습니다.
   JIRA 연동 없이도 시나리오/TC 작성은 정상 동작합니다.
   나중에 /setup check 로 다시 확인할 수 있습니다.
```

**처리 규칙:**
- `~/.claude/.mcp.json`에 `atlassian` 키가 있는지 파일 읽기로 확인
- 있으면 ✅ 표시
- 없으면 설정 가이드 출력 후 스킵 가능 (다음 단계로 진행)
- Atlassian MCP 없어도 나머지 스킬은 정상 동작 (report-bug만 비활성)

### Step 3-3: Figma Export 환경 확인

```
🎨 Figma Export 환경을 확인합니다.

data/figma_output/ 폴더 상태:
  ✅ data/figma_output/ 폴더 존재

tools/ 폴더 상태:
  ✅ tools/figma_extract.py 존재
  ✅ tools/figma_bridge.py 존재
  ✅ tools/figma_cmd.py 존재
```

**처리 규칙:**
- `data/figma_output/` 폴더 존재 여부 확인
- `tools/figma_extract.py`, `tools/figma_bridge.py`, `tools/figma_cmd.py` 존재 여부 확인
- 이 파일들은 `/init` 실행 시 자동 생성됨
- 파일이 없으면 아래 안내 출력:
  ```
  ⚠️ Figma 도구 파일이 없습니다. /init 을 먼저 실행해주세요.
  ```
- 파일 있으면 ✅ 표시 + 사용법 안내:
  ```
  💡 Figma export 실행 방법:
    1. python tools/figma_bridge.py          (브릿지 서버 실행, 별도 터미널)
    2. Figma에서 Claude Connector 플러그인 실행
    3. python tools/figma_extract.py --project SAY --version v1.4.0 --sections sections.json

  섹션 ID 확인: python tools/figma_cmd.py selection (Figma에서 노드 선택 후)
  export 결과는 data/figma_output/{프로젝트}_{버전}/ 에 저장됩니다.
  이후 /enrich-figma 스킬로 시나리오 보강이 가능합니다.
  ```
- Figma 도구 없어도 다음 단계로 진행 가능 (Figma 보강만 비활성)

### Step 4: 연결 테스트 (선택)

```
🧪 설정한 연결을 테스트할까요? (Y/N)

테스트 결과:
  ✅ JIRA - 연결 성공 (프로젝트: SAY 확인됨)
  ✅ Confluence - 연결 성공 (Space: SAY 확인됨)
  ❌ Figma API - 연결 실패 (401 Unauthorized → 토큰 확인 필요)
  ✅ Figma Bridge - tools/figma_bridge.py 존재 확인
```

**처리 규칙:**
- 각 서비스별 최소 API 호출로 연결 확인
- 실패 시 원인 안내 (401 → 토큰, 404 → URL, timeout → 네트워크)
- MCP 서버 연결 여부도 확인 (Atlassian MCP, Figma MCP 등)
- Atlassian MCP 연결 시 JIRA 프로젝트 조회 테스트 포함
- Figma Bridge: `tools/figma_bridge.py` 파일 존재 여부 확인. 없으면 안내:
  ```
  ⚠️ tools/figma_bridge.py 파일이 없습니다.
  Figma 보강 단계(Phase 1-A)에서 Figma 브릿지가 필요합니다.
  설정 가이드: https://medisolveai.atlassian.net/wiki/spaces/01/pages/230457386/claude+code+-+Figma+connect+plugin
  figma_bridge.py를 tools/ 폴더에 배치해주세요.
  ```
- Figma Bridge 실행은 파이프라인 Phase 1-A에서 자동 처리됨 (setup에서는 파일 존재만 확인)

### Step 5: 설정 완료 요약

```
✅ 환경 설정 완료!

공통 설정: config/common.json ✅
프로젝트 설정: config/project.json ✅ (SAY, admin, v1.4.0)
API 키: .env ⚠️ (FIGMA_ACCESS_TOKEN 미설정)
Slack 알림: ✅ 설정됨 / ❌ 미설정 (파이프라인 알림 비활성)
Atlassian MCP: ✅ 연결됨 / ❌ 미설정 (JIRA 버그 관리 비활성)
Figma Export: tools/figma_extract.py ✅ / data/figma_output/ ✅

💡 나중에 변경하려면: /setup update
💡 상태 확인하려면: /setup check
```

### Step 6: 사용법 가이드 출력

설정 완료 요약 직후 아래 사용법 가이드를 자동 출력한다:

```
🚀 사용법:
  • /run-pipeline             → 새 파이프라인 시작 (대화형 정보 수집)
  • /run-pipeline SAY v1.4.0  → 프로젝트/버전 지정하여 시작
  • "새 업무 줄게"             → 자연어로 시작

📌 진행 중 명령:
  • "기획서 업데이트됐어"      → 기획 변경 대응 (시나리오 diff 업데이트)
  • Ctrl+C                    → 일시정지 (자동 저장, --resume로 재개)

📂 산출물 위치:
  • data/scenarios/  → 시나리오
  • data/tc/         → TC
  • data/pipeline/   → 파이프라인 상태
  • data/figma_output/    → Figma export 데이터

🎨 Figma 보강:
  • python tools/figma_extract.py --project SAY --version v1.4.0  → Figma 데이터 추출
  • /enrich-figma SAY                                             → 시나리오 보강
```

---

## 4. 설정 변경 (`/setup update`)

현재 프로젝트의 `config/project.json` 또는 `config/common.json` 값을 수정한다.
변경할 항목만 선택적으로 업데이트.

---

## 5. 설정 검증 규칙

| 항목 | 검증 | 실패 시 안내 |
|------|------|-------------|
| URL 형식 | `https://`로 시작 | "https://로 시작하는 전체 URL을 입력해주세요" |
| JIRA 프로젝트 키 | 영문 대문자 | "영문 대문자로 입력해주세요 (예: CENSAY)" |
| Figma URL → ID 추출 | `/file/` 또는 `/design/` 패턴 | "Figma 파일 URL을 그대로 붙여넣어주세요" |
| Confluence Page ID | 숫자 | "페이지 URL 끝의 숫자를 입력해주세요" |
| API 토큰 | 비어있지 않음 | "해당 서비스의 API 토큰을 발급받아 입력해주세요" |

---

## 6. 파일 처리 규칙

- **config/common.json**: 공통 설정 저장 (JIRA URL, Confluence URL 등 — 모든 프로젝트 동일)
- **config/project.json**: 현재 프로젝트 설정 저장 (프로젝트 키, 버전, Figma 등)
- **.env**: API 토큰/비밀번호 저장 (git 추적 안 됨)

**주의사항:**
- `.env` 파일은 절대 git에 커밋하지 않음
- API 토큰 입력 시 "화면에 표시됩니다" 경고 출력
- 기존 설정 파일이 있으면 덮어쓰지 않고 빈 값만 업데이트
- 모든 경로는 프로젝트 루트 기준 상대 경로
