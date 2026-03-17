# /learn-rules - Rule Learner

> 리뷰 피드백을 분석하여 **다른 기능/화면에도 적용 가능한 패턴**을 즉시 규칙으로 등록합니다.
> 반복을 기다리지 않고, 일반화 가능성이 있으면 1회 발생으로도 규칙을 생성합니다.

---

## 1. 개요

- **역할**: 리뷰 피드백에서 일반화 가능한 패턴을 추출 → 규칙으로 저장 → 이후 리뷰/TC 작성 시 자동 참조
- **핵심 원칙**: **선제 대응** — 같은 실수가 다른 기능에서 반복되기 전에 규칙으로 차단
- **호출 시점**: 리뷰 완료 직후 (Orchestrator 호출) 또는 수동 요청
- **출력**: `data/rules/rule_{id}.json`

---

## 2. 실행

```
사용자: /learn-rules                              ← 최근 리뷰 결과에서 규칙 추출
사용자: /learn-rules list                          ← 현재 active 규칙 목록
사용자: /learn-rules disable RULE-001              ← 규칙 비활성화
사용자: /learn-rules add "모달에서 ESC 키 동작 TC 필수"  ← 수동 규칙 추가
사용자: /learn-rules review RULE-001               ← 특정 규칙 상세 확인
```

---

## 3. 학습 소스

| 소스 | 경로 | 학습 대상 |
|------|------|-----------|
| Spec Reviewer 결과 | `data/reviews/*_review-spec.json` | 기획서 대비 누락 패턴 |
| QA Reviewer 결과 | `data/reviews/*_review-qa.json` | 엣지케이스/네거티브 패턴 |
| TC Reviewer 결과 | `data/reviews/*_review-tc.json` | TC 내용 빈틈 패턴 |
| Format Checker 결과 | `data/reviews/*_format.json` | 양식 위반 패턴 |
| 팀장 수동 입력 | `/learn-rules add "..."` | 경험 기반 규칙 |

---

## 4. 규칙 형식

```json
{
  "rule_id": "RULE-001",
  "source": "qa_review",
  "source_file": "data/reviews/SAY_v1.4_로그인_review-qa.json",
  "category": "edge_case",
  "pattern": "모달 있는 화면에서 ESC 키 닫기 동작 TC 누락",
  "generalization": "모달/팝업/다이얼로그가 있는 모든 화면",
  "recommendation": "모달 있는 화면에서 ESC 키 닫기, 배경 클릭 닫기, X 버튼 닫기 TC 필수 추가",
  "projects": ["SAY", "BAY", "SSO"],
  "auto_apply": true,
  "severity": "높음",
  "status": "active",
  "created_at": "2026-03-17",
  "created_from": "SAY 로그인 리뷰에서 모달 ESC 미동작 피드백"
}
```

### 필드 설명

| 필드 | 설명 |
|------|------|
| `source` | 규칙 출처 (`spec_review`, `qa_review`, `tc_review`, `format_check`, `manual`) |
| `source_file` | 원본 리뷰 파일 경로 (추적용) |
| `category` | 규칙 분류 (아래 카테고리 표 참조) |
| `pattern` | 원래 피드백 내용 (구체적 사례) |
| `generalization` | 이 규칙이 적용되는 일반적 조건 |
| `recommendation` | 조치 사항 (TC 추가 제안 또는 체크 항목) |
| `projects` | 적용 대상 프로젝트 (`["SAY", "BAY", "SSO"]` = 전체) |
| `auto_apply` | `true`: `/write-tc`에서 자동 반영 / `false`: 리뷰 체크리스트에만 추가 |
| `severity` | `높음` / `중간` / `낮음` |
| `status` | `active` / `inactive` |

### 카테고리

| 카테고리 | 설명 | 소비 스킬 |
|----------|------|-----------|
| `coverage` | 기획서 대비 누락 패턴 | `/review-spec` |
| `business_logic` | 비즈니스 로직 검증 패턴 | `/review-spec` |
| `spec_gap` | 기획서 모호/누락 패턴 | `/review-spec` |
| `edge_case` | 엣지케이스 패턴 | `/review-qa` |
| `negative` | 네거티브 시나리오 패턴 | `/review-qa` |
| `boundary` | 경계값 패턴 | `/review-qa` |
| `ux_risk` | UX 리스크 패턴 | `/review-qa` |
| `format` | 양식 위반 패턴 | `/check-format` |

---

## 5. 학습 프로세스 (일반화 기반)

### 5.1 리뷰 완료 직후 자동 분석

리뷰 결과 JSON에서 FAIL 항목을 추출한 뒤, 각 피드백에 대해 아래 판단을 수행한다.

```
피드백 1건 발생
  ↓
Q1: 이 피드백이 특정 기능에만 해당하는가?
  → YES: 규칙 생성 안 함 (해당 기능 고유 이슈)
  → NO: Q2로
  ↓
Q2: 다른 기능/화면에도 동일 패턴이 존재할 수 있는가?
  → YES: 규칙 생성 (일반화)
  → NO: 규칙 생성 안 함
```

### 5.2 일반화 판단 기준

| 기준 | 규칙 생성 O | 규칙 생성 X |
|------|:-----------:|:-----------:|
| **UI 패턴** | "모달에서 ESC" → 모달이 있는 모든 화면 | "로그인 비밀번호 마스킹" → 로그인만 해당 |
| **사용자 행동** | "뒤로가기 시 데이터 유실" → 입력 폼이 있는 모든 화면 | "특정 API 타임아웃" → 해당 API만 해당 |
| **데이터 검증** | "빈 값 입력 시 에러 처리" → 입력 필드 있는 모든 화면 | "주민번호 형식 검증" → 주민번호 필드만 해당 |
| **상태 전환** | "비활성 버튼 클릭 시 동작" → 비활성 상태 버튼이 있는 모든 화면 | "결제 완료 후 상태" → 결제 기능만 해당 |

### 5.3 규칙 생성

1. `pattern`: 원래 피드백 그대로 기록
2. `generalization`: 어떤 조건의 화면/기능에 적용되는지 일반화
3. `projects`: 일반화 가능하면 전체 프로젝트(`["SAY", "BAY", "SSO"]`), 특정 프로젝트만 해당하면 해당 프로젝트만
4. `auto_apply`: 일반화 확신 높으면 `true`, 애매하면 `false` (리뷰 체크만)
5. 기존 규칙과 중복 확인 → 중복이면 생성하지 않고 기존 규칙의 `source_file`에 추가 사례만 기록

---

## 6. 규칙 라이프사이클

### 6.1 상태 전환

```
생성 (active) → 비활성화 (inactive)
                    ↑
            팀장 수동 비활성화
            또는 오탐 3회 이상
```

- **생성**: 리뷰 분석 또는 수동 추가 시 `active`로 생성
- **비활성화**: 팀장이 `/learn-rules disable RULE-001` 또는 오탐(해당 안 되는데 체크됨) 3회 이상
- **삭제 금지**: 규칙은 삭제하지 않고 `inactive`로 변경 (이력 보존)

### 6.2 오탐 관리

리뷰 스킬에서 규칙 기반 체크를 수행했는데 실제로는 해당 안 되는 경우:
- 해당 규칙의 `false_positive_count` +1
- 3회 이상 → 팀장에게 "이 규칙 비활성화할까요?" 보고
- 팀장 판단 후 `inactive` 또는 `generalization` 조건 수정

---

## 7. 수동 규칙 추가 (`/learn-rules add`)

```
사용자: /learn-rules add "달력 UI에서 브라우저 뒤로가기 TC 필수"
```

처리 절차:
1. 입력 문구를 `pattern`으로 저장
2. 일반화 조건 자동 추론 → 사용자에게 확인
3. `source: "manual"`, `auto_apply: true`로 기본 설정
4. `data/rules/rule_{다음번호}.json`에 저장
5. 저장 결과 요약 출력

---

## 8. 리뷰 에이전트 연동

### 소비 스킬별 규칙 참조 방식

| 소비 스킬 | 참조 카테고리 | 적용 방식 |
|-----------|---------------|-----------|
| `/review-spec` | `coverage`, `business_logic`, `spec_gap` | 리뷰 체크리스트에 추가 |
| `/review-qa` | `edge_case`, `negative`, `boundary`, `ux_risk` | 리뷰 체크리스트에 추가 |
| `/review-tc` | 전체 카테고리 | 리뷰 체크리스트에 추가 |
| `/write-tc` | `auto_apply: true`인 규칙만 | TC 사전 작성에 반영 |

### 연동 규칙

- 각 소비 스킬은 리뷰/작성 시작 전 `data/rules/` 스캔 (0절에 명시됨)
- `projects` 필드에 현재 프로젝트가 포함된 규칙만 적용
- 규칙이 없으면 기존 체크리스트만으로 동작 (규칙 의존성 없음)
- 규칙 기반 피드백은 출력에 `(규칙: RULE-XXX)` 태그 표시 → 추적 가능

---

## 9. 규칙 ID 채번

- 형식: `RULE-{3자리 순번}` (예: RULE-001, RULE-002)
- `data/rules/` 폴더의 기존 파일 스캔하여 마지막 번호 + 1
- 파일명: `rule_001.json`, `rule_002.json`
