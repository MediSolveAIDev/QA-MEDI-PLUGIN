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

### 2.1 Claude Code 내 실행 (기본)
```bash
python -m orchestrator --project SAY --version v1.4.0 --feature "로그인" --spec-url "CONFLUENCE_URL" --auto-approve
```
→ **Claude Code에서는 반드시 `--auto-approve`를 사용한다** (input() 대화형 입력 불가)
→ 프로젝트/버전/기능명/기획서 URL은 CLI 인자로 전달 (config에서 자동 참조 가능한 값은 생략)

### 2.2 터미널 직접 실행 (대화형)
```bash
python -m orchestrator
```
→ 터미널에서 직접 실행 시 대화형으로 정보 수집 + 승인 포인트에서 수동 승인

### 2.3 특정 Phase만
```bash
python -m orchestrator --phase 1-B
```

### 2.4 중단된 파이프라인 재개
```bash
python -m orchestrator --resume SAY_v1.4.0
```

### 2.5 복수 프로젝트 병렬
```bash
python -m orchestrator --project SAY --project BAY --version v1.4.0
```

### 2.6 기획서 변경 대응
```bash
python -m orchestrator --resume SAY_v1.4.0 --spec-update NEW_SPEC_URL
```

---

## 3. 자연어 매핑

사용자의 자연어 요청을 적절한 CLI 명령으로 변환한다:

| 사용자 입력 | 실행 명령 |
|------------|-----------|
| "새 업무 줄게" | `python -m orchestrator` |
| "SAY v1.4.0 처리해" | `python -m orchestrator --project SAY --version v1.4.0` |
| "TC 리뷰해줘" | `python -m orchestrator --phase 1-B` |
| "기획서 업데이트됐어" + URL | `python -m orchestrator --resume {ID} --spec-update {URL}` |
| "이어서 해줘" | `python -m orchestrator --resume {최근 pipeline_id}` |

---

## 4. 파이프라인 흐름

Python Orchestrator가 아래 흐름을 자동으로 진행한다:

```
Phase 0: 입력 수집 + 계획 확인 (★ 승인 0)
  ↓
Phase 1-A: 시나리오 확정
  ① /write-scenario → ② [/review-spec + /review-qa] 병렬
  ③ 리뷰 루프 (최대 3회) → ★ 승인 1
  ④ Figma 보강 → ★ 승인 2: 시나리오 확정
  ⑤ Confluence 업로드
  ↓
Phase 1-B: TC 확정
  ① /write-tc → ② /check-format
  ③ [/review-spec + /review-qa] 병렬
  ④ 리뷰 루프 (최대 3회) → ★ 승인 3: TC 확정
  ⑤ Google Sheet 업로드
  ↓
Phase 3: 자동화
  ① /assess-automation → ★ 승인 4
  ② /write-test-code → GH Actions
  ③ FAIL → /analyze-fail → ★ 승인 5
  ↓
Phase 4: 최종 보고 (★ 승인 6: 크로스 프로젝트 해당 시)
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
