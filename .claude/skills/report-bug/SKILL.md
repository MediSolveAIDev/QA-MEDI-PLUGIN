# /report-bug - Bug Reporter

> JIRA 티켓 관리 전담 에이전트. 버그 수집/등록 + 현황 조회/보고서 + 티켓 상태 관리까지 담당한다.
>
> **전제 조건**: Atlassian MCP 서버 연결 + JIRA 설정 완료 (`/setup`에서 설정)

---

## 1. 개요

- **역할**: JIRA 전담 — 버그 이슈 등록, 현황 조회/보고서, 티켓 상태 관리
- **3개 모드**:
  - **Mode 1: collect + execute** (Phase A/B) — 자동화 테스트 → 이슈 리스트 → 팀장 승인 → 티켓 등록
  - **Mode 2: query** (Phase Q) — 프로젝트/상태/버전 등 필터 기반 버그 현황 조회 + QA 분석 보고서
  - **Mode 3: manage** (Phase M) — 특정 티켓 상태 변경, 담당자 변경, 코멘트 추가
- **호출 시점**: 파이프라인 Phase 3에서 자동 호출(Mode 1), 또는 팀장 직접 요청(Mode 2/3)
- **출력**:
  - Mode 1: `data/bugs/{PROJECT}_{version}_{feature}_bug.json`
  - Mode 2: `data/bugs/{PROJECT}_{version}_report.json` + `data/bugs/{PROJECT}_{version}_report.html`
  - Mode 3: 실행 결과 JSON (대화형 응답)

---

## 2. 실행

```
# ── Mode 1: 이슈 등록 (파이프라인 연계) ──
# Phase A: 수집 모드 (Orchestrator → report-bug)
/report-bug collect SAY v1.4.0 --fail-analysis data/fail_analysis/SAY_v1.4.0_fail-analysis.json

# Phase B: 실행 모드 (Orchestrator → report-bug)
/report-bug execute SAY v1.4.0 --instructions data/bugs/SAY_v1.4.0_instructions.json

# 수동 호출 (팀장이 직접)
/report-bug SAY

# ── Mode 2: 현황 조회/보고서 ──
/report-bug query SAY --version v1.4.0 --status Open,Reopened
/report-bug query SAY --version v1.4.0 --severity Critical,Major --component "AI가이드"
/report-bug query SAY --period 30d --assignee 김개발

# ── Mode 3: 티켓 관리 ──
/report-bug manage CENSAY-234 --action reopen --comment "v1.4.0에서 재발"
/report-bug manage CENSAY-512 --action close --build "stg_v1.4.0-rc.4" --comment "정상 동작 확인"
/report-bug manage CENSAY-301 --action assign --assignee 김개발
/report-bug manage CENSAY-301 --action comment --comment "우회 방법 공유"
```

### 2.1 모드별 요약

| 모드 | 용도 | 호출 주체 | 출력 |
|------|------|-----------|------|
| Mode 1 (collect+execute) | 자동화 테스트 → 이슈 등록 | Orchestrator / 팀장 | bug JSON |
| Mode 2 (query) | 버그 현황 조회 + QA 분석 보고서 | 팀장 | JSON + HTML |
| Mode 3 (manage) | 티켓 상태/담당자/코멘트 변경 | 팀장 | 실행 결과 JSON |

### 2.2 Mode 1 전체 플로우

```
[자동] 구글 시트 폴링 → FAIL 행 감지
      ↓
[자동] Phase A: 수집 + 분석
  ├─ 1. 중복 확인: JQL로 기존 티켓 검색
  ├─ 2. 이슈 판단: 실제 버그 / 환경 이슈 / 테스트 데이터 문제 / 기획 변경 분류
  ├─ 3. 그룹핑: 동일 현상 묶기
  ├─ 4. 상세 내용 정리: description 템플릿 자동 작성
  ├─ 5. 심각도 추천
  └─ 6. 등록 추천: 신규등록 / 리오픈 / 스킵
      ↓
[자동] 알림: "FAIL N건 → 버그 M건 분류 완료"
      ↓
[자동] 이슈 리스트 제시
  ├─ "BUG-001: 신규등록 추천 (유사 티켓 없음)"
  ├─ "BUG-002: 리오픈 추천 (TEST-15와 동일 현상)"
  └─ "BUG-003: 스킵 추천 (환경 이슈로 판단)"
      ↓
[수동] 팀장 검토 → 담당자 지정 → 컨펌
  예: "1, 2번 등록해. 담당자 홍길동"
      ↓
[자동] Phase B: 실행
  ├─ JIRA 티켓 생성 / 리오픈 (MCP)
  └─ Google Sheet TC에 BTS ID 역기록
      ↓
[자동] 실행 결과 요약 보고
```

### 2.3 폴링 설정

#### 자연어 명령

| 자연어 | 동작 |
|--------|------|
| "폴링 시작해" / "시트 감시 켜줘" / "FAIL 감시 시작" | `poll_sheet.py` 백그라운드 실행 + `.poll_active` 플래그 생성 |
| "폴링 멈춰" / "시트 감시 꺼줘" / "FAIL 감시 중지" | `.poll_active` 플래그 삭제 (스크립트 일시정지) |
| "폴링 종료해" | `.poll_stop` 플래그 생성 (스크립트 프로세스 종료) |
| "폴링 상태" / "시트 감시 상태" | `.poll_active` 존재 여부 + `pending_bugs.json` 확인 |
| "폴링 결과 보여줘" / "폴링 결과 확인" / "미등록 버그 있어?" | `data/bugs/pending_bugs.json` 읽고 등록안 제시 |

> **"FAIL 분석 결과 확인해줘"**는 pipeline의 fail_analysis를 의미한다 (기존 파이프라인).
> 폴링 결과를 확인할 때는 **"폴링 결과"**라는 키워드를 사용한다.

#### 실행

```bash
# 폴링 시작 (백그라운드)
python tools/poll_sheet.py --sheet {SHEET_ID} --tab {TAB_NAME} --interval 600 &

# 예시
python tools/poll_sheet.py --sheet 1MIPNna8-l4chjAtlSBEsYEn5kGqOaEjg7eBWBHtvHKc --tab "1.4.0의 사본"
```

#### 파일 구조

| 파일 | 용도 |
|------|------|
| `tools/poll_sheet.py` | 폴링 스크립트 (`/init`에서 생성) |
| `data/bugs/.poll_active` | 존재하면 폴링 활성화 |
| `data/bugs/.poll_stop` | 존재하면 스크립트 종료 |
| `data/bugs/pending_bugs.json` | 미등록 FAIL 분석 결과 (매 폴링 시 갱신) |

#### 동작 규칙

- FAIL 판단: J컬럼 = "F" + N컬럼(BTS ID) = 비어있음
- 경로 조합: A~G컬럼 fill-down (상위 행에서 빈 셀 채움)
- 중복 알림 방지: `alerted_rows` 관리. 이미 알림한 행은 재알림 안 함
- 신규 FAIL이 없으면 알림 발송 안 함, `pending_bugs.json` 갱신 안 함
- 등록 완료된 건: 시트 N컬럼에 BTS ID 입력되면 다음 폴링에서 자동 제외
- 슬랙 알림: `.env`의 `SLACK_WEBHOOK_URL` 사용. UTF-8 인코딩 필수

> **시트 정보는 실행 시 입력**. 매번 다른 시트를 대상으로 폴링 가능.

---

## 3. Phase A: 수집 모드

### 3.1 입력

- `/analyze-fail` 산출물: `data/fail_analysis/{PROJECT}_{version}_fail-analysis.json`
- 또는 수동 입력 (대화형):

```
🐛 버그 리포트를 작성합니다.

1. 프로젝트: SAY / BAY / SSO
2. 버전: (예: v1.4.0)
3. 화면/기능: (예: AI 가이드 대시보드 > 기간 선택)
4. 현상 설명: (무엇이 잘못되었는지)
5. 재현 경로: (어떻게 하면 발생하는지)
6. 기대 결과: (정상이라면 어떻게 되어야 하는지)
7. 심각도: Critical / Major / Minor / Trivial
8. 스크린샷/영상: (파일 경로 또는 URL)
9. 환경: (브라우저, OS, 테스트 서버)
```

### 3.1.1 Description 템플릿

이슈 생성 시 description은 아래 구조를 따른다. **반드시 멀티라인으로 전달** (`\n` 이스케이프 금지).

```
**[Test Environment]**

- 플랫폼 정보 : {platform}
- 빌드 버전 & 서버 : {build}
- 계정 : {account}

**[Precondition]**

1. {전제조건_1}
2. {전제조건_2}

**[Step]**

1. {재현_1단계}
2. {재현_2단계}
3. {재현_3단계}

**[Actual Result]**

- {실제 결과}

**[Expected Result]**

- {기대 결과}

**[Note]**

- {비고/재현빈도/관련정보}
```

미입력 항목은 추가 질문으로 수집.

### 3.1.2 필드 자동/수동 매핑 규칙

| 필드 | 소스 | 방식 | 비고 |
|------|------|------|------|
| 타이틀 (summary) | FAIL 내용 | **AI 자동 생성** | `[화면명] 현상 요약` 형식 |
| 상세 내용 (description) | FAIL 내용 | **AI 자동 생성** | 3.1.1 템플릿 적용 |
| 컴포넌트 | 구글 시트 | **시트에서 자동** | TC의 화면/컴포넌트 컬럼 |
| 영향 버전 | 구글 시트 | **시트에서 자동** | TC의 버전 컬럼 |
| 우선순위 | FAIL 패턴 분석 | **AI 추천** + 팀장 컨펌 | 재현 빈도, 영향 범위 기반 |
| 담당자 | 팀장 지정 | **건별 수동** | 팀장이 이슈별로 직접 지정 (예: "이거 홍길동") |

> **담당자 자동 매핑**: 컴포넌트 → 담당자 매핑 테이블을 만들면 자동화 가능.
> 현재는 팀장이 건별로 지정하는 방식으로 운영. 필요 시 매핑 테이블 추가.

### 3.2 JIRA 후보 검색 (JQL)

각 버그 건에 대해 JIRA에서 유사 티켓을 검색한다:

```sql
-- Step 1: 같은 프로젝트 + 컴포넌트 + 미해결 + 최근 60일
project = {project_key} AND issuetype = Bug
AND status not in (Done, Closed)
AND component = "{component}"
AND created >= -60d
ORDER BY created DESC

-- Step 2: 키워드 보완 검색 (Step 1 결과 부족 시)
project = {project_key} AND issuetype = Bug
AND summary ~ "{키워드}"
```

### 3.3 후보 티켓 이력 수집

후보 티켓이 있으면 다음 정보를 수집한다:

| 수집 항목 | API | 용도 |
|-----------|-----|------|
| 기본 필드 | `GET /issue/{key}` | summary, status, priority, assignee, component |
| 상태 변경 이력 | `GET /issue/{key}?expand=changelog` | 리오픈 횟수, 리오픈 시점, 담당자 변경 |
| 코멘트 | `fields.comment` | 개발자 분석 내용, 우회 방법, "다음 스프린트로 미룸" 등 |
| 이슈 링크 | `fields.issuelinks` | 관련 이슈 체인 (caused by, duplicates, relates to) |
| 하위 이슈 | `subtasks` | 분리된 작업 존재 여부 |

**changelog 파싱 규칙:**
- `status` 필드에서 `→ Reopened` 횟수 = 리오픈 횟수
- `assignee` 변경 횟수 = 핑퐁 지표
- `priority` 상향 변경 = 심각도 증가 이력

---

## 4. 출력 형식

### 4.1 Phase A 보고서 JSON

Orchestrator에게 전달하는 수집 결과. Orchestrator가 이 데이터를 분석하여 추천안을 만든다.

```json
{
  "phase": "collect",
  "project": "SAY",
  "version": "v1.4.0",
  "collected_at": "2026-03-17T14:30:00",
  "bugs": [
    {
      "bug_id": "BUG-SAY-001",
      "summary": "[AI 가이드 대시보드] 기간 선택 시 달력 모달이 닫히지 않음",
      "severity": "major",
      "priority": "P2",
      "reporter": "QA_Agent",
      "environment": {
        "browser": "Chrome 122",
        "os": "Windows 11",
        "server": "dev-say.example.com"
      },
      "description": {
        "steps": ["1. AI 가이드 대시보드 진입", "2. 기간 선택 필드 Tap", "3. 시작일 선택", "4. 종료일 선택"],
        "expected": "모달 자동 닫힘, 대시보드 데이터 갱신",
        "actual": "모달이 닫히지 않고 유지됨, 데이터 미갱신",
        "frequency": "항상 재현"
      },
      "attachments": [],
      "related_tc": "Row 65",
      "jira_fields": {
        "project_key": "CENSAY",
        "issue_type": "Bug",
        "labels": ["QA-Agent", "v1.4.0"],
        "component": "AI가이드"
      },
      "jira_candidates": [
        {
          "key": "CENSAY-234",
          "summary": "[AI 가이드] 달력 모달 미닫힘",
          "status": "Reopened",
          "assignee": "김개발",
          "reopen_count": 2,
          "reopen_history": [
            {"date": "2026-01-15", "from": "Resolved", "to": "Reopened", "by": "이QA"},
            {"date": "2026-02-20", "from": "Resolved", "to": "Reopened", "by": "이QA"}
          ],
          "assignee_changes": 3,
          "priority_changes": [{"date": "2026-02-20", "from": "Minor", "to": "Major"}],
          "last_comment": "v1.3.0에서 수정했는데 v1.3.2에서 재발",
          "linked_issues": ["CENSAY-189 (is caused by)"],
          "similarity": "high"
        },
        {
          "key": "CENSAY-301",
          "summary": "[대시보드] 날짜 필터 동작 안함",
          "status": "Done",
          "reopen_count": 0,
          "last_comment": "환경 이슈로 확인, 재현 불가",
          "similarity": "low"
        }
      ]
    }
  ]
}
```

### 4.2 Phase B 실행 지시서 JSON (Orchestrator → report-bug)

팀장 선별 후 Orchestrator가 생성하여 report-bug에 전달한다.

```json
{
  "phase": "execute",
  "project": "SAY",
  "version": "v1.4.0",
  "instructions": [
    {
      "bug_id": "BUG-SAY-001",
      "action": "reopen",
      "target_key": "CENSAY-234",
      "comment": "v1.4.0에서 재발 확인. 달력 모달 미닫힘 현상 동일.",
      "attachments": ["screenshots/bug001.png"]
    },
    {
      "bug_id": "BUG-SAY-002",
      "action": "create",
      "jira_fields": {
        "project_key": "CENSAY",
        "summary": "[대시보드] 차트 데이터 0건 표시",
        "description": "대시보드 진입 시 차트 영역에 데이터 0건으로 표시...",
        "issue_type": "Bug",
        "priority": "Major",
        "component": "대시보드",
        "labels": ["QA-Agent", "v1.4.0"]
      },
      "attachments": []
    },
    {
      "bug_id": "BUG-SAY-003",
      "action": "create_and_link",
      "jira_fields": {
        "project_key": "CENSAY",
        "summary": "[설정] 알림 토글 반영 안됨",
        "description": "...",
        "issue_type": "Bug",
        "priority": "Minor",
        "component": "설정",
        "labels": ["QA-Agent", "v1.4.0"]
      },
      "link_to": {"key": "CENSAY-301", "type": "relates to"}
    }
  ]
}
```

### 4.3 Phase B 실행 결과 JSON (report-bug → Orchestrator)

```json
{
  "phase": "execute_result",
  "project": "SAY",
  "version": "v1.4.0",
  "executed_at": "2026-03-17T15:00:00",
  "results": [
    {
      "bug_id": "BUG-SAY-001",
      "action": "reopen",
      "jira_key": "CENSAY-234",
      "status": "success",
      "new_status": "Reopened"
    },
    {
      "bug_id": "BUG-SAY-002",
      "action": "create",
      "jira_key": "CENSAY-512",
      "status": "success",
      "new_status": "Open"
    },
    {
      "bug_id": "BUG-SAY-003",
      "action": "create_and_link",
      "jira_key": "CENSAY-513",
      "status": "success",
      "new_status": "Open",
      "linked_to": "CENSAY-301"
    }
  ],
  "bts_mapping": [
    {"tc_row": "Row 65", "jira_key": "CENSAY-234"},
    {"tc_row": "Row 72", "jira_key": "CENSAY-512"},
    {"tc_row": "Row 80", "jira_key": "CENSAY-513"}
  ]
}
```
```

### 4.2 JIRA 연동 (활성화 시 구현 가이드)

#### 4.2.1 인프라 구성

| 구성 요소 | 현황 | 필요 작업 |
|-----------|------|-----------|
| Atlassian MCP 권한 | `settings.json`에 `mcp__atlassian__*` 허용됨 | - |
| Atlassian MCP 서버 | **연결 완료** (2026-03-24 검증) | - |
| JIRA 설정값 구조 | `config/common.json` + `.env` 구조 정의됨 | `/setup`으로 실제 값 입력 |
| Google Sheets MCP | 연동 완료 | BTS ID 역매핑에 활용 |

#### 4.2.2 MCP 검증 결과 (2026-03-24 TEST 프로젝트)

| 기능 | 결과 | MCP 도구 | 주의사항 |
|------|:----:|----------|----------|
| 이슈 생성 | **OK** | `jira_create_issue` | |
| 이슈 수정 (필드) | **OK** | `jira_update_issue` | 담당자: 이름으로 통일 (예: `{"assignee": "홍길동"}`) |
| 영향 버전 설정 | **OK** | `jira_update_issue` | `additional_fields: {"versions": [{"name": "1.0.0"}]}` |
| 코멘트 추가 | **OK** | `jira_add_comment` | |
| 상태 변경 | **OK** | `jira_transition_issue` | transition_id는 `jira_get_transitions`로 사전 조회 필요 |
| JQL 검색 | **OK** | `jira_search` | `total: -1` 반환. 무한스크롤 방식 추가 로딩. 버전별 분할 조회 권장 |

> **줄바꿈 규칙 (필수)**
>
> description, comment 등 모든 텍스트 필드는 **반드시 실제 멀티라인(줄바꿈)으로 전달**해야 한다.
> `\n` 이스케이프 문자열을 사용하면 리터럴 텍스트로 들어가서 줄바꿈이 안 된다.
>
> ```
> # NG — \n 이스케이프 (줄바꿈 안 됨)
> description: "1단계\n2단계\n3단계"
>
> # OK — 실제 멀티라인 (줄바꿈 정상)
> description: "1단계
> 2단계
> 3단계"
> ```
>
> **상태 변경 + 코멘트**: `transition_issue`의 comment 파라미터는 줄바꿈이 안 되므로,
> 반드시 `transition_issue`(상태변경만) + `add_comment`(댓글 별도) **2단계 분리 실행**한다.

#### 4.2.3 Atlassian MCP 서버 설치 방법

`~/.claude/.mcp.json`에 아래 추가:

```json
{
  "mcpServers": {
    "atlassian": {
      "command": "npx",
      "args": ["-y", "@anthropic/atlassian-mcp-server"],
      "env": {
        "ATLASSIAN_SITE_URL": "https://{your-domain}.atlassian.net",
        "ATLASSIAN_USER_EMAIL": "{jira-email}",
        "ATLASSIAN_API_TOKEN": "{jira-api-token}"
      }
    }
  }
}
```

> ⚠️ 실제 패키지명은 설치 시점에 npm 검색 필요 (커뮤니티: `@anthropic/atlassian-mcp-server`, `mcp-remote-atlassian` 등)

#### 4.2.4 REST API 직접 호출 (MCP 보완용)

```python
# pip install atlassian-python-api 또는 requests 직접 사용
import requests
from requests.auth import HTTPBasicAuth

base_url = config["jira"]["base_url"]  # config/common.json
auth = HTTPBasicAuth(config["jira"]["email"], os.getenv("JIRA_API_TOKEN"))

# 이슈 생성
resp = requests.post(f"{base_url}/rest/api/2/issue", auth=auth, json={
    "fields": {
        "project": {"key": "CENSAY"},
        "summary": "[화면명] 현상 요약",
        "description": "재현 경로...",
        "issuetype": {"name": "Bug"},
        "priority": {"name": "Major"},
        "labels": ["QA-Agent", "v1.4.0"]
    }
})
issue_key = resp.json()["key"]  # CENSAY-123

# 첨부파일 추가 (MCP 미지원 시)
requests.post(
    f"{base_url}/rest/api/2/issue/{issue_key}/attachments",
    auth=auth,
    headers={"X-Atlassian-Token": "no-check"},
    files={"file": open("screenshot.png", "rb")}
)
```

#### 4.2.5 목표 플로우 (선별 등록)

```
매뉴얼/자동화 테스트 결과
  ↓
/analyze-fail → Fail 건 분류
  ├─ 실제 버그 (Real Bug) ← JIRA 등록 대상
  ├─ 환경 이슈 (Environment)
  ├─ 테스트 데이터 문제
  └─ 기획 변경 필요
  ↓
팀장에게 Fail 건 요약 리포트 제시
  (번호 + 요약 + 심각도 + 등록 추천 여부)
  ↓
팀장 선별: "1번, 3번, 5번 등록해"
  ↓
선별된 건만 JIRA 티켓 생성 (/report-bug)
  ├─ MCP: 이슈 생성 + JQL 중복 확인
  ├─ API: 첨부파일 + 커스텀 필드
  ├─ TC ID → JIRA 이슈 키 연결
  └─ Google Sheet TC에 BTS ID 자동 매핑
```

#### 4.2.6 활성화 체크리스트

- [ ] Atlassian MCP 서버 설치 및 `.mcp.json` 등록
- [ ] `/setup`으로 JIRA 설정값 입력 (base_url, email, API token, project key)
- [ ] MCP 연결 테스트 (이슈 조회)
- [ ] 이슈 생성 테스트 (테스트 프로젝트)
- [ ] `/analyze-fail` → `/report-bug` 연계 구현
- [ ] 선별 등록 UX 구현 (팀장 승인 플로우)
- [ ] Google Sheet BTS ID 역매핑 구현
- [ ] 팀장 최종 승인 → 비활성화 배너 제거

---

## 5. 심각도 기준

| 심각도 | 기준 | Priority 매핑 |
|--------|------|---------------|
| Critical | 서비스 중단, 데이터 손실, 보안 이슈 | P1 |
| Major | 핵심 기능 동작 불가, 우회 방법 없음 | P1-P2 |
| Minor | 기능 동작하지만 비정상, 우회 가능 | P2-P3 |
| Trivial | UI 깨짐, 오타, 경미한 불편 | P3 |

---

## 6. Phase B: 실행 가능 액션

| 팀장 지시 | action 값 | JIRA API | 비고 |
|-----------|-----------|----------|------|
| "신규 등록해" | `create` | `POST /issue` | 기본 필드 + 라벨 + 컴포넌트 |
| "리오픈해" | `reopen` | `POST /issue/{key}/transitions` | 코멘트 자동 추가 |
| "등록하고 링크 걸어" | `create_and_link` | `POST /issue` + `POST /issueLink` | relates to / caused by |
| "심각도 올려" | `update_field` | `PUT /issue/{key}` | priority, severity 등 |
| "코멘트 달아" | `add_comment` | `POST /issue/{key}/comment` | |
| "스크린샷 첨부해" | `attach_file` | `POST /issue/{key}/attachments` | REST API 직접 호출 |
| "담당자 변경해" | `update_field` | `PUT /issue/{key}` | assignee |
| "Won't Fix로 닫아" | `close` | `POST /issue/{key}/transitions` | resolution 지정 |
| "하위 티켓 만들어" | `create_subtask` | `POST /issue` (subtask type) | parent 지정 |

**실행 후 후속 작업:**
- 생성/리오픈된 이슈 키를 `execute_result` JSON에 기록
- Google Sheet TC의 BTS ID 컬럼에 이슈 키 자동 매핑 (Google Sheets MCP 사용)
- `data/bugs/` 보고서 JSON에 실행 결과 반영

---

## 7. Mode 2: 버그 현황 조회/보고서 (Phase Q)

### 7.1 개요

JIRA에 쌓인 버그 티켓을 필터 기반으로 조회하여 현황 리포트를 생성하는 모드.
출력은 **JSON + HTML** 2종으로 동시 생성된다.

```
팀장: "SAY v1.4.0 버그 현황 정리해줘"
      ↓
/report-bug query SAY --version v1.4.0
      ↓
JQL 조회 → changelog 수집 → QA 분석 → JSON + HTML 보고서 출력
```

### 7.2 필터

| 필터 | 플래그 | JQL 매핑 | 필수/옵션 |
|------|--------|----------|-----------|
| 프로젝트 | (위치 인자) | `project = {key}` | 필수 |
| 상태 | `--status` | `status in (Open, Reopened)` | 옵션 (기본: 전체) |
| 버전 | `--version` | `affectsVersion in ("v1.4.0")` | 옵션 |
| 심각도 | `--severity` | `priority in (Critical, Major)` | 옵션 |
| 컴포넌트 | `--component` | `component = "AI가이드"` | 옵션 |
| 담당자 | `--assignee` | `assignee = "김개발"` | 옵션 |
| 기간 | `--period` | `created >= -30d` | 옵션 (기본: 전체) |
| 라벨 | `--label` | `labels = "QA-Agent"` | 옵션 |
| 리포터 | `--reporter` | `reporter = "이QA"` | 옵션 |

**복합 필터 예시:**
```bash
# 릴리즈 go/no-go 판단용
/report-bug query SAY --version v1.4.0 --severity Critical,Major --status Open,Reopened,"In Progress"

# 고질적 이슈 추적
/report-bug query SAY --status Reopened --period 30d

# 특정 영역 집중 분석
/report-bug query SAY --component "AI가이드" --version v1.3.0,v1.4.0
```

### 7.3 조회 데이터 수집

각 이슈에 대해 아래 정보를 수집한다:

| 수집 항목 | API | 용도 |
|-----------|-----|------|
| 기본 필드 | `GET /search` (JQL) | summary, status, priority, assignee, component, created, updated |
| 상태 변경 이력 | `expand=changelog` | 리오픈 횟수, 체류 기간 계산 |
| 이슈 링크 | `fields.issuelinks` | 연관 이슈 클러스터 파악 |

> ⚠️ 조회 결과 **최대 100건** 제한. 초과 시 필터 좁히기 안내.

### 7.4 QA 분석 항목

보고서에 포함되는 QA 관점 분석:

| 분석 항목 | 설명 | 판단 기준 |
|-----------|------|-----------|
| **릴리즈 리스크** | 미해결 Critical/Major 건수 | Critical ≥1 → 릴리즈 보류 권고 |
| **취약 영역** | 버그 집중 컴포넌트 | 전체 대비 30% 이상 집중 시 하이라이트 |
| **고질적 이슈** | 리오픈 2회 이상 반복 건 | changelog 파싱, 근본 원인 분석 필요 표시 |
| **처리 현황** | 해결률, 미배정 건, 장기 체류 건 | Open 14일 이상 체류 시 알림 |
| **버그 트렌드** | 기간별 등록/해결 추이 | `--period` 지정 시 일별/주별 집계 |
| **미배정 건** | 담당자 없는 티켓 | assignee = null |

### 7.5 출력 형식

#### 7.5.1 JSON (`data/bugs/{PROJECT}_{version}_report.json`)

```json
{
  "mode": "query",
  "project": "SAY",
  "version": "v1.4.0",
  "generated_at": "2026-03-24T10:00:00",
  "filters": {
    "status": ["Open", "Reopened"],
    "severity": ["Critical", "Major"],
    "component": null,
    "assignee": null,
    "period": null
  },
  "summary": {
    "total": 31,
    "by_status": {"Open": 11, "In Progress": 3, "Reopened": 2, "Resolved": 15},
    "by_severity": {"Critical": 1, "Major": 7, "Minor": 15, "Trivial": 8},
    "by_component": {"AI가이드": 12, "대시보드": 8, "설정": 6, "기타": 5},
    "resolution_rate": 48.4,
    "unassigned_count": 3
  },
  "analysis": {
    "release_risk": {
      "level": "high",
      "message": "미해결 Critical 1건, Major 4건 → 릴리즈 보류 권고",
      "blocking_issues": ["CENSAY-234"]
    },
    "vulnerable_areas": [
      {"component": "AI가이드", "count": 12, "percentage": 38.7, "highlight": true}
    ],
    "chronic_issues": [
      {"key": "CENSAY-234", "summary": "달력 모달 미닫힘", "reopen_count": 3},
      {"key": "CENSAY-189", "summary": "날짜 필터 초기화", "reopen_count": 2}
    ],
    "stale_issues": [
      {"key": "CENSAY-400", "summary": "차트 로딩 지연", "days_open": 21}
    ],
    "unassigned": [
      {"key": "CENSAY-450", "summary": "알림 설정 미반영", "severity": "Major"}
    ]
  },
  "issues": [
    {
      "key": "CENSAY-234",
      "summary": "[AI가이드] 달력 모달 미닫힘",
      "status": "Reopened",
      "priority": "Critical",
      "assignee": "김개발",
      "component": "AI가이드",
      "created": "2026-01-10",
      "updated": "2026-03-20",
      "reopen_count": 3,
      "linked_issues": ["CENSAY-189"]
    }
  ]
}
```

#### 7.5.2 HTML (`data/bugs/{PROJECT}_{version}_report.html`)

단일 `.html` 파일 (CSS + Chart.js 인라인, 외부 의존성 없음).

**구조:**

```
┌──────────────────────────────────────────────┐
│  {PROJECT} {version} 버그 현황 리포트         │
│  {날짜} 기준 | QA Agent 생성                  │
├──────────────────────────────────────────────┤
│  [요약 카드 4개]                              │
│  총 버그 | 미해결 | 해결률 | 고질적 이슈       │
├──────────────────────────────────────────────┤
│  [차트 영역] Chart.js CDN 인라인              │
│  ┌──────────┐ ┌──────────┐                   │
│  │상태별     │ │심각도별   │                   │
│  │도넛 차트  │ │바 차트    │                   │
│  └──────────┘ └──────────┘                   │
│  ┌──────────┐ ┌──────────┐                   │
│  │컴포넌트별 │ │트렌드     │                   │
│  │바 차트    │ │라인 차트  │                   │
│  └──────────┘ └──────────┘                   │
├──────────────────────────────────────────────┤
│  [QA 분석 섹션]                               │
│  ⚠️ 릴리즈 리스크: Critical 1건...            │
│  🔥 취약 영역: AI가이드 38%                   │
│  🔄 고질적 이슈: CENSAY-234 (3회 리오픈)      │
│  ⏰ 장기 체류: CENSAY-400 (21일)              │
│  👤 미배정: 3건                               │
├──────────────────────────────────────────────┤
│  [버그 리스트 테이블]                          │
│  티켓키 | 요약 | 상태 | 심각도 | 담당자 | ...  │
│  (정렬 가능, JIRA 링크 클릭)                   │
└──────────────────────────────────────────────┘
```

**HTML 생성 규칙:**
- Chart.js는 CDN URL을 `<script>` 태그로 인라인 포함
- 테이블은 컬럼 헤더 클릭으로 정렬 가능 (JS 인라인)
- 티켓 키는 JIRA URL 링크 (`config/common.json`의 `jira.base_url` + `/browse/{key}`)
- 색상 코딩: Critical=빨강, Major=주황, Minor=노랑, Trivial=회색
- 반응형 레이아웃 (모바일에서도 확인 가능)

---

## 8. Mode 3: 티켓 관리 (Phase M)

### 8.1 개요

특정 JIRA 티켓의 상태 변경, 담당자 변경, 코멘트 추가를 수행하는 모드.
팀장이 직접 요청하여 사용한다.

```
팀장: "CENSAY-234 리오픈해줘, v1.4.0에서 재발했어"
      ↓
/report-bug manage CENSAY-234 --action reopen --build "stg_v1.4.0-rc.4" --comment "달력 모달 미닫힘 재발"
      ↓
상태 변경 (transition) + 코멘트 자동 추가 → 결과 확인
```

### 8.2 지원 액션

| 액션 | `--action` | API | 코멘트 |
|------|-----------|-----|--------|
| 리오픈 | `reopen` | `POST /issue/{key}/transitions` | **필수** (리오픈 템플릿) |
| 종료 | `close` | `POST /issue/{key}/transitions` | **필수** (종료 템플릿) |
| 담당자 변경 | `assign` | `PUT /issue/{key}` | 선택 |
| 코멘트 추가 | `comment` | `POST /issue/{key}/comment` | 내용 직접 입력 |

### 8.3 코멘트 템플릿

#### 종료 시 (close)

```
- 확인 결과 : PASS
- 플랫폼 정보 : {platform}
- 빌드 버전 & 서버 : {build}
- 확인 내용 : {comment}

수정 확인하여 티켓 종료합니다.
```

**입력 매핑:**
| 필드 | 플래그 | 기본값 | 비고 |
|------|--------|--------|------|
| `{platform}` | `--platform` | `Windows 11` | 자동 감지 또는 수동 입력 |
| `{build}` | `--build` | (필수 입력) | 예: `stg_v1.4.0-rc.4`, `prod_v1.4.0` |
| `{comment}` | `--comment` | (필수 입력) | 실제 확인 내용 |

#### 리오픈 시 (reopen)

```
- 확인 결과 : FAIL
- 플랫폼 정보 : {platform}
- 빌드 버전 & 서버 : {build}
- 확인 내용 : {comment}

현상 재현되어 리오픈 합니다. 확인 부탁 드립니다.
```

**입력 매핑:** 종료 시와 동일 (`--platform`, `--build`, `--comment`)

### 8.4 실행 플로우

```
1. 티켓 키로 현재 상태 조회 (jira_get_issue)
2. 요청한 transition이 가능한지 확인 (jira_get_transitions)
   - 불가능하면 현재 상태 + 가능한 transition 목록 안내 후 중단
3. transition 실행 — 상태변경만 (jira_transition_issue, comment 파라미터 사용 X)
4. 코멘트 템플릿 조립 후 별도 등록 (jira_add_comment, 멀티라인으로 전달)
5. 결과 확인 후 응답
```

> **주의**: transition_issue의 comment 파라미터는 줄바꿈이 안 되므로
> 반드시 3번(상태변경) → 4번(코멘트) 2단계로 분리 실행한다.

### 8.5 실행 결과 JSON

```json
{
  "mode": "manage",
  "executed_at": "2026-03-24T14:30:00",
  "action": "close",
  "ticket": {
    "key": "CENSAY-512",
    "previous_status": "Resolved",
    "new_status": "Closed",
    "comment_added": true
  },
  "comment": "- 확인 결과 : PASS\n- 플랫폼 정보 : Windows 11\n- 빌드 버전 & 서버 : stg_v1.4.0-rc.4\n- 확인 내용 : 정상 동작 확인\n\n수정 확인하여 티켓 종료합니다."
}
```

### 8.6 향후 확장 (v2)

```
팀장: "SAY Resolved 티켓 보여줘"
      ↓
/report-bug query SAY --status Resolved --version v1.4.0
      ↓
[Resolved 리스트 출력]
  1. CENSAY-512 [대시보드] 차트 데이터 0건 표시
  2. CENSAY-513 [설정] 알림 토글 반영 안됨
  3. CENSAY-520 [AI가이드] 추천 카드 미노출
      ↓
팀장: "1번, 3번 종료해줘"
      ↓
선택 건 일괄 종료 (각각 코멘트 템플릿 적용)
```

> v2는 Mode 2 (query)와 Mode 3 (manage) 조합으로 자연스럽게 확장된다.

---

## 9. 규칙

- summary는 `[화면명] 현상 요약` 형식 (50자 이내)
- 재현 경로는 번호 매기기 필수 (1, 2, 3...)
- 스크린샷 있으면 `attachments`에 경로 포함
- Phase A에서 JIRA 후보 검색은 **최대 50건**으로 제한 (API 부하 방지)
- changelog 파싱 시 리오픈 횟수 0이면 `reopen_history` 필드 생략
- Phase B 실행 전 반드시 Orchestrator의 실행 지시서가 있어야 함 (직접 실행 금지)
- 실행 실패 시 에러를 `execute_result`에 기록하고 Orchestrator에 보고 (재시도 안 함)
- `/analyze-fail`에서 자동 호출 시 TC 행 번호 자동 매핑
- **Jira 이슈 등록 후 구글 시트 BTS ID 역기록은 자동으로 수행한다** (별도 요청 불필요)
  - 등록된 Jira 키(예: TEST-42)를 해당 TC 행의 N컬럼(BTS ID)에 기록
  - Google Sheets MCP `update_cells` 사용
- **TC Priority → 버그 심각도 변환**: 시트의 Priority는 TC 중요도이므로, 버그 등록 시 아래 기준으로 변환하여 추천
  - 핵심 기능 동작 불가 + 우회 없음 → Highest/High
  - 기능 동작하지만 비정상 + 우회 가능 → Medium
  - UI/표시 문제 + 경미한 불편 → Low
