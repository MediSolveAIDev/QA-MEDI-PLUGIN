# /init - 로컬 작업 환경 초기화

> 플러그인 설치 후 로컬에 폴더 구조와 템플릿 파일을 생성합니다.

---

## 1. 개요

- **역할**: 플러그인 설치 후 로컬 작업 디렉토리에 필요한 폴더 구조 + 기본 파일 생성
- **실행 시점**: 플러그인 설치 직후, `/setup` 실행 전에 1회 실행
- **목표**: 스킬이 산출물을 저장하고 설정을 읽을 수 있는 로컬 환경을 만든다

---

## 2. 실행

```
사용자: /init
```

---

## 3. 생성할 폴더 구조

현재 작업 디렉토리에 아래 구조를 생성한다. **이미 존재하는 폴더/파일은 건드리지 않는다.**

```
./
├── config/
│   └── projects/
├── data/
│   ├── scenarios/
│   ├── tc/
│   ├── reviews/
│   ├── assessments/
│   ├── fail_analysis/
│   ├── bugs/
│   ├── rules/
│   ├── test_results/
│   └── pipeline/
├── templates/
└── tests/
```

---

## 4. 생성할 파일

### 4.1 config/common.json (없을 때만 생성)

```json
{
  "slack": {
    "bot_name": "QA_Agent",
    "team_lead_user_id": "",
    "webhook_url": ""
  },
  "jira": {
    "base_url": "",
    "email": ""
  },
  "confluence": {
    "base_url": ""
  },
  "figma": {
    "base_url": "https://api.figma.com"
  },
  "github": {
    "org": "MediSolveAIDev",
    "actions_repo": ""
  },
  "env_file": {
    "_comment": "민감 정보는 .env에서 관리. 아래는 필요한 키 목록.",
    "required_keys": [
      "SLACK_BOT_TOKEN",
      "JIRA_API_TOKEN",
      "CONFLUENCE_API_TOKEN",
      "FIGMA_ACCESS_TOKEN"
    ]
  }
}
```

### 4.2 config/projects/say.json (없을 때만 생성)

```json
{
  "name": "SAY",
  "platform": "admin",
  "current_version": "",
  "jira": {
    "project_key": "SAY",
    "board_id": ""
  },
  "confluence": {
    "space_key": "SAY",
    "parent_page_id": "",
    "pages": {
      "scenarios": "",
      "test_cases": "",
      "reports": ""
    }
  },
  "figma": {
    "file_id": ""
  },
  "automation": {
    "test_repo": "",
    "script_path": "",
    "base_url": "",
    "framework": "pytest"
  },
  "features": {}
}
```

### 4.3 config/projects/bay.json (없을 때만 생성)

```json
{
  "name": "BAY",
  "platform": "admin",
  "current_version": "",
  "jira": {
    "project_key": "BAY",
    "board_id": ""
  },
  "confluence": {
    "space_key": "BAY",
    "parent_page_id": "",
    "pages": {
      "scenarios": "",
      "test_cases": "",
      "reports": ""
    }
  },
  "figma": {
    "file_id": ""
  },
  "automation": {
    "test_repo": "",
    "script_path": "",
    "base_url": "",
    "framework": "pytest"
  },
  "features": {}
}
```

### 4.4 config/projects/sso.json (없을 때만 생성)

```json
{
  "name": "SSO",
  "platform": "common",
  "current_version": "",
  "jira": {
    "project_key": "SSO",
    "board_id": ""
  },
  "confluence": {
    "space_key": "SSO",
    "parent_page_id": "",
    "pages": {
      "scenarios": "",
      "test_cases": "",
      "reports": ""
    }
  },
  "figma": {
    "file_id": ""
  },
  "automation": {
    "test_repo": "",
    "script_path": "",
    "base_url": "",
    "framework": "pytest"
  },
  "features": {}
}
```

### 4.5 templates/figma_review_prompt.md (없을 때만 생성)

```markdown
# Figma 검수 가이드

> 이 문서는 Claude in Chrome이 Figma 화면과 시나리오를 대조 검수할 때 참고하는 가이드입니다.

---

## 검수 항목

현재 보이는 Figma 화면과 사용자가 제공한 시나리오를 대조하여 아래 항목을 확인하세요.

1. **UI 요소 누락**: 시나리오의 버튼, 입력 필드, 텍스트 등이 Figma에 모두 존재하는지
2. **문구 일치**: 레이블, placeholder, 토스트, Alert 문구가 Figma와 정확히 일치하는지
3. **상태별 화면**: Default / Active / Disabled / Error 등 상태가 Figma에 정의되어 있는지
4. **시나리오 미반영**: Figma에는 있지만 시나리오에 빠진 UI 요소나 인터랙션이 있는지
5. **불일치 리포트 확인**: 사용자가 불일치 리포트를 함께 제공한 경우, 해당 항목이 실제 Figma에서 확인되는지

---

## 출력 형식

불일치 항목을 아래 표로 정리하세요.

| # | 항목 | Figma | 시나리오 | 판정 | 비고 |
|---|------|-------|----------|------|------|
| 1 | 버튼 레이블 | "저장하기" | "저장" | 불일치 | Figma 기준으로 수정 필요 |

판정 기호: 일치 / 불일치 / Figma 미정의 / 확인 필요

---

## 종합 판단

마지막에 아래 중 하나로 종합 판단하세요.

| 판정 | 기준 |
|------|------|
| **PASS** | 불일치 없음, 시나리오 확정 가능 |
| **수정 필요 (N건)** | 불일치 N건, 시나리오 수정 후 확정 |
| **기획자 확인 필요** | Figma와 기획서 모두 불명확한 항목 있음 |
```

### 4.6 .gitignore (없을 때만 생성)

```
.env
*.pyc
__pycache__/
.pytest_cache/
node_modules/
```

---

## 5. 처리 규칙

1. **이미 존재하는 폴더/파일은 절대 덮어쓰지 않는다** (건너뛰기)
2. 폴더 생성 시 `mkdir -p` 방식으로 중간 경로도 함께 생성
3. 모든 작업 완료 후 결과를 요약 출력

---

## 6. 완료 출력 형식

```
초기화 완료!

[폴더]
  생성됨: config/, config/projects/, data/scenarios/, data/tc/, ...
  이미 존재: (해당 시 표시)

[파일]
  생성됨: config/common.json, config/projects/say.json, templates/figma_review_prompt.md, ...
  이미 존재: (해당 시 표시)

다음 단계: /setup 을 실행하여 설정값을 입력하세요.
```
