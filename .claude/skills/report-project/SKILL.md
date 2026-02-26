# /report-project - Project Reporter

> 프로젝트별 QA 현황을 집계하여 리포트를 생성합니다.

---

## 1. 개요

- **역할**: 프로젝트 QA 진행 현황, TC 실행 결과, 버그 통계를 종합 리포트로 생성
- **호출 시점**: Phase 4 (최종 보고) 또는 팀장 수동 요청
- **출력**: `data/pipeline/{PROJECT}_{version}_report.json` + 마크다운 요약

---

## 2. 실행

```
사용자: /report-project SAY v1.4.0
사용자: SAY 현황 보고해줘
```

---

## 3. 리포트 구성

### 3.1 TC 현황

```json
{
  "tc_summary": {
    "total": 205,
    "by_priority": { "P1": 42, "P2": 118, "P3": 45 },
    "by_status": { "pass": 180, "fail": 8, "not_tested": 17 },
    "pass_rate": "87.8%"
  }
}
```

### 3.2 버그 현황

```json
{
  "bug_summary": {
    "total": 12,
    "by_severity": { "critical": 1, "major": 4, "minor": 5, "trivial": 2 },
    "by_status": { "open": 3, "in_progress": 2, "resolved": 5, "closed": 2 },
    "open_blockers": 1
  }
}
```

### 3.3 자동화 현황

```json
{
  "automation_summary": {
    "automatable": 85,
    "automated": 62,
    "automation_rate": "72.9%",
    "last_run": { "pass": 58, "fail": 4, "date": "2026-02-25" }
  }
}
```

### 3.4 리스크 / 이슈

```json
{
  "risks": [
    {
      "type": "blocker",
      "description": "결제 모듈 API 변경으로 TC 15건 재작성 필요",
      "impact": "일정 2일 지연 예상"
    }
  ]
}
```

---

## 4. 출력 형식

### 4.1 JSON (기계 소비용)
- `data/pipeline/{PROJECT}_{version}_report.json`

### 4.2 마크다운 요약 (사람 소비용)

```markdown
## SAY v1.4.0 QA 현황 리포트

| 구분 | 수치 |
|------|------|
| 전체 TC | 205건 |
| Pass Rate | 87.8% |
| Open Bug | 3건 (Critical 1) |
| 자동화율 | 72.9% |

### 주요 이슈
- 🔴 결제 모듈 API 변경 → TC 15건 재작성 필요
```

---

## 5. 데이터 소스

| 데이터 | 출처 |
|--------|------|
| TC 현황 | `data/tc/` 폴더 내 Excel/JSON 파일 |
| 리뷰 결과 | `data/reviews/` 폴더 내 JSON 파일 |
| 자동화 결과 | GitHub Actions 실행 결과 |
| 버그 현황 | `data/bugs/` 또는 JIRA API (MCP 연동 시) |

---

## 6. 규칙

- 데이터가 없는 섹션은 "데이터 없음" 표시 (빈 값으로 두지 않음)
- Pass Rate는 `(pass / (total - not_tested)) * 100` 으로 산출
- 리포트 생성 시점 타임스탬프 필수 포함
- 이전 리포트 대비 변화량 표시 (있을 경우)
