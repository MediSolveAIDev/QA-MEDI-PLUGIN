# QA-MEDI-PLUGIN v2.9.0

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

## 스킬 목록

| # | 스킬 | 커맨드 | 역할 |
|---|------|--------|------|
| 0 | Init | `/init` | 프로젝트 루트 환경 초기화 |
| 1 | Setup Guide | `/setup` | 환경 설정 (config, .env) |
| 2 | Orchestrator | `/run-pipeline` | 파이프라인 관리 |
| 3 | Scenario Writer | `/write-scenario` | 시나리오 작성 |
| 4 | TC Writer | `/write-tc` | TC 작성 |
| 5 | Format Checker | `/check-format` | TC 양식 검토 |
| 6 | Spec Reviewer | `/review-spec` | 기획서 기준 리뷰 |
| 7 | QA Reviewer | `/review-qa` | QA 관점 크로스 체크 |
| 8 | TC Reviewer | `/review-tc` | TC 내용 리뷰 |
| 9 | Project Reporter | `/report-project` | 프로젝트 현황 보고 |
| 10 | Bug Reporter | `/report-bug` | JIRA 버그 관리 (2-Phase) |
| 11 | Impact Analyzer | `/analyze-impact` | 크로스 프로젝트 영향도 |
| 12 | Rule Learner | `/learn-rules` | 리뷰 패턴 학습 |
| 13 | Automation Assessor | `/assess-automation` | 자동화 사전 검토 |
| 14 | Test Coder | `/write-test-code` | 자동화 코드 작성 |
| 15 | Fail Analyzer | `/analyze-fail` | FAIL 원인 분석 |

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
