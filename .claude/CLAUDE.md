# QA Agent System

> QA AI 에이전트 팀 운영 프로젝트 (v2.0)
> 아키텍처: docs/qa_agent_architecture.md 참조
> 사람 조직: docs/qa_organization.md 참조

---

## 1. 프로젝트 개요

이 프로젝트는 QA 팀장(사람) + Orchestrator 기반 자율 협업 AI 에이전트 팀으로 운영되는 QA 시스템이다.

- **팀장**: 트리거(한 번), 승인(7개 포인트), 최종 판단 (유일한 사람)
- **Orchestrator**: 파이프라인 관리, 에이전트 간 핸드오프, 품질 게이트, 재작업 루프
- **에이전트**: 각 역할에 특화된 Claude Code 스킬 에이전트 (14개)
- **운영 방식**: 팀장 지시 → Orchestrator가 에이전트 자율 협업 → 최종 보고 → 승인
- **대상 프로젝트**: SAY, BAY, SSO (프로젝트별 병렬 파이프라인)

---

## 2. 에이전트 목록 (14개)

### 유틸리티

| # | 에이전트 | 스킬 | 상태 |
|---|----------|------|------|
| 0 | Setup Guide | `/setup` | 신규 개발 |

### 오케스트레이션

| # | 에이전트 | 스킬 | 상태 |
|---|----------|------|------|
| 1 | Orchestrator | `/run-pipeline` | 신규 개발 |

### 스쿼드 (프로젝트별 실행)

| # | 에이전트 | 스킬 | 상태 |
|---|----------|------|------|
| 2 | Scenario Writer | `/write-scenario` | 기존 (SAY 이관) |
| 3 | TC Writer | `/write-tc` | 기존 (SAY 이관) |
| 4 | Project Reporter | `/report-project` | 신규 개발 |
| 5 | Bug Reporter | `/report-bug` | 비활성화 (JIRA 연동 후 활성화) |

### 분석/리뷰 (전 프로젝트 공통)

| # | 에이전트 | 스킬 | 상태 |
|---|----------|------|------|
| 6 | Format Checker | `/check-format` | 신규 개발 |
| 7 | Spec Reviewer | `/review-spec` | 신규 개발 (기획서 기준 리뷰) |
| 8 | QA Reviewer | `/review-qa` | 신규 개발 (QA 관점 크로스 체크) |
| 9 | Impact Analyzer | `/analyze-impact` | 신규 개발 |
| 10 | Rule Learner | `/learn-rules` | 신규 개발 |

> **리뷰 팀 운영**: Spec Reviewer + QA Reviewer는 병렬로 동시 실행 (Agent Teams)
> - Spec Reviewer: "기획서에 있는 걸 다 했나?" (커버리지, 비즈니스 로직)
> - QA Reviewer: "기획서에 없지만 놓치면 안 되는 건?" (엣지케이스, 경계값, 네거티브)

### 자동화

| # | 에이전트 | 스킬 | 상태 |
|---|----------|------|------|
| 11 | Automation Assessor | `/assess-automation` | 신규 개발 |
| 12 | Test Coder | `/write-test-code` | 기존 (SAY 이관) |
| 13 | Fail Analyzer | `/analyze-fail` | 신규 개발 |

> Reporter(`/upload-report`), Slack Notifier(`/share-slack`)는 **GitHub Actions 워크플로**로 대체됨

---

## 3. 에이전트 운영 규칙

### 3.0 온보딩 (최초 1회)
- 플러그인 설치 후 `/init` → `/setup` 순서로 실행
- `/init`: 로컬 폴더 구조 + 빈 config 파일 생성
- `/setup`: 공통 설정(`config/common.json`) + 프로젝트별 설정(`config/projects/*.json`) + API 키(`.env`) 대화형 입력
- 온보딩 완료 즉시 업무 요청 가능 (별도 설정 파일 수동 편집 불필요)
- 이후 `/setup check`로 설정 상태 확인, `/setup update {프로젝트}`로 변경 가능

**⚠️ 자동 감지 규칙 (필수):**
- `config/` 폴더가 없으면: `"⚠️ 작업 환경이 초기화되지 않았습니다. /init 을 먼저 실행해주세요."`
- `config/common.json`의 필수 값(`slack.team_lead_user_id`, `jira.base_url`, `confluence.base_url`)이 비어있으면: `"⚠️ 환경 설정이 완료되지 않았습니다. /setup 으로 초기 세팅을 먼저 진행해주세요."`
- `.env` 파일이 없으면: `"⚠️ .env 파일이 없습니다. /setup 을 실행하여 API 키를 설정해주세요."`
- 사용자가 업무 요청 시에도 미설정 감지되면 안내 후 진행 여부 확인
- 온보딩 완료 상태면 안내 없이 바로 업무 수행

### 3.1 트리거 규칙
- 팀장은 **자유 형식**으로 지시 (예: "새 업무 줄게", "SAY 처리해", "TC 리뷰해줘")
- Orchestrator가 **부족한 정보를 자동 질문**하여 수집 (프로젝트, 버전, 기획서 링크 등)
- `config/projects/*.json`에서 프로젝트 컨텍스트 자동 참조
- **정보 수집 완료 → 진행 계획을 팀장에게 보고 → 팀장 확인 후 실행**
- **Orchestrator가 팀장 대행**으로 에이전트를 호출하고 조율
- 에이전트는 직접 다른 에이전트를 호출하지 않음 (Orchestrator 경유)
- 승인 포인트에서만 팀장에게 보고

### 3.2 자율 협업 규칙
- 검토 → 수정 → 재검토 루프를 Orchestrator가 자동 관리
- 품질 게이트 미달 시 해당 에이전트에 자동 재작업 지시 (최대 3회)
- 루프 한도 초과 시 팀장에게 에스컬레이션
- 분석/리뷰 에이전트는 **스쿼드 구분 없이** 전 프로젝트에 동일 기준 적용

### 3.3 데이터 소스 우선순위

**기본 모드 (시나리오/TC 작성):**
1. Confluence (기획서/정책서) - 기본 기준
2. Figma - 문구 불일치 발견 시 참고
3. 로컬 JSON - 참고용

**Figma 보강 모드:**
1. Figma 디자인 (실제 구현에 가까운 값) - 최우선
2. 기획서/정책서 (Figma에 없는 정책/로직)
3. 로컬 JSON - 참고용

불일치 발견 시 Figma 기준으로 시나리오 반영, 변경 목록은 Orchestrator → 팀장에게 보고

### 3.4 승인 포인트 (7개) + Slack DM 알림
- 승인 포인트 도달 시 **QA_Agent Slack Bot → 팀장 DM**으로 알림 발송
- 팀장이 세션을 보지 않아도 Slack으로 승인 요청 수신 가능

0. **진행 계획 확인** - Orchestrator가 정보 수집 후 계획 보고 → 팀장 확인 후 실행
1. **1차 시나리오 리뷰 Pass 확인** - Spec Reviewer + QA Reviewer 병렬 리뷰 Pass 후
2. **Figma 검수 후 시나리오 확정** - 팀장이 Chrome + Claude in Chrome으로 직접 검수
3. **TC 확정** - Format Checker (구조) + Spec Reviewer + QA Reviewer (내용 병렬) Pass 후
4. **자동화 구현 여부 결정** - Automation Assessor 검토 후
5. **FAIL 분석 결과** - 실제 버그 발견 시
6. **크로스 프로젝트 영향도** - SSO 등 공통 변경 시

### 3.5 업무 흐름 요약

```
Phase -1: 온보딩 (/setup → 환경 설정 완료)
  ↓
Phase 0: 입력 수집 + 계획 확인 (★ 승인 0)
  ↓
Phase 1-A: 시나리오 확정
  ① Scenario Writer
  ② [Spec Reviewer + QA Reviewer] 병렬 크로스 체크
  ★ 승인 1: 시나리오 리뷰 Pass
  ③ Scenario Writer (Figma 보강) → ④ 팀장 Figma 검수
  ★ 승인 2: 시나리오 확정
  ↓
Phase 1-B: TC 확정
  ⑤ TC Writer → ⑥ Format Checker (구조)
  ⑦ [Spec Reviewer + QA Reviewer] 병렬 크로스 체크
  ★ 승인 3: TC 확정
  ↓
Phase 3: 자동화
  Automation Assessor (★ 승인 4) → Test Coder → GH Actions → Fail Analyzer (★ 승인 5)
  ↓
Phase 4: 최종 보고 (★ 승인 6: 크로스 프로젝트 해당 시)
```

### 3.6 Figma MCP 사용 규칙 (필수)
- 파일 전체 조회 절대 금지 (Rate Limit → 계정 차단)
- 사용자가 직접 전달한 노드 ID만 요청
- 상위 페이지/섹션/캔버스 노드 요청 금지

---

## 4. 파일 구조

```
qa_agent/
├── .claude/
│   ├── CLAUDE.md                      ← 이 파일
│   └── skills/                        ← 에이전트 스킬 정의 (14개)
│       ├── setup/SKILL.md               (신규) Setup Guide - 온보딩
│       ├── run-pipeline/SKILL.md        (신규) Orchestrator
│       ├── write-scenario/SKILL.md      (기존) Scenario Writer
│       ├── write-tc/SKILL.md            (기존) TC Writer
│       ├── report-project/SKILL.md      (신규) Project Reporter
│       ├── report-bug/SKILL.md          (신규) Bug Reporter
│       ├── check-format/SKILL.md        (신규) Format Checker
│       ├── review-spec/SKILL.md         (신규) Spec Reviewer
│       ├── review-qa/SKILL.md           (신규) QA Reviewer
│       ├── analyze-impact/SKILL.md      (신규) Impact Analyzer
│       ├── learn-rules/SKILL.md         (신규) Rule Learner
│       ├── assess-automation/SKILL.md   (신규) Automation Assessor
│       ├── write-test-code/SKILL.md     (기존) Test Coder
│       └── analyze-fail/SKILL.md        (신규) Fail Analyzer
├── agents/                            ← 에이전트 설정/프로필
├── config/                            ← 환경 설정
│   └── projects/                        ← 프로젝트별 설정/상태 (Orchestrator 참조)
│       ├── say.json
│       ├── bay.json
│       └── sso.json
├── data/                              ← 에이전트 산출물
│   ├── scenarios/                       ← Scenario Writer
│   ├── tc/                              ← TC Writer
│   ├── reviews/                         ← Format Checker + Spec Reviewer + QA Reviewer + Impact Analyzer
│   ├── assessments/                     ← Automation Assessor
│   ├── fail_analysis/                   ← Fail Analyzer
│   ├── bugs/                            ← Bug Reporter (신규)
│   ├── rules/                           ← Rule Learner (신규)
│   ├── test_results/                    ← GitHub Actions (외부)
│   └── pipeline/                        ← Orchestrator (신규)
├── docs/                              ← 설계 문서
│   ├── qa_agent_architecture.md         (v2.0)
│   └── qa_organization.md
├── templates/                         ← 산출물 템플릿
│   └── figma_review_prompt.md          ← Figma 검수 프롬프트 (Phase 1-A)
└── tests/                             ← Test Coder 산출물
```

---

## 5. TC 작성 규칙 (SAY 프로젝트 기준 참조)

> 상세 규칙은 SAY 프로젝트의 CLAUDE.md 11절~11.10절 참조
> 에이전트별 SKILL.md에 해당 규칙이 포함됨

### 핵심 규칙 요약
- Depth 구조: 조건 하위에 동작/결과 배치 (평면적 구조 금지)
- Expected Result: 결과만 작성, 조건 포함 금지, "노출됨" 중복 금지
- Priority: P1/P2/P3만 사용
- 금지 용어: "테이블"→"리스트", "컬럼"→제거, "헤더"→"리스트 헤더"
- 활성화/비활성화 표기: Active/Disable 영문 금지 → "버튼이 활성화 상태로 노출됨" / "버튼이 비활성화 상태로 노출됨"
- 디자인 스펙 금지: 픽셀값(w222), Hex 코드(#5442FF), 디자인 토큰(Gray 500), 스타일 스펙(Filled/아웃라인) → 기능적 상태로 표현
- 시나리오에 명시된 내용만 작성 (추측 금지)

---

## 6. 개발 로드맵

### Phase 0: 온보딩 (즉시)
- Setup Guide `/setup` - 플러그인 설치 후 환경 설정 가이드

### Phase 1: 기반 (즉시)
- SAY 프로젝트 기존 스킬 이관: Scenario Writer, TC Writer, Test Coder

### Phase 2: 핵심 (우선)
- **Orchestrator** `/run-pipeline` - 자율 협업의 핵심, 파이프라인 관리
- Format Checker `/check-format` - 양식 검토 자동화
- Spec Reviewer `/review-spec` - 기획서 기준 커버리지/누락 검토
- QA Reviewer `/review-qa` - QA 관점 크로스 체크 (엣지케이스, 실행 가능성)

### Phase 3: 확장
- Fail Analyzer `/analyze-fail` - FAIL 원인 분석
- Automation Assessor `/assess-automation` - 자동화 사전 검토
- Project Reporter `/report-project` - 프로젝트별 현황 보고

### Phase 4: 고도화
- Impact Analyzer `/analyze-impact` - 크로스 프로젝트 영향도 분석
- Bug Reporter `/report-bug` - JIRA 자동 버그 리포팅
- Rule Learner `/learn-rules` - 리뷰 패턴 학습/규칙 강화

---

**최종 업데이트:** 2026-02-25 (v2.2 - Setup Guide 추가, 온보딩 흐름 정의)
