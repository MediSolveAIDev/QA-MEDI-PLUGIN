---
name: file-bug
description: 수동 테스트 중 발견한 버그를 구두 설명만으로 JIRA 포맷 작성 + 등록까지 원스톱 처리합니다. 스크린샷/텍스트 설명을 전달하세요.
argument-hint: [스크린샷 또는 버그 설명]
---

# /file-bug - Quick Bug Filer

> 수동 테스트 중 발견한 버그를 **구두 설명(또는 스크린샷)만으로 JIRA 이슈까지 등록**하는 원스톱 스킬.
> 질문하지 않고 바로 작성 → 팀장 확인 → JIRA 등록.

> **본 스킬은 `.claude/rules/tc_writing_rule.md` 규칙을 따른다.**
> 버그 리포트의 재현 절차는 관련 TC가 있으면 그 TC의 **`precondition` + `step`** 필드를 그대로 복사 사용한다.
> - 관련 TC ID(예: `RSV-FLT-001`)가 있으면 JIRA 본문에 명시
> - 약어 ID의 L2 약어(예: `FLT` = 좌측 필터 패널)로 JIRA 컴포넌트 자동 매핑 가능
> - 본문은 비즈니스 용어만 (개발 용어·HTTP 코드는 별도 필드)
>
> **기존 스킬과의 차이:**
> - `/report-bug`: 파이프라인 연계 (Phase A/B 분리, 자동화 테스트 FAIL 기반)
> - `/file-bug`: **수동 테스트 즉시 등록** (구두 설명 → JIRA 포맷 → 승인 → 등록)

---

## 1. 개요

- **역할**: 팀장이 말한 버그 설명을 JIRA 이슈 포맷으로 정형화 + JIRA 등록
- **호출 시점**: 수동 테스트 중 버그 발견 시 즉시
- **전제 조건**: `config/project.json` 존재 + Atlassian MCP 연결
- **출력**: JIRA 이슈 생성 + `data/bugs/{PROJECT}_{version}_{feature}_bug.json`

---

## 2. 실행

```
# 스크린샷 + 설명
/file-bug [스크린샷 첨부] 달력 모달이 안 닫혀요

# 텍스트만
/file-bug [대시보드] 등록 클리닉 수가 실제와 다르게 노출

# 여러 건 한번에
/file-bug 1. 모니터링 알림 규칙에서 이메일 버튼 체크 시 미연동 안내 노출 2. 설정 > 알림에서 토글이 반영 안됨

# 환경 정보 포함
/file-bug Chrome에서 AI가이드 대시보드 기간 선택하면 달력이 안 닫힘. 항상 재현. stg_v1.4.0-rc.3
```

---

## 3. 프로세스

```
┌─ Step 1: 입력 분석 (즉시, 질문 없이)
│  ├─ 스크린샷 있으면 → 화면 요소 자동 식별
│  ├─ 텍스트에서 화면명/현상/환경 추출
│  ├─ 여러 이슈 포함 시 → 자동 분리
│  └─ config/project.json에서 프로젝트/버전/JIRA 키 자동 참조
│
├─ Step 2: JIRA 포맷 작성
│  ├─ summary 보정 (원본 → 보정 병기)
│  ├─ description 템플릿 적용
│  ├─ 심각도/우선순위 자동 판단
│  ├─ 부족한 정보는 (확인 필요) 표기
│  └─ 기존 data/bugs/ 중복 검사
│
├─ Step 3: JIRA 중복 검색 (JQL)
│  ├─ 동일 프로젝트 + 컴포넌트 + 최근 60일
│  ├─ 키워드 보완 검색
│  └─ 유사 티켓 발견 시 안내 (신규/리오픈/스킵 추천)
│
├─ Step 4: 팀장에게 등록안 제시 ★ 승인 포인트
│  ├─ 텍스트 리포트 출력
│  ├─ 유사 티켓 정보
│  ├─ 추천 액션 (신규등록/리오픈/스킵)
│  └─ "등록할까요?" 확인 대기
│
└─ Step 5: JIRA 등록 실행
   ├─ 승인된 건만 JIRA 이슈 생성/리오픈
   ├─ 실행 결과 보고 (이슈 키 + URL)
   └─ data/bugs/ JSON 저장
```

---

## 4. 입력 수집 규칙

### 핵심 원칙: 질문하지 말고 바로 작성

- 주어진 정보만으로 **즉시** 리포트를 작성한다
- 부족한 정보는 리포트 내 해당 필드에 `(확인 필요)` 로 표기한다
- 작성 완료 후, 보충이 필요한 항목만 간단히 안내한다
- **절대 사전 질문으로 작성 흐름을 끊지 않는다**

### 자동 참조 소스

| 정보 | 소스 | 폴백 |
|------|------|------|
| 프로젝트명 | `config/project.json` → `name` | 사용자 입력에서 추출 |
| 버전 | `config/project.json` → `version` | 사용자 입력에서 추출 |
| JIRA 프로젝트 키 | `config/project.json` → `jira_project_key` | `(확인 필요)` |
| JIRA base URL | `config/common.json` → `jira.base_url` | 환경 변수 |
| 컴포넌트 | 화면명에서 자동 매핑 | `(확인 필요)` |
| 환경 정보 | 사용자 입력에서 추출 | 기본값: `Windows 11 Chrome` |

### 방식 A: 스크린샷 + 설명

1. 스크린샷에서 화면 요소를 자동 식별
2. 해당 화면/기능이 어떤 페이지인지 파악
3. 스크린샷에서 관찰 가능한 사실만 기술
4. 부족한 정보는 `(확인 필요)` 로 표기

### 방식 B: 텍스트 설명만

```
사용자: [모니터링] 알림 규칙에서 이메일 버튼 체크 시 미연동 안내 노출
→ 즉시 리포트 작성, 부족한 정보는 (확인 필요) 표기
```

### 여러 이슈 분리

하나의 설명에 여러 이슈가 포함되면 이슈를 분리하여 각각 작성한다.

---

## 5. 출력 형식

### 5.1 summary 보정 (필수)

매 이슈 작성 시 아래 형식으로 원본/보정 제목을 반드시 병기한다:

```
**summary 보정:**
- 원본: `{사용자가 전달한 원본 제목}`
- 보정: `{50자 이내로 간결하게 보정한 제목}`
```

JSON의 `summary` 필드에는 보정 제목을 반영한다.

### 5.2 텍스트 리포트 (팀장 확인용)

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
BUG-{PROJECT}-{순번}: {보정된 summary}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**summary 보정:**
- 원본: `{원본}`
- 보정: `{보정}`

**심각도**: {severity} | **우선순위**: {priority}
**컴포넌트**: {component}
**추천 액션**: 신규등록 / 리오픈({기존 티켓 키}) / 스킵

[Test Environment]
■ 플랫폼 정보 : {OS} {브라우저}
■ 빌드 버전 & 서버 : {테스트 일자} {서버 환경} {버전}
■ 계정 : {테스트 계정}
■ 재현율 : {n/n}

[Precondition]

{사전조건}

[Step]

1. {동작 흐름 1}
2. {동작 흐름 2}

[Actual Result]

{실제 발생한 현상}

[Expected Result]

{정상적으로 기대되는 동작 — "~해야 한다" 확정형}

※ 비고: {해당 시에만}

---
유사 티켓: {있으면 키 + summary + status 표시 / 없으면 "없음"}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### 5.3 승인 요청 메시지

```
총 {N}건 버그 리포트를 작성했습니다.

| # | summary | 심각도 | 추천 |
|---|---------|--------|------|
| 1 | [화면명] 현상 요약 | High | 신규등록 |
| 2 | [화면명] 현상 요약 | Medium | 리오픈 (CENSAY-234) |

등록할 건을 선택해주세요. (예: "전부 등록", "1번만", "1번 등록 2번 스킵")
담당자를 지정해주세요. (예: "전부 홍길동", "1번 홍길동 2번 김개발")
```

### 5.4 JSON (data/bugs/ 저장용)

```json
{
  "mode": "file-bug",
  "project": "{PROJECT}",
  "version": "{version}",
  "created_at": "{ISO 8601}",
  "bugs": [
    {
      "bug_id": "BUG-{PROJECT}-{순번}",
      "summary": "[{화면명}] {보정된 현상 요약}",
      "severity": "High",
      "priority": "P2",
      "status": "open",
      "reporter": "QA_Agent",
      "environment": {
        "platform": "{OS} {브라우저}",
        "build": "{서버 환경} {버전}",
        "account": "{테스트 계정}",
        "reproduction_rate": "{n/n}"
      },
      "description": {
        "precondition": ["{사전조건}"],
        "steps": ["{동작 흐름 1}", "{동작 흐름 2}"],
        "expected": "{정상적으로 기대되는 동작}",
        "actual": "{실제 발생한 현상}",
        "frequency": "{재현 빈도}"
      },
      "attachments": [],
      "related_tc": "",
      "related_bugs": [],
      "note": "",
      "jira_fields": {
        "project_key": "{JIRA 프로젝트 키}",
        "issue_type": "Bug",
        "component": "{컴포넌트}",
        "versions": ["{version}"],
        "assignee": ""
      },
      "jira_candidates": [],
      "recommended_action": "create"
    }
  ]
}
```

---

## 6. JIRA 중복 검색

### 6.1 JQL 검색

각 버그 건에 대해 유사 티켓을 검색한다:

```sql
-- Step 1: 같은 프로젝트 + 컴포넌트 + 최근 60일
project = {project_key} AND issuetype = Bug
AND component = "{component}"
AND created >= -60d
ORDER BY created DESC

-- Step 2: 키워드 보완 검색
project = {project_key} AND issuetype = Bug
AND summary ~ "{핵심 키워드}"
```

### 6.2 추천 액션 판단

| 조건 | 추천 액션 |
|------|-----------|
| 유사 티켓 없음 | `create` (신규등록) |
| 유사 티켓 있음 + status = Done/Closed | `reopen` (리오픈) |
| 유사 티켓 있음 + status = Open/In Progress | `skip` (이미 등록됨) |
| 유사 티켓 있음 + similarity = low | `create` (신규등록, 유사건 참고 링크) |

---

## 7. JIRA 등록 실행

### 7.1 신규등록 (create)

```
1. jira_create_issue 호출
   - project_key, summary, description(멀티라인), issue_type=Bug
   - priority, component, versions
   - assignee (팀장이 지정한 경우)
   - **labels는 생성하지 않음** (라벨 자동 매핑 비활성화)
2. 생성된 이슈 키 기록
3. 유사 티켓이 참고용으로 있으면 → 이슈 링크 (relates to)
```

### 7.2 리오픈 (reopen)

```
1. jira_get_transitions로 가능한 transition 조회
2. jira_transition_issue로 Reopen 상태 변경 (comment 파라미터 사용 X)
3. jira_add_comment로 리오픈 코멘트 별도 등록 (멀티라인)
```

### 7.3 description 템플릿

JIRA description은 반드시 **실제 멀티라인**으로 전달한다 (`\n` 이스케이프 금지).

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

### 7.4 실행 결과 보고

```
JIRA 등록 완료:

| # | bug_id | 액션 | JIRA 키 | URL |
|---|--------|------|---------|-----|
| 1 | BUG-SAY-001 | 신규등록 | CENSAY-550 | https://xxx.atlassian.net/browse/CENSAY-550 |
| 2 | BUG-SAY-002 | 리오픈 | CENSAY-234 | https://xxx.atlassian.net/browse/CENSAY-234 |
```

---

## 8. 심각도 판단

| 심각도 | JIRA 매핑 | 기준 | Priority | 예시 |
|--------|-----------|------|----------|------|
| **Highest** | Critical | 서비스 중단, 데이터 손실, 보안 이슈, 핵심 기능 완전 불가 | P1 | 로그인 불가, 데이터 미표시, 결제 오류 |
| **High** | Critical | 주요 기능 동작 불가, 우회 방법 없음, UI 영역 자체 미노출 | P1-P2 | 필터 미작동, 모달 닫히지 않음, API 에러 |
| **Medium** | Major | 기능 동작하지만 비정상, 우회 가능 | P2-P3 | 정렬 오류, 간헐적 로딩 지연, 잘못된 텍스트, 데이터 불일치 |
| **Low** | Minor | UI 깨짐, 오타, 경미한 불편, 일시적 시각 이슈 | P3 | 여백 틀어짐, 오타, 아이콘 미표시, 깜빡임 |

---

## 9. 규칙

### 9.1 작성 규칙
- **질문 금지**: 주어진 정보로 바로 작성, 부족한 건 `(확인 필요)` 표기
- **summary 보정 필수**: 매 이슈마다 원본 → 보정 제목 병기, JSON에는 보정 제목 반영
- summary는 `[화면명] 현상 요약` 형식 (50자 이내)
- Expected Result는 `~해야 한다` 확정형으로 작성
- 재현율은 구체적 수치로 기록 (예: 3/3, 5/5). 모르면 `(확인 필요)` 표기
- 스크린샷 있으면 `attachments`에 경로 포함
- 하나의 설명에 여러 이슈가 포함되면 이슈를 분리하여 각각 작성
- 연관 버그가 있으면 `related_bugs`에 bug_id 연결

### 9.2 JIRA 등록 규칙
- **팀장 승인 없이 JIRA 등록 절대 금지** — 반드시 등록안 제시 후 승인 대기
- description은 **반드시 실제 멀티라인**으로 전달 (`\n` 이스케이프 금지)
- 상태 변경(transition) + 코멘트는 **2단계 분리 실행** (transition_issue의 comment 파라미터 줄바꿈 불가)
- 담당자는 이름으로 통일 (예: `{"assignee": "홍길동"}`)
- **labels는 자동 생성하지 않음** (메모리 규칙: 레이블 절대 제외)
- 등록 실패 시 에러를 결과에 기록하고 팀장에게 보고 (자동 재시도 안 함)
- 등록 후 `data/bugs/` JSON에 `jira_key`와 `jira_url` 필드 추가 저장

### 9.3 중복 방지 규칙
- 기존 `data/bugs/` 파일에서 유사 건 검색 후 안내
- JIRA JQL 검색으로 기존 티켓 중복 확인
- 유사도 높은 기존 티켓이 있으면 반드시 팀장에게 안내 후 판단 위임

### 9.4 기획 확인 필요 건
- 기획/정책 확인이 필요한 건은 `note`에 명시 (JIRA labels 사용 X)

$ARGUMENTS
