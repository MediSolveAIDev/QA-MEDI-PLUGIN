# QA-MEDI-PLUGIN v3.0.0

QA AI 에이전트 팀 운영 플러그인 — Claude Code 스킬 기반

## 설치

```bash
/plugin marketplace add MediSolveAIDev/QA-MEDI-PLUGIN
/plugin install qa-medi-plugin@qa-medi-plugin
```

## 초기 설정

각 프로젝트 폴더에서 실행:

```bash
cd say-admin/                # 프로젝트 폴더로 이동
claude                       # Claude Code 실행
/qa-medi-plugin:init         # 폴더 구조 + 빈 config 파일 생성
/qa-medi-plugin:setup        # config 값 채우기 + .env 생성 (대화형)
```

## 스킬 목록 (20개)

### 환경 설정

#### Init Guide `/init`
프로젝트 루트에 폴더 구조(`config/`, `data/`, `tests/`, `tools/`)와 빈 config 템플릿을 생성합니다. 프로젝트별 최초 1회 실행. 플러그인 업데이트로 구조가 변경되면 재실행 필요 (기존 파일은 유지).

- **입력**: 없음 (프로젝트 루트에서 실행)
- **출력**: `config/common.json`, `config/project.json`, `data/` 하위 폴더, `.env.template`
- **예시**: `/init`

#### Setup Guide `/setup`
JIRA, Confluence, GitHub, Slack, Figma 등 외부 서비스 연결을 대화형으로 설정합니다.

- **입력**: 모드 지정 (생략 시 초기 세팅)
- **출력**: `config/common.json`, `config/project.json`, `.env`
- **예시**: `/setup` · `/setup check` (상태 확인) · `/setup update` (설정 변경)

---

### 오케스트레이션

#### Orchestrator `/run-pipeline`
팀장의 자연어 지시를 받아 시나리오 → TC → 자동화 → 버그 등록까지 전체 파이프라인을 자동 관리합니다. 부족한 정보는 자동으로 질문하고, 승인 포인트에서 팀장 확인을 받습니다.

- **입력**: 자연어 지시 (프로젝트명, 버전, 기획서 URL 등)
- **출력**: `data/pipeline/{PROJECT}_{version}_pipeline.json` + 각 Phase별 산출물
- **예시**: `/run-pipeline` · `/run-pipeline SAY v1.4.0` · "새 업무 줄게"

---

### 작성 (Writing)

#### Scenario Writer `/write-scenario`
Confluence 기획서/정책서를 기반으로 테스트 시나리오를 작성합니다. 사용자 중심의 동작-결과 형태로 구성.

- **입력**: Confluence Page ID 또는 시나리오 파일 경로
- **출력**: `data/scenarios/{PROJECT}_{version}_{feature}_scenario.md`
- **예시**: `/write-scenario 123456789`

#### Figma Enricher `/enrich-figma`
Figma export(디자인 이미지 + 텍스트)를 기반으로 기존 시나리오를 보강합니다. UI 요소, 문구, 상태별 화면을 시나리오에 반영.

- **입력**: `data/figma_output/` 하위 폴더 경로 또는 프로젝트명
- **출력**: 보강된 시나리오 (원본 덮어쓰기 + `.backup.md` 백업)
- **예시**: `/enrich-figma data/figma_output/say_admin_1.3.0` · `/enrich-figma SAY`

#### TC Writer `/write-tc`
확정된 시나리오를 기반으로 테스트 케이스(TC)를 작성합니다. Depth 구조의 계층적 TC 생성.

- **입력**: 시나리오 MD 파일 경로, Confluence Page ID, 또는 Figma 노드 ID
- **출력**: `data/tc/{PROJECT}_{version}_{feature}_tc.json`
- **예시**: `/write-tc data/scenarios/SAY_v1.4.0_로그인_scenario.md`

---

### 검증 & 리뷰 (Review)

#### Format Checker `/check-format`
시나리오·TC의 양식 준수 여부를 검증합니다. 규칙 위반을 자동 탐지하고 수정 방법을 제시.

- **입력**: TC JSON 또는 시나리오 MD 파일 경로
- **출력**: `data/reviews/{PROJECT}_{version}_{feature}_format-check.json`
- **예시**: `/check-format data/tc/SAY_v1.4.0_로그인_tc.json`

#### Spec Reviewer `/review-spec`
기획서/정책서 기준으로 시나리오·TC의 커버리지와 정합성을 리뷰합니다. "기획서에 있는 걸 다 했나?" 관점.

- **입력**: TC JSON, 시나리오 MD 파일 경로, 또는 제품명+버전
- **출력**: `data/reviews/{PROJECT}_{version}_{feature}_review-spec.json`
- **예시**: `/review-spec data/tc/SAY_v1.4.0_로그인_tc.json`

#### QA Reviewer `/review-qa`
QA 실무 관점에서 시나리오·TC를 크로스 체크합니다. 엣지케이스, 네거티브 시나리오, 실행 가능성 판단.

- **입력**: TC JSON, 시나리오 MD 파일 경로, 또는 제품명+버전
- **출력**: `data/reviews/{PROJECT}_{version}_{feature}_review-qa.json`
- **예시**: `/review-qa data/tc/SAY_v1.4.0_로그인_tc.json`

#### Content Reviewer `/review-tc`
작성된 TC의 내용 완성도를 검증합니다. 시나리오 대비 TC 커버리지, 기획서 정합성, Priority 적정성 판단.

- **입력**: TC JSON, 시나리오 MD 파일 경로, 또는 제품명+버전
- **출력**: `data/reviews/{PROJECT}_{version}_{feature}_review-tc.json`
- **예시**: `/review-tc data/tc/SAY_v1.4.0_로그인_tc.json`

#### Bug Reviewer `/review-bug`
버그 리포트(Phase A 산출물)의 필드 완성도와 정합성을 검증합니다. 심각도, 중복 판단 타당성 확인.

- **입력**: bug JSON 파일 경로
- **출력**: `data/reviews/{PROJECT}_{version}_{feature}_review-bug.json`
- **예시**: `/review-bug data/bugs/SAY_v1.4.0_대시보드_bug.json`

---

### 분석 (Analysis)

#### Fail Analyzer `/analyze-fail`
자동화 테스트 FAIL 원인을 분석하고 분류합니다. 코드 이슈 / 실제 버그 / 환경 이슈 / TC 오류로 구분.

- **입력**: `data/test_results/test_results.json` (자동 탐색)
- **출력**: `data/fail_analysis/{PROJECT}_{version}_{feature}_fail-analysis.json`
- **예시**: `/analyze-fail` · "FAIL 분석해줘"

#### Impact Analyzer `/analyze-impact`
크로스 프로젝트 영향도를 분석합니다. SSO 등 공통 모듈 변경 시 SAY, BAY에 미치는 영향 파악.

- **입력**: 프로젝트명, 버전, 변경 사항
- **출력**: `data/reviews/{PROJECT}_{version}_{feature}_impact.json`
- **예시**: `/analyze-impact SSO v2.0.0 로그인 정책 변경`

#### Automation Assessor `/assess-automation`
확정된 TC의 자동화 적합성을 사전 검토합니다. 자동화 가능 여부, 기술적 제약, 공수 산정.

- **입력**: TC JSON 파일 경로
- **출력**: `data/assessments/{PROJECT}_{version}_{feature}_assessment.json`
- **예시**: `/assess-automation data/tc/SAY_v1.4.0_로그인_tc.json`

#### Rule Learner `/learn-rules`
리뷰 피드백에서 일반화 가능한 패턴을 추출하여 규칙으로 등록·관리합니다. 이후 시나리오/TC 작성 시 자동 참조.

- **입력**: 리뷰 결과 (자동 로드) 또는 수동 규칙
- **출력**: `data/rules/rule_{id}.json`
- **예시**: `/learn-rules` · `/learn-rules list` · `/learn-rules add "모달에서 ESC 키 동작 TC 필수"`

---

### 보고 & 버그 관리 (Reporting)

#### Project Reporter `/report-project`
프로젝트별 QA 현황(TC 실행 결과, 버그 통계, 자동화율, 리스크)을 종합 리포트로 생성합니다.

- **입력**: 프로젝트명, 버전 (`config/project.json`에서 자동 참조)
- **출력**: `data/pipeline/{PROJECT}_{version}_report.json`
- **예시**: `/report-project SAY v1.4.0` · "SAY 현황 보고해줘"

#### Bug Reporter `/report-bug`
JIRA 버그 티켓을 관리합니다. 3가지 모드로 동작:
- **Mode 1** (등록): FAIL → 후보 검색 → 중복/리오픈/신규 판단 → JIRA 생성
- **Mode 2** (조회): 버그 현황 조회 + QA 분석 보고서 생성 (JSON + HTML)
- **Mode 3** (관리): 티켓 상태 변경, 담당자 변경, 코멘트 추가

| 모드 | 입력 | 출력 | 예시 |
|------|------|------|------|
| Mode 1 | FAIL 분석 결과 | `data/bugs/*_bug.json` → JIRA 티켓 | `/report-bug collect SAY v1.4.0` |
| Mode 2 | 프로젝트 + 필터 | `data/bugs/*_report.json` + `.html` | `/report-bug query SAY --version v1.4.0` |
| Mode 3 | 티켓 키 + 액션 | JIRA 티켓 업데이트 | `/report-bug manage CENSAY-234 --action reopen` |

---

### 자동화 (Automation)

#### Test Coder `/write-test-code`
TC 또는 시나리오를 기반으로 pytest + Playwright 자동화 테스트 코드를 생성합니다. 기존 코드가 있으면 수정/추가.

- **입력**: TC JSON 또는 시나리오 MD 파일 경로
- **출력**: `tests/test_{PROJECT}_{version}_{feature}.py`
- **예시**: `/write-test-code data/tc/SAY_v1.4.0_로그인_tc.json`

---

### 공유 & 업로드 (Integration)

#### Slack Notifier `/share-slack`
테스트 결과를 Slack 채널로 공유하는 코드를 생성합니다. 성공률, 실패 항목, 리포트 링크 포함.

- **입력**: `data/test_results/test_results.json`
- **출력**: `share_test_results_to_slack.py` (실행 코드)
- **예시**: GitHub Actions에서 자동 호출 또는 수동 실행

#### Report Uploader `/upload-report`
테스트 결과 리포트를 Confluence 페이지로 업로드하는 코드를 생성합니다.

- **입력**: `data/checklist_results.json` 또는 `data/test_results.json`
- **출력**: `upload_report_to_confluence.py` (실행 코드) + Confluence 페이지
- **예시**: GitHub Actions에서 자동 호출 또는 수동 실행

## 파일 구조

```
플러그인 (글로벌 설치):
  ~/.claude/plugins/cache/qa-medi-marketplace/qa-medi-plugin/{버전}/

프로젝트 루트 (/init 생성):
├── config/
│   ├── common.json          ← 공통 설정 (JIRA URL 등)
│   └── project.json         ← 현재 프로젝트 설정
├── data/                    ← 에이전트 산출물
├── templates/               ← 검수 템플릿
├── tests/                   ← 자동화 테스트
└── .env                     ← API 키
```

## 업데이트

```bash
/plugin update qa-medi-plugin@qa-medi-plugin
```

플러그인 업데이트는 스킬 파일만 갱신. 로컬 작업 데이터(config, data, .env)에 영향 없음.

### ⚠️ v2.7.0 이하 → v2.8.0 이상 마이그레이션

config 구조가 변경되었습니다. 각 프로젝트 폴더에서 `/init` → `/setup` 다시 실행해주세요.

```
변경 전: config/projects/say.json (프로젝트별 파일 여러 개)
변경 후: config/project.json (현재 프로젝트 설정 1개)
```

> `/init` 실행 시 기존 파일은 건드리지 않고 `config/project.json`만 새로 생성됩니다.
> 스킬 실행 시 `config/project.json`이 없으면 자동으로 안내가 표시됩니다.
