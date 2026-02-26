# QA-MEDI-PLUGIN v2.1.0

QA AI 에이전트 팀 운영 플러그인 — Claude Code 스킬 기반

## 설치

```bash
/plugin marketplace add MediSolveAIDev/QA-MEDI-PLUGIN
/plugin install qa-medi-plugin@qa-medi-plugin
```

## 초기 설정

```bash
/qa-medi-plugin:init     # 로컬 폴더 구조 + 빈 config 파일 생성
/qa-medi-plugin:setup    # config 값 채우기 + .env 생성 (대화형)
```

## 스킬 목록

| # | 스킬 | 커맨드 | 역할 |
|---|------|--------|------|
| 0 | Init | `/init` | 로컬 작업 환경 초기화 |
| 1 | Setup Guide | `/setup` | 환경 설정 (config, .env) |
| 2 | Orchestrator | `/run-pipeline` | 파이프라인 관리 |
| 3 | Scenario Writer | `/write-scenario` | 시나리오 작성 |
| 4 | TC Writer | `/write-tc` | TC 작성 |
| 5 | Format Checker | `/check-format` | TC 양식 검토 |
| 6 | Spec Reviewer | `/review-spec` | 기획서 기준 리뷰 |
| 7 | QA Reviewer | `/review-qa` | QA 관점 크로스 체크 |
| 8 | TC Reviewer | `/review-tc` | TC 내용 리뷰 |
| 9 | Project Reporter | `/report-project` | 프로젝트 현황 보고 |
| 10 | Bug Reporter | `/report-bug` | JIRA 버그 리포팅 |
| 11 | Impact Analyzer | `/analyze-impact` | 크로스 프로젝트 영향도 |
| 12 | Rule Learner | `/learn-rules` | 리뷰 패턴 학습 |
| 13 | Automation Assessor | `/assess-automation` | 자동화 사전 검토 |
| 14 | Test Coder | `/write-test-code` | 자동화 코드 작성 |
| 15 | Fail Analyzer | `/analyze-fail` | FAIL 원인 분석 |

## 파일 구조

```
플러그인 (레포):
├── .claude-plugin/          ← 플러그인 설정
├── .claude/
│   ├── CLAUDE.md            ← 프로젝트 지침
│   └── skills/              ← 스킬 정의
└── README.md

로컬 (/init 생성):
├── config/                  ← 공통/프로젝트별 설정
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
