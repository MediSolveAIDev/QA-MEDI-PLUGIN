# /run-pipeline - Orchestrator

> 에이전트 파이프라인을 관리하고, 에이전트 간 핸드오프/품질 게이트/재작업 루프를 자동 운영합니다.

---

## 1. 개요

- **역할**: 팀장 지시 → 에이전트 자율 협업 조율 → 최종 보고
- **위치**: 모든 에이전트의 상위. 에이전트는 직접 통신하지 않고 Orchestrator 경유
- **원칙**: 팀장은 트리거 1회 + 승인 7개 포인트만 관여

---

## 2. 실행 모드

### 2.1 전체 파이프라인
```
사용자: /run-pipeline
사용자: 새 업무 줄게
```

### 2.2 특정 Phase만
```
사용자: /run-pipeline --phase 1-B    ← TC 작성만
사용자: /run-pipeline --phase 3      ← 자동화만
```

### 2.3 특정 에이전트만
```
사용자: TC 리뷰해줘                   ← Orchestrator가 판단하여 해당 에이전트 호출
```

---

## 3. 파이프라인 흐름

### Phase 0: 입력 수집

1. 팀장 지시 수신 (자유 형식)
2. 부족한 정보 자동 질문:
   - 프로젝트: SAY / BAY / SSO
   - 버전: (예: v1.4.0)
   - 기획서/정책서 링크 (Confluence URL)
   - 대상 기능/화면
3. `config/projects/{project}.json` 자동 참조
4. 진행 계획 수립 → **★ 승인 0: 팀장 확인**

### Phase 1-A: 시나리오 확정

1. `/write-scenario` 호출 → 시나리오 생성
2. `/review-spec` + `/review-qa` **병렬** 호출 → 크로스 체크
3. 리뷰 결과 병합:
   - 둘 다 Pass → **★ 승인 1** 요청
   - 하나라도 Fail → `/write-scenario`에 수정 지시 (최대 3회)
   - 3회 초과 → 팀장 에스컬레이션
4. 승인 1 통과 → Figma 보강 모드
5. `/write-scenario` (Figma 보강) → 팀장 Figma 검수
6. **★ 승인 2: 시나리오 확정**

### Phase 1-B: TC 확정

1. `/write-tc` 호출 → TC 생성
2. `/check-format` 호출 → 양식 검증
   - Fail → `/write-tc`에 수정 지시 (최대 3회)
3. `/review-spec` + `/review-qa` **병렬** 호출 → 내용 크로스 체크
4. 리뷰 결과 병합:
   - 둘 다 Pass → **★ 승인 3** 요청
   - Fail → `/write-tc`에 수정 지시 (최대 3회)
5. **★ 승인 3: TC 확정**

### Phase 3: 자동화

1. `/assess-automation` 호출 → 자동화 가능 여부 판단
2. **★ 승인 4: 자동화 구현 여부 결정**
3. 승인 시 → `/write-test-code` 호출 → 테스트 코드 생성
4. GitHub Actions 실행 → 결과 수신
5. FAIL 발생 시 → `/analyze-fail` 호출 → 원인 분석
6. 실제 버그 발견 시 → **★ 승인 5: FAIL 분석 결과**

### Phase 4: 최종 보고

1. `/report-project` 호출 → 프로젝트 현황 보고
2. 크로스 프로젝트 영향 시 → `/analyze-impact` 호출
3. **★ 승인 6: 크로스 프로젝트 영향도** (해당 시)

---

## 4. 품질 게이트

### 4.1 재작업 루프

```
에이전트 실행 → 검토 에이전트 리뷰 → Pass?
  ├─ Yes → 다음 단계
  └─ No → 피드백 전달 → 재작업 (최대 3회)
              └─ 3회 초과 → 팀장 에스컬레이션
```

### 4.2 리뷰 결과 병합 규칙

| Spec Reviewer | QA Reviewer | 최종 판정 |
|---------------|-------------|-----------|
| Pass | Pass | **Pass** |
| Pass | Feedback | **Feedback** → 수정 후 재리뷰 |
| Feedback | Pass | **Feedback** → 수정 후 재리뷰 |
| Fail | * | **Fail** → 즉시 재작업 |
| * | Fail | **Fail** → 즉시 재작업 |

### 4.3 에스컬레이션 조건

- 재작업 3회 초과
- 리뷰어 간 판정 충돌 (Spec: Pass, QA: Fail 반복)
- 기획서 누락/모호 발견
- 에이전트 실행 오류

---

## 5. 핸드오프 데이터

에이전트 간 데이터는 파일 기반으로 전달:

```
/write-scenario 출력 → data/scenarios/{PROJECT}_{version}_{feature}_scenario.md
    ↓
/review-spec, /review-qa 입력 → 시나리오 파일 경로
    ↓
/review-spec 출력 → data/reviews/{PROJECT}_{version}_{feature}_review-spec.json
/review-qa 출력 → data/reviews/{PROJECT}_{version}_{feature}_review-qa.json
    ↓
/write-tc 입력 → 시나리오 + 리뷰 피드백
    ↓
/write-tc 출력 → data/tc/{PROJECT}_{version}_{feature}_tc.json
```

---

## 6. 상태 추적

파이프라인 상태를 `data/pipeline/` 에 기록:

```json
{
  "project": "SAY",
  "version": "v1.4.0",
  "feature": "AI 가이드 대시보드",
  "started_at": "2026-02-25T10:00:00",
  "current_phase": "1-B",
  "status": "in_progress",
  "approvals": {
    "0_plan": "approved",
    "1_scenario_review": "approved",
    "2_scenario_final": "approved",
    "3_tc_final": "pending",
    "4_automation": null,
    "5_fail_analysis": null,
    "6_cross_project": null
  },
  "rework_count": { "write-scenario": 1, "write-tc": 0 },
  "agents_log": []
}
```

---

## 7. Slack 알림

승인 포인트 도달 시:
- QA_Agent Slack Bot → 팀장 DM 발송
- 메시지 형식: `[{project} {version}] ★ 승인 {N}: {내용} - 확인 부탁드립니다.`
