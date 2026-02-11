---
name: upload-report
description: 테스트 결과 리포트를 Confluence 페이지로 업로드하는 코드를 생성합니다.
---

# /upload-report

> 테스트 결과 리포트를 Confluence 페이지로 업로드하는 코드를 생성합니다.

---

## 1. 개요

테스트 실행 결과를 Confluence REST API를 통해 새 페이지로 생성합니다.
생성된 페이지 URL은 파일로 저장하여 Slack 공유 시 활용합니다.

---

## 2. 입력 파일

| 파일 | 용도 | 우선순위 |
|------|------|----------|
| `data/checklist_results.json` | 체크리스트 결과 (체크 단위) | 1순위 |
| `data/test_results.json` | pytest 실행 결과 (함수 단위) | 2순위 (fallback) |
| `tests/version_info.json` | 버전 정보 | - |

---

## 3. 출력 파일

| 파일 | 용도 |
|------|------|
| `data/confluence_report_url.txt` | 생성된 페이지 URL 저장 |

---

## 4. 환경 변수 (.env)

```
CONFLUENCE_URL=https://your-domain.atlassian.net/wiki
CONFLUENCE_EMAIL=your-email@example.com
CONFLUENCE_API_TOKEN=your-api-token
CONFLUENCE_SPACE_KEY=SPACE
CONFLUENCE_PARENT_PAGE_ID=123456789
```

---

## 5. 리포트 형식

### 5.1 페이지 제목

```
[프로젝트명] {버전} 자동화 테스트 결과 - {날짜} {시간}
```

예: `[SAY] STG-1.2.0 자동화 테스트 결과 - 2026-01-29 16:34:44`

### 5.2 요약 섹션

```html
<table>
  <tr><th>상태</th><th>개수</th></tr>
  <tr><td>✅ 통과</td><td>232</td></tr>
  <tr><td>❌ 실패</td><td>7</td></tr>
  <tr><td>🔵 건너뜀</td><td>3</td></tr>
  <tr><td><strong>전체</strong></td><td><strong>242</strong></td></tr>
  <tr><td><strong>통과율</strong></td><td><strong>95.9%</strong></td></tr>
</table>
```

### 5.3 상세 결과 섹션 (리스트 형식)

```html
<h3>✅ 로그인/로그아웃 확인</h3>
<h4>✅ test_login (52/53)</h4>
<ul>
  <li>✅ 이메일 입력란 노출</li>
  <li>✅ 비밀번호 입력란 노출</li>
  <li>❌ 로그인 버튼 클릭 <em>(버튼 미노출)</em></li>
  <li>🔵 로딩 아이콘 확인</li>
</ul>
```

**상태 이모지:**
- ✅ PASS
- ❌ FAIL (에러 메시지 포함)
- 🔵 SKIP

---

## 6. 코드 구조

```python
import os
import json
import html
import requests
from datetime import datetime
from requests.auth import HTTPBasicAuth
from dotenv import load_dotenv

load_dotenv(override=True)

CONFLUENCE_URL = os.getenv("CONFLUENCE_URL")
CONFLUENCE_EMAIL = os.getenv("CONFLUENCE_EMAIL")
CONFLUENCE_API_TOKEN = os.getenv("CONFLUENCE_API_TOKEN")
CONFLUENCE_SPACE_KEY = os.getenv("CONFLUENCE_SPACE_KEY")
CONFLUENCE_PARENT_PAGE_ID = os.getenv("CONFLUENCE_PARENT_PAGE_ID")

# === 데이터 로드 ===

def load_checklist_results(file_path="data/checklist_results.json"):
    """체크리스트 결과 로드 (우선)"""
    if not os.path.exists(file_path):
        return None
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)

def load_test_results(file_path="data/test_results.json"):
    """테스트 결과 로드 (fallback)"""
    if not os.path.exists(file_path):
        return []
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)

def load_version(file_path="tests/version_info.json"):
    """버전 정보 로드"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("pc_version", "버전 정보 없음")
    except:
        return "버전 정보 없음"

# === 콘텐츠 생성 ===

def build_confluence_content(checklist_data):
    """
    체크리스트 데이터 기반 Confluence 콘텐츠 생성 (Storage Format)
    """
    # 전체 통계 계산
    total_checks = 0
    passed_checks = 0
    failed_checks = 0
    skipped_checks = 0

    for test in checklist_data:
        for step in test.get("steps", []):
            for check in step.get("checks", []):
                total_checks += 1
                status = check.get("status", "")
                if status == "PASS":
                    passed_checks += 1
                elif status == "FAIL":
                    failed_checks += 1
                elif status == "SKIP":
                    skipped_checks += 1

    success_rate = (passed_checks / total_checks * 100) if total_checks > 0 else 0

    # Storage Format HTML
    content = f"""
<ac:structured-macro ac:name="info">
  <ac:rich-text-body>
    <p><strong>📊 요약</strong></p>
  </ac:rich-text-body>
</ac:structured-macro>

<table>
  <thead>
    <tr><th>상태</th><th>개수</th></tr>
  </thead>
  <tbody>
    <tr><td>✅ 통과</td><td>{passed_checks}</td></tr>
    <tr><td>❌ 실패</td><td>{failed_checks}</td></tr>
    <tr><td>🔵 건너뜀</td><td>{skipped_checks}</td></tr>
    <tr><td><strong>전체</strong></td><td><strong>{total_checks}</strong></td></tr>
    <tr><td><strong>통과율</strong></td><td><strong>{success_rate:.1f}%</strong></td></tr>
  </tbody>
</table>

<h2>📋 테스트 결과 상세</h2>
"""

    # 파일별 그룹핑
    grouped_by_file = {}
    for test in checklist_data:
        file_name = test.get("file_name") or "기타"
        if file_name not in grouped_by_file:
            grouped_by_file[file_name] = []
        grouped_by_file[file_name].append(test)

    # 각 파일별 섹션 생성
    for file_name, tests in grouped_by_file.items():
        # 파일별 통계
        file_failed = sum(1 for t in tests if t.get("status") != "PASS")
        file_icon = "✅" if file_failed == 0 else "❌"

        content += f"<h3>{file_icon} {html.escape(file_name)}</h3>\n"

        # 각 테스트별 체크항목 표시
        for test in tests:
            test_name = test.get("test_name", "Unknown")
            test_status = test.get("status", "UNKNOWN")

            # 체크 통계
            check_passed = 0
            check_total = 0
            for step in test.get("steps", []):
                for check in step.get("checks", []):
                    check_total += 1
                    if check.get("status") == "PASS":
                        check_passed += 1

            test_icon = "✅" if test_status == "PASS" else "❌"
            content += f"<h4>{test_icon} {html.escape(test_name)} ({check_passed}/{check_total})</h4>\n<ul>\n"

            # 체크 항목 나열
            for step in test.get("steps", []):
                for check in step.get("checks", []):
                    check_name = check.get("name", "")
                    check_status = check.get("status", "")
                    check_error = check.get("error", "")

                    icon = {"PASS": "✅", "FAIL": "❌", "SKIP": "🔵"}.get(check_status, "")
                    error_info = f" <em>({html.escape(check_error)})</em>" if check_error else ""

                    content += f"  <li>{icon} {html.escape(check_name)}{error_info}</li>\n"

            content += "</ul>\n"

    return content

# === Confluence API ===

def create_confluence_page(title, content):
    """Confluence 페이지 생성"""
    url = f"{CONFLUENCE_URL}/rest/api/content"

    payload = {
        "type": "page",
        "title": title,
        "space": {"key": CONFLUENCE_SPACE_KEY},
        "body": {
            "storage": {
                "value": content,
                "representation": "storage"
            }
        }
    }

    if CONFLUENCE_PARENT_PAGE_ID:
        payload["ancestors"] = [{"id": CONFLUENCE_PARENT_PAGE_ID}]

    try:
        response = requests.post(
            url,
            json=payload,
            auth=HTTPBasicAuth(CONFLUENCE_EMAIL, CONFLUENCE_API_TOKEN),
            headers={"Content-Type": "application/json"}
        )

        if response.status_code == 200:
            page_data = response.json()
            page_id = page_data.get("id")
            page_url = f"{CONFLUENCE_URL}/pages/viewpage.action?pageId={page_id}"
            print(f"✅ Confluence 페이지 생성 완료: {page_url}")
            return page_url
        else:
            print(f"❌ 생성 실패: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"❌ 업로드 오류: {e}")
        return None

# === 메인 실행 ===

def upload_test_report():
    """테스트 결과를 Confluence에 업로드"""
    version = load_version()

    # 체크리스트 우선
    checklist_data = load_checklist_results()
    if not checklist_data:
        print("⚠️ checklist_results.json 없음")
        return None

    # 페이지 제목
    now = datetime.now()
    title = f"[프로젝트명] {version} 자동화 테스트 결과 - {now.strftime('%Y-%m-%d %H:%M:%S')}"

    # 콘텐츠 생성
    content = build_confluence_content(checklist_data)

    # 페이지 생성
    page_url = create_confluence_page(title, content)

    if page_url:
        # URL 저장 (Slack 공유용)
        with open("data/confluence_report_url.txt", "w", encoding="utf-8") as f:
            f.write(page_url)
        print(f"📊 리포트 URL 저장 완료")

    return page_url

if __name__ == "__main__":
    upload_test_report()
```

---

## 7. 핵심 규칙

### Confluence Storage Format

- **마크다운 사용 금지**: Confluence는 Storage Format HTML 사용
- **HTML 이스케이프 필수**: `html.escape()` 사용
- **representation**: 항상 `"storage"` 지정

### REST API 인증

```python
from requests.auth import HTTPBasicAuth

auth = HTTPBasicAuth(CONFLUENCE_EMAIL, CONFLUENCE_API_TOKEN)
```

### 페이지 생성 vs 업데이트

| 작업 | 메서드 | 엔드포인트 |
|------|--------|------------|
| 생성 | POST | `/rest/api/content` |
| 업데이트 | PUT | `/rest/api/content/{pageId}` |

업데이트 시 현재 버전 번호 조회 후 +1 해서 전송 필요.

---

## 8. 확장 옵션

| 기능 | 설명 |
|------|------|
| 테스트명 한글 매핑 | `test_name_mapping` 딕셔너리로 한글 표시 |
| 기존 페이지 업데이트 | 동일 제목 페이지 찾아서 업데이트 |
