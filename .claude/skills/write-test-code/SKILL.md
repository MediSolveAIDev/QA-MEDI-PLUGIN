---
name: write-test-code
description: TC 또는 시나리오를 기반으로 pytest + playwright 자동화 테스트 코드를 생성합니다. TC JSON 파일 경로 또는 시나리오 파일 경로를 전달하세요.
argument-hint: "[TC 파일 경로 또는 시나리오 파일 경로]"
---

# 테스트 코드 생성

입력: $ARGUMENTS

> **본 스킬은 `.claude/rules/tc_writing_rule.md` 규칙을 따른다.**
> TC JSON 구조: `category_l1/l2/l3` + `precondition` + `step` + `expected` (분해된 행 = 한 TC = 한 검증).
> - TC ID 형식: `<도메인>-<L2약어>-<NNN>` (예: `RSV-FLT-001`) → 테스트 함수명에 사용 가능
> - 한 TC = 한 pytest 함수 (분해된 각 행이 독립 TC)
> - `precondition` → fixture, `step` → action, `expected` → assert
> - 분해 행 사전조건 누적(옵션 A) 적용된 상태라 각 TC가 자기 충족적

---

## 0. 선행 탐색 (코드 생성 전 필수)

코드 생성 전 대상 프로젝트의 기존 구조를 탐색한다.

### 0.1 기존 테스트 파일 확인 + 고도화 판단
- 대상 프로젝트의 `tests/` 폴더를 탐색하여 관련 기존 파일 확인
- **동일 기능의 테스트 파일이 이미 존재하면** → 기존 파일에 함수 추가/수정 (신규 생성 금지)
- **없으면** → 신규 파일 생성

**기존 파일이 있을 때 고도화 판단 절차:**

1. **TC 매핑 비교**: 새 TC 목록과 기존 테스트 함수를 1:1 대조
   - TC는 있는데 함수가 없음 → 함수 신규 추가
   - TC와 함수가 있지만 TC 내용이 변경됨 → 기존 함수 수정
   - TC가 삭제됨 → 기존 함수 deprecated 처리 (즉시 삭제 금지, 주석으로 표기)
2. **셀렉터 점검**: 기존 함수의 셀렉터가 현재 UI와 불일치 → 셀렉터 업데이트
3. **하드코딩 점검**: 기존 함수에 하드코딩된 URL, 테스트 데이터 → 환경변수/fixture로 전환
4. **패턴 점검**: `bare assert` 사용, `time.sleep` 남용 등 → soft_* 함수, 명시적 대기로 전환

### 0.2 기존 헬퍼 유틸리티 확인 + 신규 유틸 판단
- `helpers/` 폴더의 기존 유틸리티 함수(`*_utils.py`) 탐색
- 로그인, 페이지 이동, 데이터 세팅 등 반복 작업은 기존 함수 재사용
- 기존 파일 수정 시 import, fixture, 기존 함수와의 일관성 유지

**신규 유틸 함수 생성 기준:**

| 조건 | 액션 |
|------|------|
| 동일 로직이 **2개 이상** 테스트 함수에서 반복 | 유틸로 분리 |
| 1개 함수에서만 사용 | 분리하지 않음 (인라인 유지) |
| 기존 유틸과 유사하지만 파라미터만 다름 | 기존 유틸에 파라미터 추가 |

**유틸 카테고리 및 파일 네이밍:**

| 카테고리 | 파일명 | 예시 함수 |
|----------|--------|-----------|
| 인증 | `helpers/login_utils.py` | `login()`, `logout()`, `get_auth_token()` |
| 페이지 이동 | `helpers/page_utils.py` | `navigate_to()`, `wait_for_page()` |
| 데이터 세팅 | `helpers/data_utils.py` | `create_test_data()`, `cleanup_data()` |
| 공통 검증 | `helpers/assert_utils.py` | `check_toast_message()`, `check_modal()` |
| API 호출 | `helpers/api_utils.py` | `api_request()`, `setup_via_api()` |

> 기존 프로젝트에 다른 유틸 구조가 있으면 해당 구조를 따른다.

### 0.3 네이밍 컨벤션 확인
- 기존 `tests/` 폴더의 파일명 패턴을 확인하여 동일 패턴으로 생성
- 기존 파일이 없을 때만 아래 기본 규칙 사용

---

## 1. 저장 규칙

### 테스트 코드 저장 경로

**기본 규칙** (기존 파일이 없는 경우):
```
tests/test_{프로젝트}_{버전}_{기능}.py
```

**예시:**
- `tests/test_SAY_v3.2_로그인.py`
- `tests/test_BAY_v1.0_결제.py`
- `tests/test_SSO_v2.0_인증.py`

> 기존 프로젝트에 다른 네이밍 패턴이 있으면 해당 패턴을 따른다.

### 테스트 결과 저장 경로

모든 테스트 실행 결과는 `data/test_results/` 폴더에 저장:

```
data/test_results/
├── test_results.json              ← pytest 실행 결과 (Slack 알림용)
├── checklist_results.json         ← ChecklistReporter 결과 (Confluence 리포트용)
├── test_run_{timestamp}.json      ← 실행별 결과 아카이브
└── latest_test_results.json       ← 최신 결과 심볼릭
```

### data/ 폴더 전체 구조

```
data/
├── scenarios/       ← 시나리오 마크다운 (/write-scenario)
├── tc/              ← TC JSON (/write-tc)
└── test_results/    ← 테스트 실행 결과 (/write-test-code)
```

---

## 2. 테스트 구조 (AAA 패턴)

모든 테스트는 Arrange-Act-Assert 패턴을 따른다.

```python
def test_example(page: Page):
    # Arrange - 테스트 준비 (기존 헬퍼 우선 사용)
    page.goto(LOGIN_URL)

    # Act - 동작 수행
    page.fill("[data-testid='id-input']", "user@test.com")
    page.click("[data-testid='login-btn']")

    # Assert - 결과 검증
    assert page.locator("[data-testid='title-txt']").is_visible()
```

**Arrange 단계 규칙:**
- 기존 `helpers/` 유틸리티가 있으면 반드시 재사용 (예: `login_utils.login()`, `page_utils.navigate()`)
- 새 유틸리티가 필요하면 기존 `helpers/` 패턴에 맞춰 추가

---

## 3. 네이밍 규칙

### 기본 규칙 (기존 파일이 없는 경우)

```python
# 테스트 파일: test_{프로젝트}_{버전}_{기능}.py
test_SAY_v3.2_로그인.py
test_BAY_v1.0_결제.py
test_SSO_v2.0_인증.py

# 테스트 함수: test_{동작}_{조건}_{결과}
def test_login_with_valid_credentials_should_succeed():
def test_login_with_invalid_password_should_fail():
```

> 기존 프로젝트에 다른 네이밍 패턴이 있으면 해당 패턴을 따른다.

### test_name_mapping.py 업데이트

대상 프로젝트에 `helpers/test_name_mapping.py`가 존재하면, 테스트 파일/함수 추가 시 매핑도 함께 업데이트한다. 없으면 스킵.

```python
# helpers/test_name_mapping.py

# 파일명 매핑 — 테스트 파일 추가 시 항목 추가
test_name_mapping = {
    "test_pc_login.py": "[PC][로그인] 로그인 화면 테스트",
    # ← 새 파일 추가 시 여기에 매핑 추가
}

# 함수명 매핑 — 테스트 함수 추가 시 항목 추가
test_function_mapping = {
    "test_pc_login": "로그인/로그아웃 확인",
    # ← 새 함수 추가 시 여기에 매핑 추가
}
```

---

## 4. 셀렉터 우선순위

1. **data-testid** (최우선): `[data-testid='login-btn']`
2. **role + name**: `page.get_by_role("button", name="로그인")`
3. **text**: `page.get_by_text("로그인")`
4. **CSS selector** (최후): `.login-button`

---

## 5. 대기 전략

### 명시적 대기 (권장)
```python
# 요소가 나타날 때까지 대기
page.wait_for_selector("[data-testid='title-txt']", state="visible")

# 네트워크 요청 완료 대기
page.wait_for_load_state("networkidle")

# 특정 URL로 이동 대기
page.wait_for_url("**/dashboard")
```

### 암시적 대기 (지양)
```python
import time
time.sleep(3)  # 꼭 필요한 경우만 사용
```

---

## 6. 테스트 데이터

### JSON 파일 활용
```python
import json
with open("data/customer.json") as f:
    data = json.load(f)
```

### 환경변수 활용
```python
import os
from dotenv import load_dotenv

load_dotenv()
BASE_URL = os.getenv("BASE_URL")
TEST_USER = os.getenv("TEST_USER")
```

---

## 7. Fixture 활용

conftest.py에 정의된 fixture 사용:

| Fixture | 용도 |
|---------|------|
| `page` | PC Chrome (마이크 허용) |
| `page_no_mic` | PC Chrome (마이크 미허용) |
| `mobile_page` | 모바일 Chrome |
| `playwright` | Playwright 직접 접근 (멀티 브라우저) |

---

## 8. Soft Assertion (ChecklistReporter 패턴)

**목적:** 테스트 중 실패(Fail)나 예외 발생 시 테스트가 자동 종료되지 않고, 이후 단계를 모두 실행한 뒤 최종 결과를 집계한다.

### 8.1 기본 구조

```python
from helpers.checklist_reporter import (
    ChecklistReporter, step,
    soft_expect, soft_check, soft_click, soft_fill, soft_wait, soft_action
)

def test_login(page: Page):
    reporter = ChecklistReporter("test_login", "test_pc_login.py")

    try:
        page.goto(URLS["login"])

        with step(reporter, "로그인 화면 UI 확인"):
            soft_expect(reporter, page.locator('[data-testid="id-input"]'), "to_be_visible", "이메일 입력란 노출")
            soft_expect(reporter, page.locator('[data-testid="pw-input"]'), "to_be_visible", "비밀번호 입력란 노출")
            soft_expect(reporter, page.locator('[data-testid="login-btn"]'), "to_be_visible", "로그인 버튼 노출")

        with step(reporter, "정상 로그인"):
            soft_fill(reporter, page.locator('[data-testid="id-input"]'), "user@test.com", "이메일 입력")
            soft_fill(reporter, page.locator('[data-testid="pw-input"]'), "password", "비밀번호 입력")
            soft_click(reporter, page.locator('[data-testid="login-btn"]'), "로그인 버튼 클릭")
            soft_wait(reporter, page, '[data-testid="home"]', "홈 화면 진입 확인")

    finally:
        result = reporter.finish()
        if reporter.has_failure:
            pytest.fail(f"체크리스트 실패 항목 있음: {result['summary']}")
```

### 8.2 Soft 함수 목록

| 함수 | 용도 | 반환값 |
|------|------|--------|
| `soft_expect(reporter, locator, method, name)` | Playwright expect 검증 | `bool` |
| `soft_check(reporter, condition, name)` | 조건 True/False 검증 | `bool` |
| `soft_click(reporter, locator, name)` | 클릭 (실패해도 계속) | `bool` |
| `soft_fill(reporter, locator, value, name)` | 입력 (실패해도 계속) | `bool` |
| `soft_wait(reporter, page, selector, name)` | 대기 (실패해도 계속) | `bool` |
| `soft_action(reporter, callable, name)` | 임의 함수 실행 | `(bool, Any)` |

### 8.3 soft_expect 사용 예시

```python
# to_be_visible - 요소 노출 확인
soft_expect(reporter, page.locator('[data-testid="btn"]'), "to_be_visible", "버튼 노출")

# to_have_text - 텍스트 확인
soft_expect(reporter, title, "to_have_text", "제목 확인", expected="Hello")

# to_be_enabled - 활성화 확인
soft_expect(reporter, button, "to_be_enabled", "버튼 활성화")

# to_have_count - 개수 확인
soft_expect(reporter, items, "to_have_count", "항목 3개", count=3)
```

### 8.4 step 컨텍스트 매니저

`step()`으로 테스트를 논리적 단위로 묶는다. Step 내 하나라도 FAIL이면 해당 Step은 FAIL로 기록되지만, **다음 Step은 계속 실행**된다.

```python
with step(reporter, "1. 화면 진입"):
    # 이 안에서 실패해도 다음 step으로 진행
    soft_expect(reporter, ...)

with step(reporter, "2. 데이터 입력"):
    soft_fill(reporter, ...)
    soft_click(reporter, ...)

with step(reporter, "3. 결과 확인"):
    soft_expect(reporter, ...)
```

### 8.5 결과 집계

`reporter.finish()` 호출 시:
- Step별 PASS/FAIL/SKIP 집계
- `data/test_results/checklist_results.json`에 자동 저장
- 콘솔에 요약 출력

```
==================================================
[test_login] 테스트 완료
Steps: 3 | ✅ 2 | ❌ 1 | ⏭️ 0
Duration: 12.34초
==================================================
```

### 8.6 핵심 규칙

- 모든 검증은 `soft_*` 함수 사용 (bare `assert` 사용 금지)
- `try/finally` 블록으로 감싸서 예외 발생 시에도 `reporter.finish()` 호출 보장
- `reporter.has_failure`로 최종 실패 여부 판단 후 `pytest.fail()` 호출
- Step 이름은 테스트 흐름을 나타내는 한글 사용

### 8.7 예외 발생 시 리포트 처리

테스트 중 예상치 못한 예외(TimeoutError, 네트워크 오류 등)가 발생해도 **리포트에 기록**되어야 한다.

```python
def test_example(page: Page):
    reporter = ChecklistReporter("test_example", "test_pc_example.py")

    try:
        with step(reporter, "1. 화면 진입"):
            soft_expect(reporter, ...)

        with step(reporter, "2. 동작 수행"):
            soft_click(reporter, ...)
            # 여기서 예상치 못한 예외 발생 시 → except로 이동

        with step(reporter, "3. 결과 확인"):
            soft_expect(reporter, ...)

    except Exception as e:
        # 예외를 리포트에 FAIL로 기록
        reporter.fail_check(f"예외 발생: {type(e).__name__}", str(e)[:200])

    finally:
        # 반드시 finish() 호출하여 결과 저장
        result = reporter.finish()
        if reporter.has_failure:
            pytest.fail(f"체크리스트 실패 항목 있음: {result['summary']}")
```

**핵심 포인트:**
- `except Exception`에서 예외를 `reporter.fail_check()`으로 기록
- `finally`에서 `reporter.finish()`로 결과 저장 보장
- 예외가 발생한 시점까지의 모든 Step 결과가 리포트에 포함됨
- 예외로 인해 실행되지 못한 이후 Step은 리포트에 나타나지 않음 (정상 동작)

### 8.8 결과 데이터 이중 구조 (Slack vs 리포트)

테스트 실행 시 **두 가지 결과 파일**이 생성되며, 각각 다른 단위로 집계된다.

| 구분 | Slack 알림 | Confluence 리포트 |
|------|-----------|-------------------|
| **데이터 소스** | `data/test_results/test_results.json` (pytest) | `data/test_results/checklist_results.json` (ChecklistReporter) |
| **집계 단위** | 테스트 함수 단위 | 체크 항목(check) 단위 |
| **FAIL 기준** | 함수 내 1건이라도 실패 → 함수 전체 FAIL | 개별 check마다 PASS/FAIL 기록 |

**예시: 20개 체크 중 1개 실패한 테스트 함수**

```
Slack 결과:    ❌ test_pc_login — FAIL (1건)
리포트 결과:   test_pc_login — ✅ 19 / ❌ 1 (체크리스트 95% 통과)
```

**코드에서의 구조:**
```python
def test_login(page: Page):
    reporter = ChecklistReporter("test_login", "test_pc_login.py")
    try:
        # soft_expect → checklist_results.json에 개별 check 기록
        # 여기서 1개 실패해도 나머지 19개 계속 실행

    finally:
        result = reporter.finish()  # data/test_results/checklist_results.json 저장
        if reporter.has_failure:
            pytest.fail(...)        # pytest가 test_results.json에 FAIL 기록
```

**따라서 테스트 코드 작성 시:**
- `soft_*` 함수의 `check_name`이 리포트의 체크 항목명이 됨 → **구체적이고 명확하게** 작성
- `step()` 이름이 리포트의 섹션 구분이 됨 → **논리적 단위**로 묶기
- Slack에는 함수 단위만 보이므로, 함수명도 의미 있게 작성

---

## 9. 테스트 안정성

- 각 테스트는 독립적으로 실행 가능해야 함
- 테스트 간 데이터 의존성 최소화
- 테스트 후 데이터 정리 (cleanup)
- Flaky 테스트 방지를 위한 적절한 대기
- 네트워크 불안정 대비 재시도 로직
- 타임아웃 설정

---

## 10. 마커 활용

```python
import pytest

@pytest.mark.smoke
@pytest.mark.high
def test_login_success(page):
    ...

@pytest.mark.regression
@pytest.mark.low
def test_login_placeholder(page):
    ...
```

사용 가능한 마커: ui, functional, user_scenario, exception, performance, high, medium, low, smoke, regression

---

## 11. 테스트 실행 파일 (run_tests)

전체 테스트를 한 번에 실행하는 엔트리포인트 스크립트를 구성한다.

### 11.1 기본 구조

```python
# run_tests.py (프로젝트 루트)
import subprocess
import sys
import os
from datetime import datetime

def run_tests(marker=None, parallel=False, headed=False):
    """pytest 실행 래퍼"""
    cmd = [
        sys.executable, "-m", "pytest",
        "tests/",
        "-v",
        "--tb=short",
        f"--json-report-file=data/test_results/test_results.json",
    ]

    if marker:
        cmd += ["-m", marker]
    if parallel:
        cmd += ["-n", "auto"]  # pytest-xdist
    if headed:
        cmd += ["--headed"]

    # 환경변수로 headless 제어
    if not headed:
        os.environ["PLAYWRIGHT_HEADLESS"] = "1"

    print(f"[{datetime.now()}] 테스트 실행: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=False)
    return result.returncode

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--marker", "-m", help="pytest 마커 (smoke, regression 등)")
    parser.add_argument("--parallel", "-p", action="store_true", help="병렬 실행")
    parser.add_argument("--headed", action="store_true", help="브라우저 표시")
    args = parser.parse_args()

    exit_code = run_tests(marker=args.marker, parallel=args.parallel, headed=args.headed)
    sys.exit(exit_code)
```

### 11.2 실행 예시

```bash
# 전체 실행
python run_tests.py

# smoke 테스트만
python run_tests.py -m smoke

# 병렬 실행
python run_tests.py -p

# 브라우저 표시 (디버깅)
python run_tests.py --headed
```

### 11.3 필수 설정 파일

**pytest.ini 또는 pyproject.toml:**
```ini
[pytest]
markers =
    smoke: 핵심 기능 검증
    regression: 회귀 테스트
    high: 우선순위 높음
    medium: 우선순위 보통
    low: 우선순위 낮음
testpaths = tests
addopts = --tb=short -v
timeout = 300
```

**conftest.py 필수 항목:**
- `page` fixture (Playwright 브라우저 세션)
- `base_url` fixture (환경변수에서 읽기)
- pytest-json-report 플러그인 설정
- ChecklistReporter 결과 저장 경로 설정

---

## 12. GitHub Actions 워크플로

### 12.1 워크플로 파일 템플릿

```yaml
# .github/workflows/test.yml
name: Run Tests

on:
  workflow_dispatch:
    inputs:
      marker:
        description: "pytest 마커 (smoke, regression, 빈값=전체)"
        required: false
        default: ""
      project:
        description: "프로젝트 (SAY, BAY, SSO)"
        required: true

jobs:
  test:
    runs-on: ubuntu-latest
    timeout-minutes: 30

    steps:
      - uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          playwright install chromium
          playwright install-deps

      - name: Run tests
        env:
          BASE_URL: ${{ secrets.BASE_URL }}
          TEST_USER: ${{ secrets.TEST_USER }}
          TEST_PASSWORD: ${{ secrets.TEST_PASSWORD }}
          PLAYWRIGHT_HEADLESS: "1"
        run: |
          if [ -n "${{ inputs.marker }}" ]; then
            python run_tests.py -m "${{ inputs.marker }}"
          else
            python run_tests.py
          fi

      - name: Upload results
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: test-results-${{ inputs.project }}
          path: data/test_results/
          retention-days: 30
```

### 12.2 GitHub Secrets 매핑

| `.env` 변수 | GitHub Secret | 용도 |
|-------------|---------------|------|
| `BASE_URL` | `BASE_URL` | 테스트 대상 URL |
| `TEST_USER` | `TEST_USER` | 테스트 계정 ID |
| `TEST_PASSWORD` | `TEST_PASSWORD` | 테스트 계정 PW |
| `CONFLUENCE_API_TOKEN` | `CONFLUENCE_API_TOKEN` | Confluence 업로드 |
| `SLACK_WEBHOOK_URL` | `SLACK_WEBHOOK_URL` | Slack 알림 |

> `.env` 파일은 로컬 전용. GitHub Actions에서는 반드시 Secrets 사용.

---

## 13. GitHub Actions 실행 주의사항

### 13.1 필수 규칙

| 항목 | 규칙 |
|------|------|
| 브라우저 모드 | **headless 필수** (`PLAYWRIGHT_HEADLESS=1`). headed는 CI에서 불가 |
| 타임아웃 | job 레벨 `timeout-minutes: 30` + pytest 레벨 `timeout=300` (개별 테스트 5분) |
| 아티팩트 | `always()` 조건으로 실패해도 결과 파일 업로드 |
| 시크릿 | `.env` 값을 GitHub Secrets로 1:1 매핑. 로그에 노출 금지 |
| 재시도 | Flaky 테스트는 `pytest-rerunfailures` 사용 (`--reruns 2 --reruns-delay 3`) |

### 13.2 Flaky 테스트 대응

```yaml
# 재시도 옵션 추가
run: python -m pytest tests/ --reruns 2 --reruns-delay 3
```

- 최대 2회 재시도, 재시도 간 3초 대기
- 재시도 후에도 실패하면 FAIL 확정

### 13.3 병렬 실행 시 주의

- `pytest-xdist` 사용 시 테스트 간 데이터 충돌 방지 필수
- 같은 계정으로 동시 로그인 불가 → 테스트 계정을 분리하거나 순차 실행
- ChecklistReporter 결과 파일 쓰기 충돌 → 병렬 시 파일명에 worker ID 포함

### 13.4 디버깅

- 실패 시 스크린샷 자동 저장: `page.screenshot(path=f"data/test_results/fail_{test_name}.png")`
- 아티팩트로 스크린샷 함께 업로드
- GitHub Actions 로그에서 pytest 출력 확인

---

## 14. 코드 품질 원칙 (디버깅 친화 + 중복 최소화)

테스트 코드 작성 시 처음부터 다음 11개 원칙을 모두 따른다. 일부만 적용하고 "안정화 후 리팩터링"하면 누적 비용이 크다. SKILL 은 신규 코드의 prescription 이므로 day 1 부터 11 개 모두 적용한다.

### 14.1 디버깅 시간 단축 (D1 ~ D6)

#### D1. 검증 메시지에 실제 값 포함

모든 검증(`soft_check` / `soft_expect` / `assert` / 로그) 메시지를 f-string 으로 작성하고 입력값·실제 값·기대 값을 메시지에 포함한다. 실패 시 화면 재현 없이 원인 추적 가능해야 한다.

```python
# ❌ 결과만 보고 원인 모름
soft_check(reporter, found, "값 확인")

# ✅ 실패 시 실제 값으로 즉시 진단
soft_check(reporter, found, f"값 확인 (actual={actual}, expected={expected})")
```

#### D2. step 에 식별자 + 의미 라벨 부여

모든 step 이름은 `TC-ID: 한글 의미` 형식으로 작성한다. 실패 로그에서 TC 매핑 + 의미가 즉시 파악된다.

```python
with step(reporter, "TC-001a: 입력 필드 노출 확인"):
    ...
```

#### D3. 데이터 variant 별 step 분리

같은 검증을 다른 variant(입력 종류·권한·환경·디바이스·상태 등)에 적용할 때, 한 step 에 여러 variant 를 욱여넣지 않는다. 분리하면 어느 variant 에서 깨졌는지 즉시 식별된다.

```python
# ❌ 어느 케이스에서 실패했는지 추적 불가
with step(reporter, "TC-001: 입력 필드 검증"):
    for variant in [...]: ...

# ✅ variant 별 step ID 분리
with step(reporter, "TC-001a: 단일 입력"):
    ...
with step(reporter, "TC-001b: 다중 입력"):
    ...
```

#### D4. 함수 길이·단일 책임 가이드 (~50 줄)

한 함수에 진입·검증·후처리·예외 분기를 섞지 않는다. ~50 줄 초과 또는 책임이 복합적이면 sub 함수로 분할한다. stack trace 에서 실패 위치가 즉시 보이도록 하는 것이 목표.

```python
# ❌ 단일 함수에 진입·폼 제출·예외 분기·검증이 섞임
def login(...): ...   # 100+ 줄

# ✅ 책임 단위 sub 함수로 분할
def login(...):
    _wait_for_login_page(page)
    _submit_login_form(page, id)
    _verify_login_success(page, id)
```

#### D5. 명시적 실패 + 컨텍스트 raise

미발견·예외를 silent 처리(`return None`, `pass`)하지 않는다. 원인·컨텍스트(검색어·인덱스·상태)를 메시지에 박아 raise 한다.

```python
# ❌ 호출자가 None 반환 원인 모름
if target is None:
    return None

# ✅ 원인 + 컨텍스트
if target is None:
    raise Exception(f"'{key}' 행을 찾을 수 없음 (검색어={query}, rows={count})")
```

#### D6. 검증 raw 데이터 보존

검증 실패 시 expected / actual / snapshot 을 결과 파일에 저장한다. 사후 분석 시 화면·DB 재현 없이 원인 분석 가능하도록.

```python
# 결과 저장기(ChecklistReporter 등)가 실패 시 raw 정보를 함께 기록
soft_expect(reporter, locator, "to_have_text", "제목 확인", expected="Hello")
# 실패 시 결과 JSON 에 actual="World", expected="Hello", raw=... 저장됨
```

---

### 14.2 코드 중복 최소화 (C1 ~ C5)

#### C1. 데이터 중앙화 — config / constants / fixtures

인라인 리터럴(URL·계정·라벨·메시지·임계값)을 테스트 코드에 박지 않는다. 모듈로 분리해 단일 소스로 관리한다.

```
config/
├── accounts.py    ← 계정·권한·이메일
├── urls.py        ← URL·라우트
├── messages.py    ← 토스트·알럿·라벨
└── test_data.py   ← 시드 데이터·임계값
```

```python
# ❌ 인라인
page.goto("https://stg.example.com/login")

# ✅ 단일 소스
from config import URLS
page.goto(URLS["login"])
```

#### C2. 헬퍼 분할 기준 강화

기존 0.2 의 "2 회 이상 반복 → 헬퍼" 기준에 다음을 추가한다.

- 단일 함수 ~50 줄 초과 → sub 분할 (D4 와 동일 원칙)
- 한 함수에 진입·검증·후처리가 섞이면 → 책임별 sub 분할
- 동일 로직이 자료구조만 달리 반복되면 → 일반 함수 + 인자로 분리

#### C3. spec / dict 기반 generic 검증 패턴

상태·조건·케이스별 if-elif 분기 대신 dict + 일반 함수로 정의한다. 새 케이스 추가 = dict 한 줄.

```python
# ❌ 케이스 추가 시 함수 분기 폭발
def check_buttons(state):
    if state == "pending":
        ...
    elif state == "approved":
        ...

# ✅ spec dict + 일반 함수
SPEC_MAP = {
    "pending":  {"submit_enabled": True,  "label": "처리 중"},
    "approved": {"submit_enabled": False, "label": "완료"},
}
def verify(row, spec):
    btn = row.locator("[data-testid=submit]")
    expect(btn).to_be_enabled() if spec["submit_enabled"] else expect(btn).to_be_disabled()
```

#### C4. 매직 상수 통합 모듈

대기 시간·자주 쓰는 정규식·임계값·반복 셀렉터를 한 모듈에 모은다. 튜닝 시 1 곳에서 통제.

```python
# helpers/timing.py
WAIT_SHORT      = 500
WAIT_MEDIUM     = 1500
WAIT_LONG       = 3000
TIMEOUT_DEFAULT = 5000
TIMEOUT_LONG    = 15000

# 호출 측 — 매직 넘버 박지 않기
page.wait_for_timeout(WAIT_MEDIUM)
```

#### C5. variant 그룹 상수화

데이터·권한·환경별 그룹을 의미 있는 상수로 묶는다. 결정성 확보 + 테스트 매트릭스 명시.

```python
# ❌ 매번 인덱스/문자열 박기
products = ["product_a", "product_b", "product_c"]

# ✅ 의미 있는 그룹 상수
ADMIN_ACCOUNTS    = [...]
INDIVIDUAL_INPUTS = [...]
BATCH_INPUTS      = [...]
MOBILE_VIEWPORTS  = [...]
```

---

### 14.3 위반 점검

새 코드 작성/리뷰 시 11 개 원칙 모두 점검:

| 원칙 | 점검 질문 |
|---|---|
| D1 | 검증 메시지에 실제 값이 들어 있나? |
| D2 | step 이름에 TC ID + 한글 라벨이 있나? |
| D3 | variant 별로 step 이 분리됐나? |
| D4 | 함수가 50 줄 넘거나 책임이 섞이지 않았나? |
| D5 | 미발견·예외를 silent 처리하지 않았나? |
| D6 | 검증 실패 시 raw 데이터가 결과에 저장되나? |
| C1 | 인라인 리터럴(URL·계정·라벨)이 남아 있지 않나? |
| C2 | 50 줄+ 함수가 sub 로 분할됐나? |
| C3 | 상태별 if-elif 분기가 spec dict 로 대체됐나? |
| C4 | 매직 넘버가 상수 모듈을 통해 사용되나? |
| C5 | variant 가 의미 있는 그룹 상수로 묶였나? |

---

## 15. 자동화 커버리지 리포트 (TC 기반 입력일 때만)

테스트 코드 작성 완료 시점에 **TC 기준 커버리지**를 산정하여 리포트를 출력한다.

### 15.0 적용 조건 (필수)

**TC JSON이 입력으로 사용된 경우에만 커버리지 산정**. 다음 조건에선 SKIP:

| 입력 | 커버리지 산정 |
|---|---|
| TC JSON 파일 (`data/tc/{...}_tc.json`) | ✓ 산정 |
| 시나리오 MD만 (TC 없음) | **SKIP** — TC가 없어 매핑 대상 없음 |
| Confluence Page / Figma 노드 (시나리오 입력) | **SKIP** |
| 혼합 (시나리오 + 일부 TC) | TC 있는 부분만 산정 |

**SKIP 시 동작**: 콘솔에 "TC JSON이 없어 커버리지 리포트를 생략합니다." 한 줄 출력. coverage.json 파일 생성 X.

### 15.1 산정 방식 (TC JSON 있을 때)

1. TC JSON에서 전체 TC 목록 추출 (`data/tc/{...}_tc.json`)
2. 작성된 테스트 파일 스캔 → 각 함수에 매핑된 TC ID 추출 (step 이름 또는 docstring에서 `TC-ID:` 토큰 검색)
3. TC ID 매칭으로 자동화 여부 판정
4. 영역별(L2 약어) / 우선순위별(P1/P2/P3) 분포 집계

### 15.2 출력 형식 (필수)

**JSON 저장**: `data/test_results/{프로젝트}_{버전}_{기능}_coverage.json`

```json
{
  "metadata": {
    "product": "DAY",
    "version": "v0.1.0",
    "feature": "예약관리",
    "abbreviation": "RSV",
    "tc_source": "data/tc/DAY_v0.1.0_예약관리_tc.json",
    "test_source": "tests/test_DAY_v0.1.0_예약관리.py",
    "generated_at": "2026-05-12T15:00:00"
  },
  "summary": {
    "total_tc": 39,
    "automated": 25,
    "coverage_pct": 64.1
  },
  "by_area": [
    {"l2_abbr": "ENT", "l2_name": "화면 진입", "total": 2, "automated": 2, "coverage_pct": 100.0},
    {"l2_abbr": "FLT", "l2_name": "좌측 필터 패널", "total": 10, "automated": 10, "coverage_pct": 100.0},
    {"l2_abbr": "STA", "l2_name": "상태 전이", "total": 8, "automated": 6, "coverage_pct": 75.0},
    {"l2_abbr": "CAL", "l2_name": "캘린더 뷰", "total": 6, "automated": 4, "coverage_pct": 66.7},
    {"l2_abbr": "REG", "l2_name": "예약 등록 슬라이드 패널", "total": 5, "automated": 3, "coverage_pct": 60.0},
    {"l2_abbr": "DTL", "l2_name": "예약 상세 패널", "total": 3, "automated": 0, "coverage_pct": 0.0},
    {"l2_abbr": "PRM", "l2_name": "권한 검증", "total": 2, "automated": 0, "coverage_pct": 0.0}
  ],
  "by_priority": [
    {"priority": "P1", "total": 20, "automated": 18, "coverage_pct": 90.0},
    {"priority": "P2", "total": 12, "automated": 6, "coverage_pct": 50.0},
    {"priority": "P3", "total": 7, "automated": 1, "coverage_pct": 14.3}
  ],
  "automated_tcs": ["RSV-ENT-001", "RSV-ENT-002", "RSV-FLT-001", "..."],
  "missing_tcs": [
    {"id": "RSV-STA-006", "priority": "P2", "l2": "상태 전이", "l3": "종료 상태 드롭다운"},
    {"id": "RSV-STA-007", "priority": "P2", "l2": "상태 전이", "l3": "종료 상태 드롭다운"},
    {"id": "RSV-CAL-005", "priority": "P1", "l2": "캘린더 뷰", "l3": "예약 카드 드래그 (당일)"},
    {"id": "RSV-DTL-001", "priority": "P1", "l2": "예약 상세/수정 슬라이드 패널", "l3": "환자 카드 클릭"}
  ]
}
```

**마크다운 요약 (콘솔 출력)**:

```
=== 자동화 커버리지 ===
대상: DAY v0.1.0 예약관리 (RSV)
총 TC: 39건 / 자동화: 25건 / 커버리지 64.1%

영역별:
  ENT 화면 진입         : 2/2  (100%)
  FLT 좌측 필터 패널    : 10/10 (100%)
  STA 상태 전이         : 6/8  (75%)
  CAL 캘린더 뷰         : 4/6  (66.7%)
  REG 예약 등록         : 3/5  (60%)
  DTL 예약 상세         : 0/3  (0%)  ← 미착수
  PRM 권한 검증         : 0/2  (0%)  ← 미착수

우선순위별:
  P1: 18/20 (90%)
  P2: 6/12  (50%)
  P3: 1/7   (14.3%)

미자동화 TC (14건):
  RSV-STA-006, RSV-STA-007, RSV-CAL-005, RSV-DTL-001, ...
```

### 15.3 시트 반영 (선택)

커버리지 JSON을 기반으로 시트에 자동화 여부 컬럼 갱신 가능. **별도 도구로 처리** (write-test-code 직접 호출 X):

| 옵션 | 처리 방식 |
|---|---|
| A. 시트에 "Auto" 컬럼 추가 | 자동화된 TC 행에 "✓" 또는 함수명 표시 |
| B. 비고 컬럼 활용 | 비고 컨벤션상 액션 필요 항목만이라 비추 |
| C. 시트 외부 통계만 보관 | JSON·HTML 리포트로 별도 관리 (기본 권장) |

→ **옵션 A 또는 C** 권장. 시트 컬럼 추가 시 기존 컬럼 매핑(init 스킬의 `COL_*`)도 함께 갱신 필요.

### 15.4 호출 시점

- `write-test-code` 실행 마지막 단계 (코드 작성 + lint 통과 후)
- Orchestrator의 Phase 3 (자동화) 종료 시점 자동 산정
- `report-project`에서 종합 보고서 작성 시 이 JSON 참조
