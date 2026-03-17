# /report-bug - Bug Reporter

> **⚠️ 현재 비활성화 상태입니다. 이 스킬은 아직 운영에 투입되지 않았습니다.**
> 활성화 시점: JIRA API 연동 완료 후 팀장 승인 시

> JIRA 티켓 관리 전담 에이전트. 버그 수집/정리 + JIRA 검색/이력 분석 + 티켓 실행(생성/리오픈/수정)까지 담당한다.

---

## 1. 개요

- **역할**: JIRA 전담 — 버그 정보 수집, 기존 티켓 검색/이력 분석, 티켓 실행(생성/리오픈/수정/링크)
- **2-Phase 호출**: Orchestrator가 동일 스킬을 2회 호출한다
  - **Phase A (수집)**: Fail 건 정보 수집 + JIRA 후보 검색 + 이력 분석 → 보고서 JSON 출력
  - **Phase B (실행)**: Orchestrator의 실행 지시서를 받아 JIRA 액션 수행
- **호출 시점**: `/analyze-fail`에서 실제 버그 판정 후, 또는 수동 테스트 중 버그 발견 시
- **출력**: `data/bugs/{PROJECT}_{version}_{feature}_bug.json`

---

## 2. 실행

```
# Phase A: 수집 모드 (Orchestrator → report-bug)
/report-bug collect SAY v1.4.0 --fail-analysis data/fail_analysis/SAY_v1.4.0_fail-analysis.json

# Phase B: 실행 모드 (Orchestrator → report-bug)
/report-bug execute SAY v1.4.0 --instructions data/bugs/SAY_v1.4.0_instructions.json

# 수동 호출 (팀장이 직접)
/report-bug SAY
```

### 2.1 전체 플로우

```
/analyze-fail → Fail 분류 (실제 버그 판별)
      ↓
/report-bug [Phase A: 수집]
  ├─ 버그별 JIRA JQL 후보 검색
  ├─ 후보 티켓 changelog 조회 (리오픈 이력, 상태 변경)
  ├─ 후보 티켓 코멘트/링크 수집
  └─ 정형화된 보고서 JSON 출력
      ↓
Orchestrator → 보고서 종합 분석
  ├─ "CENSAY-234 리오픈 추천 (3번째 재발, 고질적)"
  ├─ "신규 등록 추천 (유사 티켓 없음)"
  └─ "CENSAY-301과 관련 있으나 별개 현상, 링크 연결 추천"
      ↓
팀장에게 요약 + 추천안 제시 → 팀장 선별/방향 제시
      ↓
Orchestrator → 실행 지시서 생성
      ↓
/report-bug [Phase B: 실행]
  ├─ JIRA 티켓 생성 / 리오픈 / 수정 / 링크 연결
  ├─ 첨부파일 업로드
  └─ Google Sheet TC에 BTS ID 매핑
      ↓
Orchestrator → 실행 결과 요약 보고
```

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

미입력 항목은 추가 질문으로 수집.

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
| Atlassian MCP 서버 | **미설치** | `.mcp.json`에 서버 등록 필요 |
| JIRA 설정값 구조 | `config/common.json` + `.env` 구조 정의됨 | `/setup`으로 실제 값 입력 |
| Google Sheets MCP | 연동 완료 | BTS ID 역매핑에 활용 |

#### 4.2.2 MCP vs REST API 기능 비교

| 기능 | Atlassian MCP | JIRA REST API 직접 호출 | 비고 |
|------|:---:|:---:|------|
| 이슈 생성 (기본 필드) | O | O | summary, description, priority, labels |
| 이슈 생성 (커스텀 필드) | △ | O | MCP 서버 구현에 따라 다름 |
| 첨부파일 (스크린샷) | △ | O | 대부분 MCP 미지원, API 직접 호출 필요 |
| JQL 검색 (중복 확인) | O | O | |
| 이슈 링크 (관련 이슈 연결) | △ | O | |
| Transition (상태 변경) | O | O | |
| 벌크 생성 (다건 일괄) | X | O | REST API `/rest/api/2/issue/bulk` |
| Google Sheet BTS ID 매핑 | - | - | Google Sheets MCP로 별도 처리 |

> **추천**: MCP 우선 + REST API 보완 조합. 기본 CRUD는 MCP, 첨부파일/커스텀필드/벌크는 API 직접 호출.

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

## 7. 확장 가능성: 버그 현황 조회/분석 (Phase Q)

> 현재는 이슈 중복 확인 + 등록(Phase A/B)만 구현 대상이다.
> 향후 아래 기능으로 확장 가능하며, QA 관점 분석 기준은 활성화 시점에 구체화한다.

### 7.1 개요

JIRA에 이미 쌓인 버그 티켓을 **컴포넌트 + 영향 버전** 기준으로 조회하여 현황을 정리하는 모드.

```
팀장: "AI가이드 컴포넌트, v1.3.0~v1.4.0 버그 정리해줘"
      ↓
/report-bug query --component "AI가이드" --versions "v1.3.0,v1.4.0"
      ↓
JQL 조회 → changelog 수집 → 현황 리포트 출력
```

### 7.2 조회 가능 항목

| 항목 | JQL / API | 비고 |
|------|-----------|------|
| 컴포넌트별 버그 목록 | `component = "X"` | |
| 특정 버전 영향 버그 | `affectsVersion in ("v1.3.0", "v1.4.0")` | |
| 상태별 분류 | `status` 필드 | Open/In Progress/Resolved/Closed/Reopened |
| 심각도 분포 | `priority` 필드 | Critical/Major/Minor/Trivial |
| 고질적 이슈 (리오픈 반복) | changelog `→ Reopened` 카운트 | |
| 담당자별 현황 | `assignee` 필드 | 미배정 건 포함 |
| 이슈 체인 | `issuelinks` | 연관 이슈 클러스터 |

### 7.3 QA 관점 분석 (활성화 시 구체화 필요)

아래는 출력에 포함할 QA 관점 분석 항목 후보. 실제 운영 시 팀 기준에 맞춰 확정한다.

- **고질적 이슈 하이라이트**: 리오픈 2회 이상, 근본 원인 분석 필요 여부
- **미해결 건 현황**: 담당자/상태/체류 기간
- **영역 집중도**: 특정 컴포넌트/화면에 버그 집중 여부
- **미배정 건**: 담당자 없는 티켓 알림
- **릴리즈 리스크**: 해당 버전 미해결 Critical/Major 건수
- **버그 트렌드**: 기간별 등록/해결 추이

> ⚠️ QA 관점 분석 기준은 팀 운영 경험이 쌓인 후 `/learn-rules`로 패턴화하여 규칙에 반영한다.

---

## 8. 규칙

- summary는 `[화면명] 현상 요약` 형식 (50자 이내)
- 재현 경로는 번호 매기기 필수 (1, 2, 3...)
- 스크린샷 있으면 `attachments`에 경로 포함
- Phase A에서 JIRA 후보 검색은 **최대 50건**으로 제한 (API 부하 방지)
- changelog 파싱 시 리오픈 횟수 0이면 `reopen_history` 필드 생략
- Phase B 실행 전 반드시 Orchestrator의 실행 지시서가 있어야 함 (직접 실행 금지)
- 실행 실패 시 에러를 `execute_result`에 기록하고 Orchestrator에 보고 (재시도 안 함)
- `/analyze-fail`에서 자동 호출 시 TC 행 번호 자동 매핑
