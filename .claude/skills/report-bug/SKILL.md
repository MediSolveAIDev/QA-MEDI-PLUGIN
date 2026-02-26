# /report-bug - Bug Reporter

> **⚠️ 현재 비활성화 상태입니다. 이 스킬은 아직 운영에 투입되지 않았습니다.**
> 활성화 시점: JIRA API 연동 완료 후 팀장 승인 시

> 발견된 버그를 정형화하여 JIRA 이슈 생성용 리포트를 작성합니다.

---

## 1. 개요

- **역할**: 테스트 중 발견된 버그를 JIRA 이슈 형식으로 정리
- **호출 시점**: 수동 테스트 중 버그 발견 시, 또는 `/analyze-fail`에서 실제 버그 판정 시
- **출력**: `data/bugs/{PROJECT}_{version}_{feature}_bug.json`

---

## 2. 실행

```
사용자: /report-bug SAY
사용자: 버그 리포트 작성해줘
```

---

## 3. 입력 수집

대화형으로 아래 정보 수집:

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

---

## 4. 출력 형식

### 4.1 JSON

```json
{
  "bug_id": "BUG-SAY-001",
  "project": "SAY",
  "version": "v1.4.0",
  "summary": "[AI 가이드 대시보드] 기간 선택 시 달력 모달이 닫히지 않음",
  "severity": "major",
  "priority": "P2",
  "status": "open",
  "reporter": "QA_Agent",
  "environment": {
    "browser": "Chrome 122",
    "os": "Windows 11",
    "server": "dev-say.example.com"
  },
  "description": {
    "steps": [
      "1. AI 가이드 대시보드 진입",
      "2. 기간 선택 필드 Tap",
      "3. 시작일 선택",
      "4. 종료일 선택"
    ],
    "expected": "모달 자동 닫힘, 대시보드 데이터 갱신",
    "actual": "모달이 닫히지 않고 유지됨, 데이터 미갱신",
    "frequency": "항상 재현"
  },
  "attachments": [],
  "related_tc": "Row 65",
  "created_at": "2026-02-25T14:30:00",
  "jira_fields": {
    "project_key": "CENSAY",
    "issue_type": "Bug",
    "labels": ["QA-Agent", "v1.4.0"]
  }
}
```

### 4.2 JIRA 연동 (향후)

- `jira_fields`를 기반으로 JIRA API 호출하여 이슈 자동 생성
- 생성된 이슈 키(예: CENSAY-123)를 JSON에 기록
- TC의 BTS ID 컬럼에 자동 매핑

---

## 5. 심각도 기준

| 심각도 | 기준 | Priority 매핑 |
|--------|------|---------------|
| Critical | 서비스 중단, 데이터 손실, 보안 이슈 | P1 |
| Major | 핵심 기능 동작 불가, 우회 방법 없음 | P1-P2 |
| Minor | 기능 동작하지만 비정상, 우회 가능 | P2-P3 |
| Trivial | UI 깨짐, 오타, 경미한 불편 | P3 |

---

## 6. 규칙

- summary는 `[화면명] 현상 요약` 형식 (50자 이내)
- 재현 경로는 번호 매기기 필수 (1, 2, 3...)
- 스크린샷 있으면 `attachments`에 경로 포함
- 동일 버그 중복 등록 방지: 기존 `data/bugs/` 파일 검색 후 유사 건 안내
- `/analyze-fail`에서 자동 호출 시 TC 행 번호 자동 매핑
