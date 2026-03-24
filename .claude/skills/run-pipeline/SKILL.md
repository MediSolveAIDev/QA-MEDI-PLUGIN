# /run-pipeline - Orchestrator

> Claude Code가 직접 파이프라인을 운영한다. Skill 도구로 각 스킬을 호출하고, JSON으로 상태를 관리한다.
>
> **자연어 트리거**: 아래 패턴이 감지되면 이 스킬을 즉시 실행한다.
> - "새 업무 줄게", "새 업무", "업무 줄게", "일 줄게"
> - "파이프라인 실행", "파이프라인 시작", "파이프라인 돌려"
> - "{프로젝트명} 처리해", "{프로젝트명} 시작해"
> - "시나리오부터 해줘", "전체 진행해줘"
> - "이어서 해줘", "재개해줘", "이어서 진행"
> - "기획서 업데이트됐어", "기획 변경됐어"
> - "진행 상황", "어디까지 했어", "상태 알려줘", "지금 뭐 하고 있어"
> - "시나리오 확정", "시나리오 승인" → 현재 Phase 확인 → 해당 승인 처리 + 다음 Phase 자동 진행
> - "TC 확정", "TC 승인" → 현재 Phase 확인 → 해당 승인 처리 + 다음 Phase 자동 진행
>
> **중요**: 위 패턴 감지 시 사용자에게 "어떤 작업을 할까요?" 같은 선택지를 제시하지 않는다. 부족한 정보만 질문한 뒤 바로 파이프라인을 실행한다.

---

## 1. 개요

- **역할**: 팀장 지시 → Skill 도구로 각 스킬 호출 → 상태 JSON 관리 → 승인 포인트에서 대기
- **구현**: Claude Code 대화 기반 + `orchestrator/cli_state.py` (상태 관리 CLI)
- **원칙**: 팀장은 트리거 1회 + 승인 7개 포인트만 관여. 나머지는 자동 진행.

---

## 2. 상태 관리 CLI

파이프라인 상태는 `data/pipeline/{PROJECT}_{ver}_pipeline.json`에 저장한다.
아래 명령을 Bash로 호출하여 상태를 관리한다:

```bash
# 신규 파이프라인 생성
python -m orchestrator.cli_state init SAY v1.4.0 "로그인" "PAGE_ID"

# 상태 조회
python -m orchestrator.cli_state status latest
python -m orchestrator.cli_state status SAY_v1.4.0

# 상태 업데이트
python -m orchestrator.cli_state update SAY_v1.4.0 phase "1-A"
python -m orchestrator.cli_state update SAY_v1.4.0 status "in_progress"
python -m orchestrator.cli_state update SAY_v1.4.0 approval.1_scenario_review "approved"
python -m orchestrator.cli_state update SAY_v1.4.0 artifact.scenario "/path/to/file.json"
python -m orchestrator.cli_state update SAY_v1.4.0 upload.scenario_confluence "https://..."

# 파이프라인 목록
python -m orchestrator.cli_state list
```

---

## 3. 실행 절차

### 3.1 파이프라인 시작

사용자가 업무를 요청하면:

1. 부족한 정보 질문 (프로젝트, 버전, 기능명, 기획서 URL)
2. `config/project.json`에서 프로젝트 정보 자동 참조
3. `python -m orchestrator.cli_state init {프로젝트} {버전} {기능} {기획서URL}` 실행
4. Phase 0부터 순차 진행

### 3.2 파이프라인 재개

"이어서 해줘" 또는 새 세션에서:

1. `python -m orchestrator.cli_state status latest` 로 마지막 상태 확인
2. `current_phase`부터 이어서 진행

### 3.3 진행 상황 확인

"어디까지 했어", "진행 상황" 등:

1. `python -m orchestrator.cli_state status latest` 실행
2. 결과를 읽기 쉽게 요약하여 보여줌

---

## 4. Phase 실행 규칙

**핵심 규칙: 승인 포인트가 아닌 단계에서는 사용자에게 묻지 않고 자동 진행한다.**

### Phase 0: 입력 수집 + 계획 확인

1. 정보 수집 (프로젝트/버전/기획서) — 이미 수집된 상태
2. 진행 계획 보고
3. **★ 승인 0 (수동)**: 사용자에게 계획 확인 요청 → 승인 대기
4. 승인 즉시 실행 (중단 금지):
   - `update {ID} approval.0_plan approved`
   - `update {ID} phase "1-A"`
   - Phase 1-A 시작

### Phase 1-A: 시나리오 확정

1. `update {ID} phase "1-A"`
2. Skill `/write-scenario` 호출 (기획서 URL 전달)
3. 산출물 경로 저장: `update {ID} artifact.scenario {파일경로}`
4. Skill `/review-spec` 호출 (시나리오 파일 전달)
5. Skill `/review-qa` 호출 (시나리오 파일 전달)
6. 리뷰 결과 확인:
   - **PASS**: 7단계로
   - **FAIL**: Skill `/write-scenario` 재호출 (피드백 반영), `update {ID} rework write-scenario` → 4단계 반복 (최대 3회)
   - **3회 초과**: 사용자에게 에스컬레이션 보고 → 중단
7. 리뷰 산출물 저장: `update {ID} artifact.scenario_review_spec {경로}`, `artifact.scenario_review_qa {경로}`
8. Skill `/learn-rules` 호출 (리뷰 산출물 전달 → 일반화 가능한 패턴 자동 추출 → `data/rules/`에 저장)
9. **★ 승인 1 (수동)**: 사용자에게 리뷰 결과 확인 요청
10. 승인 즉시 실행 (중단 금지):
    - `update {ID} approval.1_scenario_review approved`
    - 사용자에게 안내: "Figma 보강이 필요하면 `/enrich-figma`로 진행해주세요. 시나리오 확정 시 승인해주세요."
    - **Figma 보강은 팀장 판단** (수동 — `/enrich-figma` 직접 호출)
    - 파이프라인은 승인 2를 대기
11. **★ 승인 2 (수동)**: 사용자에게 시나리오 확정 요청 (Figma 보강 여부 무관하게 최종 확정)
11. 승인 즉시 실행 (중단 금지):
    - `update {ID} approval.2_scenario_final approved`
    - Confluence 업로드 (Bash로 Python 유틸 호출)
    - `update {ID} phase "1-B"`
    - Phase 1-B 시작

### Phase 1-B: TC 확정

1. `update {ID} phase "1-B"`
2. Skill `/write-tc` 호출 (확정 시나리오 파일 전달)
   - **write-tc 내부에서 자체 리뷰 루프 2회 이상 수행** (check-format + review-tc + review-qa)
   - 양식 위반은 자동 수정, 내용 수정 제안은 목록으로 반환
   - `review_history`에 리뷰 이력 기록됨
3. 산출물 경로 저장: `update {ID} artifact.tc {파일경로}`
4. write-tc가 반환한 내용 수정 제안을 사용자에게 보고
   - 승인된 항목 반영 → TC 최종 확정
5. Skill `/learn-rules` 호출 (write-tc 내부 리뷰 결과(`review_history`) 전달 → 일반화 가능한 패턴 추출 → `data/rules/`에 저장)
   - 승인된 항목 반영 → TC 최종 확정
5. **★ 승인 3 (수동)**: 사용자에게 TC 확정 요청
9. 승인 즉시 실행 (중단 금지):
   - `update {ID} approval.3_tc_final approved`
   - Google Sheet 업로드 (Bash로 Python 유틸 호출)
   - `update {ID} phase "3"`
   - Phase 3 시작

### Phase 3: 자동화

1. `update {ID} phase "3"`
2. Skill `/assess-automation` 호출
3. **★ 승인 4 (수동)**: 자동화 구현 여부 결정
   - 거부 시: `update {ID} phase "4"` → Phase 4로 건너뜀
4. 승인 즉시 실행 (중단 금지):
   - `update {ID} approval.4_automation approved`
   - Skill `/write-test-code` 호출
   - 사용자에게 안내: "GitHub Actions에서 테스트를 실행하고 결과를 알려주세요."
5. 테스트 결과 확인 후:
   - **★ 승인 5 (자동)**: FAIL 없으면 자동 통과 → 7단계로
   - FAIL 있으면: 6단계로
6. **FAIL 처리 (analyze-fail → report-bug 2-Phase 플로우)**:
   - ① Skill `/analyze-fail` 호출 → Fail 분류 (코드 이슈/실제 버그/환경 이슈/TC 오류)
   - ② 실제 버그 있으면:
     - Skill `/report-bug` Phase A 호출 (수집 모드: JIRA 후보 검색 + 이력 수집)
     - Orchestrator가 보고서 분석 → 중복/리오픈/신규 추천안 작성
     - 사용자에게 요약 + 추천안 제시 → **사용자 선별 대기**
     - 사용자 방향 제시 후 → 실행 지시서 생성
     - Skill `/report-bug` Phase B 호출 (실행 모드: JIRA 생성/리오픈/수정/링크)
     - 실행 결과 요약 보고 + Google Sheet BTS ID 매핑
   - ③ 코드 이슈 (auto_fixable): 사용자에게 자동 수정 승인 요청 → 승인 시 `/write-test-code` 재호출
   - ④ 환경 이슈: 사용자에게 재실행 또는 무시 결정 요청
   - ⑤ TC 오류: TC 수정 필요 건 목록 → 사용자 확인 후 `/write-tc` 재작업
7. `update {ID} phase "4"` → Phase 4 시작

### Phase 4: 최종 보고

1. `update {ID} phase "4"`
2. Skill `/report-project` 호출
3. 크로스 프로젝트 해당 시: Skill `/analyze-impact` 호출
   - **★ 승인 6 (수동)**: 영향도 확인 (해당 시에만)
4. `update {ID} status "completed"`
5. 파이프라인 완료 요약 출력

---

## 5. 승인 규칙

| # | 승인 포인트 | Phase | 모드 | 설명 |
|---|------------|-------|------|------|
| 0 | 진행 계획 확인 | 0 | 수동 | 계획 보고 → 확인 후 실행 |
| 1 | 시나리오 리뷰 Pass | 1-A | 수동 | 리뷰 루프 통과 후 결과 확인 |
| 2 | 시나리오 확정 | 1-A | 수동 | Figma 보강 후 팀장 직접 검수 |
| 3 | TC 확정 | 1-B | 수동 | 포맷 검증 + 리뷰 루프 통과 후 확정 |
| 4 | 자동화 구현 여부 | 3 | 수동 | 자동화 검토 후 진행/거부 결정 |
| 5 | FAIL 분석 결과 | 3 | 자동 | FAIL 없으면 자동 통과, FAIL 있으면 사용자에게 보고 |
| 6 | 크로스 프로젝트 영향도 | 4 | 수동 | 해당 시에만 |

**수동 승인 시 사용자 응답 처리:**
- "승인", "ㅇㅇ", "확인" → approved → 다음 단계
- "재작업", "수정해" → rework → 해당 단계 재실행
- "거부", "중단" → rejected → 파이프라인 중단, 상태 저장

**자동 승인 (5번):**
- FAIL 없으면 자동 통과, FAIL 있으면 사용자에게 결과 보고 후 다음 단계 진행

---

## 6. 리뷰 루프 규칙

1. `/review-spec`과 `/review-qa`를 호출하여 리뷰 결과 확인
2. 리뷰 결과 JSON에서 `verdict` 필드 확인 (PASS/FAIL)
3. FAIL 시:
   - 피드백 내용을 writer 스킬에 전달하여 재작업
   - `update {ID} rework {스킬명}` 으로 재작업 횟수 기록
   - 재작업 산출물로 다시 리뷰 (최대 3회)
4. 3회 초과 시:
   - 사용자에게 에스컬레이션 보고
   - `update {ID} status "escalated"`

---

## 7. 기획서 변경 대응

"기획서 업데이트됐어" 감지 시:

1. `python -m orchestrator.cli_state status latest` 로 현재 상태 확인
2. Skill `/write-scenario` 호출 (변경 분석 모드 — SKILL.md 2절)
   - 변경이력 파싱 → Confluence에서 해당 섹션 조회 → 기존 시나리오와 비교
   - 변경사항 diff 출력 (추가/수정/삭제 + 영향받는 TC 목록)
3. 변경 분석 결과 + 현재 Phase 기반으로 재작업 범위 결정:
   - **1-A (승인 1 이전)**: 시나리오 수정 → 리뷰 루프 재진행 → 승인 1
   - **1-A (승인 1 통과 ~ 승인 2 이전)**: 시나리오 수정 → 리뷰 루프 재진행 (승인 1부터 다시) → Pass 후 Figma 보강 → 승인 2
   - **1-B 진행 중/완료**: 시나리오 수정 → 시나리오 리뷰 루프 → 영향받는 TC 재작업 → TC 리뷰 루프
   - **3 이후**: 시나리오 → TC → 테스트코드 순차 재작업 (각 단계마다 리뷰 루프 포함)
4. 재작업 범위를 사용자에게 보고 후 진행
5. **원칙: 시나리오/TC가 수정되면 반드시 리뷰 루프를 재진행한다. 리뷰 없이 승인 단계로 넘어가지 않는다.**

---

## 8. Slack 알림 규칙 (필수)

**Orchestrator가 팀장에게 보고하는 모든 시점에서 Slack 알림을 발송한다.**

### 8.1 알림 발송 시점

아래 시점마다 반드시 `python -m orchestrator.cli_state notify {파이프라인ID} {타입} {메시지}` 를 호출한다:

| 시점 | 타입 | 메시지 예시 |
|------|------|------------|
| 승인 요청 (수동 승인 6개) | `approval` | `0_plan\|진행 계획 확인이 필요합니다.` |
| 에스컬레이션 (리뷰 3회 초과) | `approval` | `escalation\|write-scenario 리뷰 3회 초과. 팀장 확인 필요.` |
| 완료된 산출물 수정 발생 | `approval` | `escalation\|시나리오 수정됨 — 리뷰 재진행 후 재확인 필요.` |
| Phase 완료 | `progress` | `Phase 1-A 완료. 시나리오 확정됨.` |
| FAIL 분석 결과 보고 | `progress` | `테스트 3건 FAIL — 실제 버그 1건, 코드 이슈 2건` |
| 기획서 변경 감지 → 재작업 시작 | `progress` | `기획서 변경 감지. 시나리오 재작업 시작.` |

### 8.2 재확인 알림 (핵심)

**이미 완료/승인된 단계의 산출물이 수정되면 반드시 알림을 발송한다:**

- 승인 완료된 시나리오가 수정됨 → `approval` 타입으로 "시나리오 수정 발생 — 리뷰 재진행 중. 완료 후 재확인 요청 예정." 알림
- 승인 완료된 TC가 수정됨 → `approval` 타입으로 "TC 수정 발생 — 리뷰 재진행 중. 완료 후 재확인 요청 예정." 알림
- 리뷰 재진행 완료 시 → 해당 승인 포인트 알림 재발송 (승인 1/2/3)

### 8.3 설정

Slack webhook은 아래 순서로 탐색한다:
1. `.env`의 `SLACK_WEBHOOK_APPROVAL` (승인 전용 채널)
2. `config/common.json`의 `slack.webhook_url` (공통 채널)
3. `.env`의 `SLACK_WEBHOOK_URL` (범용)

미설정 시 로그 경고만 남기고 파이프라인은 중단하지 않는다.

---

## 9. 금지사항

- 승인 포인트가 아닌 곳에서 "다음 단계 진행할까요?" 묻기
- 승인 포인트가 아닌 곳에서 사용자에게 확인/선택을 요구하는 모든 형태의 프롬프트 (진행 여부, Bash 실행 여부 등)
- 상태 JSON 없이 기억에만 의존하여 진행
- Phase 순서 건너뛰기 (승인 4 거부 시 Phase 4 건너뜀은 예외)
- 리뷰 루프 3회 초과하여 계속 재작업
- **승인 후 다음 Phase 미실행**: 승인을 받으면 반드시 "승인 즉시 실행" 블록의 모든 액션을 완료하고 다음 Phase로 진입해야 한다. 승인만 기록하고 멈추는 것은 금지.

## 10. 무중단 실행 원칙

**파이프라인 실행 중 터미널 확인 창을 띄우지 않는다.**

- 승인 포인트(수동 6개)에서만 멈추고, 그 외 모든 단계는 자동 진행한다.
- Bash 호출, Skill 호출, 파일 읽기/쓰기 등 중간 작업에서 확인 프롬프트를 띄우면 파이프라인이 무기한 멈추므로 절대 금지한다.
- 에러 발생 시에도 사용자에게 묻지 않고, 상태 JSON에 에러를 기록한 뒤 사용자에게 보고한다.
