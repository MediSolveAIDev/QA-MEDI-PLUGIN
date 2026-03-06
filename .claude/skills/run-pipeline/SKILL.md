# /run-pipeline - Orchestrator

> Python Orchestrator를 실행하여 에이전트 파이프라인을 자동 운영합니다.
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
> **중요**: 위 패턴 감지 시 사용자에게 "어떤 작업을 할까요?" 같은 선택지를 제시하지 않는다. config/projects/*.json에서 프로젝트 정보를 자동 참조하고, 부족한 정보만 질문한 뒤 바로 파이프라인을 실행한다.

---

## 1. 개요

- **역할**: 팀장 지시 → 에이전트 자율 협업 조율 → 최종 보고
- **구현**: `orchestrator/` Python 패키지 (claude -p로 각 스킬 호출)
- **원칙**: 팀장은 트리거 1회 + 승인 7개 포인트만 관여

---

## 2. 실행 방법

사용자가 `/run-pipeline` 또는 자연어로 업무를 요청하면, 아래 Python 명령을 실행한다.

### 2.1 Claude Code 내 실행 (기본 — 전체 자동 진행)

`--auto-approve`로 실행하면 **전체 파이프라인이 한 번에 진행**된다.
팀장 승인이 필요한 포인트(0,1,2,3,4,6)에서만 멈추고, 나머지는 자동으로 달린다.

**실행:**
```bash
python -m orchestrator --project SAY --version v1.4.0 --feature "로그인" --spec-url "PAGE_ID" --auto-approve
```

**승인 동작:**
- 자동 승인 (5): Slack 알림만 보내고 바로 다음 단계 진행
- 수동 승인 (0,1,2,3,4,6): Slack 알림 + 터미널에서 팀장 응답 대기
- "승인" → 다음 단계 진행
- "재작업" → 해당 단계 재실행
- "거부" → 파이프라인 중단, 상태 저장

### 2.2 터미널 직접 실행 (대화형)
```bash
python -m orchestrator
```
→ 터미널에서 직접 실행 시 대화형으로 정보 수집 + 승인 포인트에서 수동 승인

### 2.3 특정 Phase만
```bash
python -m orchestrator --phase 1-B --auto-approve
```

### 2.4 중단된 파이프라인 재개
```bash
python -m orchestrator --resume SAY_v1.4.0 --auto-approve
```

### 2.5 복수 프로젝트 병렬
```bash
python -m orchestrator --project SAY --project BAY --version v1.4.0 --auto-approve
```

### 2.6 기획서 변경 대응
```bash
python -m orchestrator --resume SAY_v1.4.0 --spec-update NEW_SPEC_URL --auto-approve
```

---

## 3. 자연어 매핑

사용자의 자연어 요청을 Phase별 실행으로 변환한다:

| 사용자 입력 | 동작 |
|------------|------|
| "새 업무 줄게" | 정보 수집 → Phase 1-A부터 순차 실행 |
| "SAY v1.4.0 처리해" | config에서 참조 → Phase 1-A부터 순차 실행 |
| "TC 리뷰해줘" | `--phase 1-B --auto-approve` |
| "기획서 업데이트됐어" + URL | `--resume {ID} --spec-update {URL} --auto-approve` |
| "이어서 해줘" | `--resume {최근 pipeline_id} --auto-approve` |
| "승인" / "ㅇㅇ" | 다음 Phase 실행 |
| "재작업" | 같은 Phase 재실행 |
| "진행 상황 알려줘" | `--status` (최근 파이프라인) |
| "SAY 어디까지 했어" | `--status SAY_v1.4.0` |

---

## 4. 파이프라인 흐름

Python Orchestrator가 아래 흐름을 자동으로 진행한다:

```
Phase 0: 입력 수집 + 계획 확인
  ・정보 수집 (프로젝트/버전/기획서)
  ★ 승인 0: 진행 계획 확인
  ↓
Phase 1-A: 시나리오 확정
  ① /write-scenario (시나리오 작성)
  ② [/review-spec + /review-qa] 병렬 크로스 체크
  ③ 리뷰 루프 (Pass까지 자동 재작업, 최대 3회)
  ★ 승인 1: 시나리오 리뷰 Pass 확인
  ④ /write-scenario (Figma 보강)
  ⑤ 팀장 Figma 직접 검수
  ★ 승인 2: 시나리오 확정 → Confluence 업로드
  ↓
Phase 1-B: TC 확정
  ① /write-tc (TC 작성)
  ② /check-format (구조 검증, 실패 시 자동 재작업)
  ③ [/review-spec + /review-qa] 병렬 크로스 체크
  ④ 리뷰 루프 (Pass까지 자동 재작업, 최대 3회)
  ★ 승인 3: TC 확정 → Google Sheet 업로드
  ↓
Phase 3: 자동화
  ① /assess-automation (자동화 검토)
  ★ 승인 4: 자동화 구현 여부 결정 (거부 시 Phase 4로 건너뜀)
  ② /write-test-code (테스트 코드 생성)
  ③ GitHub Actions 실행 (수동)
  ④ FAIL 발견 시 → /analyze-fail
  ★ 승인 5: FAIL 분석 결과 확인 (FAIL 없으면 자동 통과)
  ↓
Phase 4: 최종 보고
  ① /report-project (리포트 생성)
  ② 크로스 프로젝트 해당 시 → /analyze-impact
  ★ 승인 6: 크로스 프로젝트 영향도 확인 (해당 시에만)
  ③ 파이프라인 완료 요약 출력
```

### 기획서 변경 대응

진행 중 "기획서 업데이트됐어" 시:
1. 기존 시나리오 백업
2. /write-scenario (diff 모드) → 리뷰 루프 → 승인
3. Confluence 재업로드
4. 선택: [A] 원래 단계 복귀 / [B] TC도 수정

---

## 5. 처리 규칙

1. **반드시 `python -m orchestrator` 명령으로 실행**한다
2. Orchestrator가 `claude -p`로 각 스킬을 독립 호출한다
3. 승인 포인트에서 터미널 input()으로 팀장 응답을 받는다
4. 파이프라인 상태는 `data/pipeline/`에 자동 저장된다
5. Ctrl+C로 일시정지 → `--resume`로 재개 가능
6. Slack 알림 비활성화: `--no-slack` 옵션
