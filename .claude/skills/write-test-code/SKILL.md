---
name: write-test-code
description: TC 또는 시나리오를 기반으로 pytest + playwright 자동화 테스트 코드를 생성합니다. TC JSON 파일 경로 또는 시나리오 파일 경로를 전달하세요.
argument-hint: "[TC 파일 경로 또는 시나리오 파일 경로]"
---

# 테스트 코드 생성

입력: $ARGUMENTS

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
