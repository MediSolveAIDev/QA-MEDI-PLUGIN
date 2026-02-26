# /setup - 프로젝트 온보딩 & 환경 설정

> 플러그인 설치 후 프로젝트별 환경 설정을 대화형으로 안내합니다.

---

## 1. 개요

- **역할**: 팀원이 플러그인 설치 후 처음 실행하는 초기 세팅 가이드
- **실행 시점**: 플러그인 설치 직후, 또는 새 프로젝트 추가/설정 변경 시
- **목표**: `config/common.json`, `config/projects/*.json`, `.env` 파일을 대화형으로 완성

---

## 2. 실행 모드

### 2.1 초기 세팅 (처음 설치 시)

```
사용자: /setup
```

아래 순서로 진행:

1. **공통 설정 확인** (`config/common.json`)
2. **프로젝트 선택 및 설정** (`config/projects/*.json`)
3. **API 키 확인** (`.env`)
4. **연결 테스트** (선택)
5. **설정 완료 요약**

### 2.2 프로젝트 추가

```
사용자: /setup new
```

- 새 프로젝트 JSON 파일 생성 (`config/projects/{name}.json`)
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

1. Slack 설정
   - Slack Bot Token이 있나요? (Y/N)
   - 팀장 Slack User ID: (예: U0123456789)
   - Webhook URL: (예: https://hooks.slack.com/services/xxx/yyy/zzz)

2. JIRA 설정
   - JIRA URL: (예: https://your-domain.atlassian.net)
   - JIRA 계정 이메일:

3. Confluence 설정
   - Confluence URL: (예: https://your-domain.atlassian.net/wiki)

4. GitHub 설정
   - Organization: (기본값: MediSolveAIDev)
   - Actions Repo:
```

**처리 규칙:**
- 입력된 값은 `config/common.json`에 즉시 반영
- 빈 값은 기존 값 유지 (엔터만 치면 스킵)
- URL 형식 기본 검증 (https:// 시작 여부)

### Step 2: 프로젝트 설정 (`config/projects/*.json`)

```
📁 어떤 프로젝트를 세팅할까요?

현재 등록된 프로젝트:
  1. SAY (Admin v1.4.0) - ⚠️ 미설정 항목 5개
  2. BAY (Admin v1.0.0) - ⚠️ 미설정 항목 7개
  3. SSO (v1.0.0) - ⚠️ 미설정 항목 7개
  4. [새 프로젝트 추가]
```

선택 후 해당 프로젝트의 항목 수집:

```
📁 SAY 프로젝트 설정

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
  ✅ SLACK_WEBHOOK_URL = https://hooks.slack.com/...
  ❌ JIRA_API_TOKEN = (미설정)

미설정 항목이 3개 있습니다.
지금 입력하시겠습니까? (Y/N)
```

**처리 규칙:**
- `.env` 파일이 없으면 새로 생성하고 대화형으로 값을 입력받는다
- `.env`가 이미 있으면 빈 값만 표시하고 해당 항목만 입력받는다
- API 토큰 입력 시 마스킹 안내 (화면에 노출되므로 주의)
- `.env`는 `.gitignore`에 포함 확인

### Step 4: 연결 테스트 (선택)

```
🧪 설정한 연결을 테스트할까요? (Y/N)

테스트 결과:
  ✅ JIRA - 연결 성공 (프로젝트: SAY 확인됨)
  ✅ Confluence - 연결 성공 (Space: SAY 확인됨)
  ❌ Figma - 연결 실패 (401 Unauthorized → 토큰 확인 필요)
  ✅ Slack - Webhook 전송 성공
```

**처리 규칙:**
- 각 서비스별 최소 API 호출로 연결 확인
- 실패 시 원인 안내 (401 → 토큰, 404 → URL, timeout → 네트워크)
- MCP 서버 연결 여부도 확인 (Confluence MCP, Figma MCP 등)

### Step 5: 설정 완료 요약

```
✅ 세팅 완료!

공통 설정: config/common.json ✅
프로젝트 설정:
  - SAY: config/projects/say.json ✅
  - BAY: config/projects/bay.json ⚠️ (Figma 미설정)
  - SSO: config/projects/sso.json ⚠️ (전체 미설정)
API 키: .env ⚠️ (FIGMA_ACCESS_TOKEN 미설정)

💡 나중에 변경하려면: /setup update SAY
💡 상태 확인하려면: /setup check
```

---

## 4. 새 프로젝트 추가 (`/setup new`)

```
📁 새 프로젝트를 추가합니다.

- 프로젝트 코드명: (영문, 예: SAY)
- 프로젝트 표시명: (예: Centurion Say)
- 플랫폼: admin / app / web
- 초기 버전: (예: v1.0.0)
```

→ `config/projects/{코드명}.json` 생성 후 Step 2와 동일한 세팅 진행

---

## 5. 설정 검증 규칙

| 항목 | 검증 | 실패 시 안내 |
|------|------|-------------|
| URL 형식 | `https://`로 시작 | "https://로 시작하는 전체 URL을 입력해주세요" |
| JIRA 프로젝트 키 | 영문 대문자 | "영문 대문자로 입력해주세요 (예: CENSAY)" |
| Figma URL → ID 추출 | `/file/` 또는 `/design/` 패턴 | "Figma 파일 URL을 그대로 붙여넣어주세요" |
| Confluence Page ID | 숫자 | "페이지 URL 끝의 숫자를 입력해주세요" |
| Slack User ID | `U`로 시작 + 영숫자 | "Slack 프로필에서 Member ID를 복사해주세요" |
| API 토큰 | 비어있지 않음 | "해당 서비스의 API 토큰을 발급받아 입력해주세요" |

---

## 6. 파일 처리 규칙

- **config/common.json**: 공통 설정 저장 (Slack, JIRA URL 등)
- **config/projects/*.json**: 프로젝트별 설정 저장
- **.env**: API 토큰/비밀번호 저장 (git 추적 안 됨)

**주의사항:**
- `.env` 파일은 절대 git에 커밋하지 않음
- API 토큰 입력 시 "화면에 표시됩니다" 경고 출력
- 기존 설정 파일이 있으면 덮어쓰지 않고 빈 값만 업데이트
