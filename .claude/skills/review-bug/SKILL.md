---
name: review-bug
description: 버그 리포트(Phase A 산출물)의 정합성·품질을 검증합니다. bug JSON 파일 경로를 전달하세요.
argument-hint: [bug JSON 파일 경로]
---

# /review-bug - Bug Reviewer

> 버그 리포트(report-bug Phase A 산출물)의 품질과 정합성을 검증하는 리뷰 에이전트.
> 시나리오의 `/review-spec` + `/review-qa`와 동일한 패턴으로, 버그 등록 전 최종 품질 게이트 역할을 한다.

> **본 스킬은 `.claude/rules/tc_writing_rule.md` 규칙을 따른다.**
> 버그 본문은 비즈니스 용어만 (DB 컬럼명·상태 코드·HTTP 코드는 별도 필드).
> 관련 TC ID(`<도메인>-<L2약어>-<NNN>` 형식) 인용 여부 확인.
>
> **호출 주체**: Orchestrator (Phase Bug 또는 Phase 3 FAIL 처리 시 자동 호출)

---

## 1. 개요

- **역할**: report-bug Phase A 산출물(bug JSON)의 필드 완성도, 내용 정합성, 중복 판단 타당성 검증
- **입력**: `data/bugs/{PROJECT}_{version}_{feature}_bug.json` (Phase A 보고서)
- **출력**: `data/reviews/{PROJECT}_{version}_{feature}_review-bug.json`
- **verdict**: PASS / FAIL (FAIL 시 항목별 피드백 → report-bug 재작업)

---

## 2. 실행

```
# Orchestrator에서 자동 호출
/review-bug data/bugs/SAY_v1.4.0_대시보드_bug.json

# 팀장 직접 호출 (독립)
/review-bug data/bugs/SAY_v1.4.0_대시보드_bug.json
```

---

## 3. 검증 항목

### 3.1 필수 필드 완성도

| # | 검증 항목 | 규칙 | 심각도 |
|---|-----------|------|--------|
| F1 | summary | 비어있으면 FAIL | ERROR |
| F2 | summary 형식 | `[화면명] 현상 요약` 형식이 아니면 FAIL | ERROR |
| F3 | summary 길이 | 50자 초과 시 WARN | WARN |
| F4 | description | 비어있으면 FAIL | ERROR |
| F5 | description 템플릿 | `[Test Environment]`, `[Step]`, `[Actual Result]`, `[Expected Result]` 섹션 누락 시 FAIL | ERROR |
| F6 | priority | 비어있으면 FAIL | ERROR |
| F7 | component | 비어있으면 FAIL | ERROR |
| F8 | versions | 비어있으면 FAIL (영향 버전 필수) | ERROR |
| F9 | assignee | 비어있으면 WARN (팀장 수동 지정 대상이므로) | WARN |
| F11 | project_key | 비어있으면 FAIL | ERROR |
| F12 | issue_type | "Bug"이 아니면 FAIL | ERROR |

### 3.2 내용 정합성

| # | 검증 항목 | 규칙 | 심각도 |
|---|-----------|------|--------|
| C1 | 심각도 ↔ 현상 정합성 | Critical인데 UI 오타/경미한 불편이면 불일치 | ERROR |
| C2 | 심각도 ↔ 현상 정합성 | Trivial인데 데이터 손실/서비스 중단이면 불일치 | ERROR |
| C3 | Step 재현 경로 | 번호 매기기 + 구체적 동작 기술 여부 (1줄 이하면 WARN) | WARN |
| C4 | Actual vs Expected | 둘 다 동일한 내용이면 FAIL (기대 결과와 실제 결과가 같으면 버그가 아님) | ERROR |
| C5 | 환경 정보 | browser, OS, server 중 하나라도 비어있으면 WARN | WARN |
| C6 | 재현 빈도 | frequency 미기재 시 WARN | WARN |

### 3.3 중복 판단 타당성

| # | 검증 항목 | 규칙 | 심각도 |
|---|-----------|------|--------|
| D1 | 신규등록 추천 건 | jira_candidates가 있는데 similarity="high"인 후보를 무시하고 신규등록 추천이면 WARN | WARN |
| D2 | 리오픈 추천 건 | target_key의 status가 Done/Closed가 아니면 리오픈 대상이 아닐 수 있음 | WARN |
| D3 | 스킵 추천 건 | 스킵 사유가 불충분하면 (사유 문자열 10자 미만) WARN | WARN |
| D4 | 유사도 근거 | similarity="high"인데 summary 키워드 겹침이 없으면 WARN | WARN |

### 3.4 JIRA 필드 매핑 검증

| # | 검증 항목 | 규칙 | 심각도 |
|---|-----------|------|--------|
| J1 | versions 형식 | 배열이 아니거나, `v` 접두사 없으면 WARN | WARN |
| J2 | component ↔ 시트 | 시트의 컴포넌트와 bug JSON의 component 일치 여부 | WARN |
| J3 | labels 미생성 | labels 필드가 있으면 WARN (메모리 규칙: 레이블 절대 제외) | WARN |

---

## 4. 출력 형식

```json
{
  "review_type": "review-bug",
  "source": "data/bugs/SAY_v1.4.0_대시보드_bug.json",
  "reviewed_at": "2026-03-26T14:00:00",
  "verdict": "FAIL",
  "summary": {
    "total_bugs": 3,
    "error_count": 2,
    "warn_count": 4,
    "pass_count": 1
  },
  "bugs": [
    {
      "bug_id": "BUG-SAY-001",
      "verdict": "FAIL",
      "issues": [
        {
          "rule": "F5",
          "severity": "ERROR",
          "field": "description",
          "message": "[Expected Result] 섹션이 누락되었습니다.",
          "suggestion": "기대 결과를 명시해주세요. 예: '모달 자동 닫힘, 대시보드 데이터 갱신'"
        },
        {
          "rule": "C1",
          "severity": "ERROR",
          "field": "priority",
          "message": "Critical로 설정되었지만 현상이 'UI 텍스트 오타'입니다. 심각도가 과대평가되었습니다.",
          "suggestion": "Minor 또는 Trivial로 변경을 권장합니다."
        },
        {
          "rule": "F9",
          "severity": "WARN",
          "field": "assignee",
          "message": "담당자가 지정되지 않았습니다.",
          "suggestion": "팀장이 건별로 직접 지정 예정"
        }
      ]
    },
    {
      "bug_id": "BUG-SAY-002",
      "verdict": "PASS",
      "issues": []
    },
    {
      "bug_id": "BUG-SAY-003",
      "verdict": "FAIL",
      "issues": [
        {
          "rule": "D1",
          "severity": "WARN",
          "field": "jira_candidates",
          "message": "similarity='high'인 후보 CENSAY-301이 있지만 신규등록으로 추천되었습니다.",
          "suggestion": "리오픈 또는 링크 등록을 재검토해주세요."
        }
      ]
    }
  ]
}
```

---

## 5. 판정 규칙

### 5.1 개별 버그 판정
- **ERROR 1건 이상** → 해당 버그 `verdict: "FAIL"`
- **WARN만** → 해당 버그 `verdict: "PASS"` (경고는 참고용)

### 5.2 전체 판정
- **FAIL 버그 1건 이상** → 전체 `verdict: "FAIL"` → report-bug 재작업 트리거
- **모든 버그 PASS** → 전체 `verdict: "PASS"` → Orchestrator가 팀장에게 등록안 제시

### 5.3 재작업 시 피드백 전달
- FAIL 판정 시, `issues` 배열을 report-bug에 피드백으로 전달
- report-bug는 피드백을 반영하여 해당 버그만 수정 (전체 재생성 아님)
- 재작업 후 다시 review-bug 호출 (최대 3회)

---

## 6. Orchestrator 연계

### 6.1 파이프라인 내 호출 (Phase 3 / Phase Bug)

```
report-bug Phase A (수집) → review-bug (검증) → [PASS] → 팀장 승인 → Phase B (실행)
                                              → [FAIL] → report-bug 재작업 → review-bug 재검증
                                                         (최대 3회, 초과 시 에스컬레이션)
```

### 6.2 독립 호출

팀장이 직접 `/review-bug` 호출 시에도 동일 검증 수행. 결과를 대화로 보고.

---

## 7. 금지사항

- 검증 없이 PASS 판정 금지 (모든 항목 순회 필수)
- 버그 내용을 직접 수정하지 않음 (피드백만 제공, 수정은 report-bug가 수행)
- WARN만 있는 건을 FAIL로 판정 금지 (ERROR 기준 엄수)
- 검증 항목 추가/삭제는 이 SKILL.md 수정을 통해서만 가능
