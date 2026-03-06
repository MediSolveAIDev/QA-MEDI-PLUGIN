# /run-pipeline - Orchestrator

> Claude Code가 직접 파이프라인을 운영한다. Skill 도구로 각 스킬을 호출하고, JSON으로 상태를 관리한다.
>
> **별칭 트리거**: `config/common.json`의 `orchestrator.nickname`에 설정된 별칭으로 호출하면 무조건 Orchestrator로 인식한다.
> - 예: nickname이 설정되어 있으면 → "{별칭}야 새 업무 줄게", "{별칭} 진행 상황" 등
>
> **자연어 트리거**: 아래 패턴이 감지되면 이 스킬을 즉시 실행한다.
> - "새 업무 줄게", "새 업무", "업무 줄게", "일 줄게"
> - "파이프라인 실행", "파이프라인 시작", "파이프라인 돌려"
> - "{프로젝트명} 처리해", "{프로젝트명} 시작해"
> - "시나리오부터 해줘", "전체 진행해줘"
> - "이어서 해줘", "재개해줘", "이어서 진행"
> - "기획서 업데이트됐어", "기획 변경됐어"
> - "진행 상황", "어디까지 했어", "상태 알려줘", "지금 뭐 하고 있어"
>
> **중요**: 별칭 또는 위 패턴 감지 시 사용자에게 "어떤 작업을 할까요?" 같은 선택지를 제시하지 않는다. 부족한 정보만 질문한 뒤 바로 파이프라인을 실행한다.

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

# Slack 알림
python -m orchestrator.cli_state notify SAY_v1.4.0 approval "0_plan|진행 계획이 수립되었습니다."
python -m orchestrator.cli_state notify SAY_v1.4.0 progress "시나리오 작성 완료, 리뷰 진행합니다."

# 파이프라인 목록
python -m orchestrator.cli_state list
```

---

## 3. 실행 절차

### 3.1 파이프라인 시작

사용자가 업무를 요청하면:

1. 부족한 정보 질문 (프로젝트, 버전, 기능명, 기획서 URL)
2. `config/projects/*.json`에서 프로젝트 정보 자동 참조
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
3. Slack 알림: `notify {ID} approval "0_plan|진행 계획이 수립되었습니다."`
4. **★ 승인 0 (수동)**: 사용자에게 계획 확인 요청 → 승인 대기
5. 승인 시: `update {ID} approval.0_plan approved` → Phase 1-A로 진행

### Phase 1-A: 시나리오 확정

1. `update {ID} phase "1-A"`
2. Skill `/write-scenario` 호출 (기획서 URL 전달)
3. 산출물 경로 저장: `update {ID} artifact.scenario {파일경로}`
4. Slack 알림: `notify {ID} progress "시나리오 작성 완료, 리뷰 진행합니다."`
5. Skill `/review-spec` 호출 (시나리오 파일 전달)
6. Skill `/review-qa` 호출 (시나리오 파일 전달)
7. 리뷰 결과 확인:
   - **PASS**: 8단계로
   - **FAIL**: Skill `/write-scenario` 재호출 (피드백 반영), `update {ID} rework write-scenario` → 5단계 반복 (최대 3회)
   - **3회 초과**: Slack 에스컬레이션 알림 → 사용자에게 보고 → 중단
8. 리뷰 산출물 저장: `update {ID} artifact.scenario_review_spec {경로}`, `artifact.scenario_review_qa {경로}`
9. Slack 알림: `notify {ID} approval "1_scenario_review|시나리오 리뷰가 Pass 되었습니다."`
10. **★ 승인 1 (수동)**: 사용자에게 리뷰 결과 확인 요청
11. Skill `/write-scenario` 호출 (Figma 보강 컨텍스트)
12. Slack 알림: `notify {ID} approval "2_scenario_final|Figma 보강 시나리오가 준비되었습니다."`
13. **★ 승인 2 (수동)**: 사용자에게 Figma 검수 후 시나리오 확정 요청
14. 승인 시: Confluence 업로드 (Bash로 Python 유틸 호출)
15. `update {ID} phase "1-B"`

### Phase 1-B: TC 확정

1. `update {ID} phase "1-B"`
2. Skill `/write-tc` 호출 (확정 시나리오 파일 전달)
3. 산출물 경로 저장: `update {ID} artifact.tc {파일경로}`
4. Skill `/check-format` 호출 (TC 파일 전달)
   - **PASS**: 5단계로
   - **FAIL**: Skill `/write-tc` 재호출 (포맷 피드백 반영) → 4단계 반복 (최대 3회)
5. Slack 알림: `notify {ID} progress "TC 작성 완료, 포맷 검증 Pass. 내용 리뷰 진행합니다."`
6. Skill `/review-spec` 호출 (TC 파일 전달)
7. Skill `/review-qa` 호출 (TC 파일 전달)
8. 리뷰 결과 확인:
   - **PASS**: 9단계로
   - **FAIL**: Skill `/write-tc` 재호출 (피드백 반영) → 6단계 반복 (최대 3회)
9. Slack 알림: `notify {ID} approval "3_tc_final|TC 리뷰가 Pass 되었습니다."`
10. **★ 승인 3 (수동)**: 사용자에게 TC 확정 요청
11. 승인 시: Google Sheet 업로드 (Bash로 Python 유틸 호출)
12. `update {ID} phase "3"`

### Phase 3: 자동화

1. `update {ID} phase "3"`
2. Skill `/assess-automation` 호출
3. Slack 알림: `notify {ID} approval "4_automation|자동화 검토 결과가 준비되었습니다."`
4. **★ 승인 4 (수동)**: 자동화 구현 여부 결정
   - 거부 시: Phase 4로 건너뜀
5. Skill `/write-test-code` 호출
6. Slack 알림: `notify {ID} progress "테스트 코드 생성 완료."`
7. 사용자에게 안내: "GitHub Actions에서 테스트를 실행하고 결과를 알려주세요."
8. 테스트 결과 확인 후:
   - FAIL 있으면: Skill `/analyze-fail` 호출
   - **★ 승인 5 (자동)**: FAIL 없으면 자동 통과, FAIL 있으면 Slack 알림만
9. `update {ID} phase "4"`

### Phase 4: 최종 보고

1. `update {ID} phase "4"`
2. Skill `/report-project` 호출
3. Slack 알림: `notify {ID} progress "리포트 생성 완료."`
4. 크로스 프로젝트 해당 시: Skill `/analyze-impact` 호출
   - **★ 승인 6 (수동)**: 영향도 확인 (해당 시에만)
5. `update {ID} status "completed"`
6. 파이프라인 완료 요약 출력

---

## 5. 승인 규칙

| # | 승인 포인트 | Phase | 모드 | 설명 |
|---|------------|-------|------|------|
| 0 | 진행 계획 확인 | 0 | 수동 | 계획 보고 → 확인 후 실행 |
| 1 | 시나리오 리뷰 Pass | 1-A | 수동 | 리뷰 루프 통과 후 결과 확인 |
| 2 | 시나리오 확정 | 1-A | 수동 | Figma 보강 후 팀장 직접 검수 |
| 3 | TC 확정 | 1-B | 수동 | 포맷 검증 + 리뷰 루프 통과 후 확정 |
| 4 | 자동화 구현 여부 | 3 | 수동 | 자동화 검토 후 진행/거부 결정 |
| 5 | FAIL 분석 결과 | 3 | 자동 | FAIL 없으면 자동 통과 |
| 6 | 크로스 프로젝트 영향도 | 4 | 수동 | 해당 시에만 |

**수동 승인 시 사용자 응답 처리:**
- "승인", "ㅇㅇ", "확인" → approved → 다음 단계
- "재작업", "수정해" → rework → 해당 단계 재실행
- "거부", "중단" → rejected → 파이프라인 중단, 상태 저장

**자동 승인 (5번):**
- Slack 알림만 보내고 바로 다음 단계 진행

---

## 6. 리뷰 루프 규칙

1. `/review-spec`과 `/review-qa`를 호출하여 리뷰 결과 확인
2. 리뷰 결과 JSON에서 `verdict` 필드 확인 (PASS/FAIL)
3. FAIL 시:
   - 피드백 내용을 writer 스킬에 전달하여 재작업
   - `update {ID} rework {스킬명}` 으로 재작업 횟수 기록
   - 재작업 산출물로 다시 리뷰 (최대 3회)
4. 3회 초과 시:
   - `notify {ID} approval "escalation|리뷰 3회 재작업 후에도 통과하지 못했습니다."`
   - 사용자에게 에스컬레이션 보고
   - `update {ID} status "escalated"`

---

## 7. 기획서 변경 대응

"기획서 업데이트됐어" 감지 시:

1. `python -m orchestrator.cli_state status latest` 로 현재 상태 확인
2. 현재 Phase에 따라 재작업 범위 결정:
   - **1-A 진행 중/완료**: 시나리오 재작업 → 리뷰 → 승인
   - **1-B 진행 중/완료**: 시나리오 diff → 변경된 부분 TC 재작업
   - **3 이후**: 시나리오 → TC → 테스트코드 순차 재작업
3. 재작업 범위를 사용자에게 보고 후 진행

---

## 8. 금지사항

- 승인 포인트가 아닌 곳에서 "다음 단계 진행할까요?" 묻기
- 승인 포인트가 아닌 곳에서 사용자에게 확인/선택을 요구하는 모든 형태의 프롬프트 (진행 여부, Bash 실행 여부 등)
- 상태 JSON 없이 기억에만 의존하여 진행
- Phase 순서 건너뛰기 (승인 4 거부 시 Phase 4 건너뜀은 예외)
- 리뷰 루프 3회 초과하여 계속 재작업

## 9. 무중단 실행 원칙

**파이프라인 실행 중 터미널 확인 창을 띄우지 않는다.**

- 팀장은 터미널을 상시 확인하지 않는다. Slack 승인 알림이 올 때만 확인한다.
- 승인 포인트(수동 6개)에서만 멈추고, 그 외 모든 단계는 자동 진행한다.
- Bash 호출, Skill 호출, 파일 읽기/쓰기 등 중간 작업에서 확인 프롬프트를 띄우면 파이프라인이 무기한 멈추므로 절대 금지한다.
- 에러 발생 시에도 사용자에게 묻지 않고, 상태 JSON에 에러를 기록한 뒤 Slack으로 에스컬레이션 알림을 보낸다.
