---
name: share-slack
description: 테스트 결과를 Slack 채널로 공유하는 코드를 생성합니다.
---

# /share-slack

> 테스트 결과를 Slack 채널로 공유하는 코드를 생성합니다.

---

## 1. 개요

테스트 실행 후 결과를 Slack Webhook을 통해 팀 채널에 공유하는 Python 코드를 생성합니다.

---

## 2. 입력 파일

| 파일 | 용도 | 필수 |
|------|------|------|
| `data/test_results.json` | pytest 실행 결과 (함수 단위) | O |
| `data/checklist_results.json` | 체크리스트 결과 (체크 단위) | X |
| `data/confluence_report_url.txt` | Confluence 리포트 URL | X |
| `tests/version_info.json` | 버전 정보 | X |

---

## 3. 환경 변수 (.env)

```
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/xxx/xxx/xxx
```

---

## 4. 메시지 구조

### 4.1 메인 텍스트 (항상 표시)

```
:mega: *[프로젝트명] 자동화 테스트 결과* (2026-01-29 16:34:44)
버전: `pc 1.2.0 | mobile 1.1.0`
Total: 50 | ✅ PASS: 45 | ❌ FAIL: 3 | ⚪ SKIP: 2
📈 성공률: 90.0%
:stopwatch: 전체 수행 시간: 24분 53초
```

### 4.2 링크 섹션

```
*📎 링크 바로가기*
• <URL|Confluence 상세 리포트>
```

### 4.3 Attachment (자동 접힘)

파일별 상세 결과는 Slack attachment로 전송하여 "자세히 표시" 기능 적용:

```
📂 파일별 상세 결과
━━━━━━━━━━━━━━━━━━
*로그인/로그아웃 확인*
   └ ✅ 이메일 입력 확인
   └ ✅ 비밀번호 입력 확인
   └ ❌ 로그인 버튼 클릭

*고객 선택 확인*
   └ ✅ 고객 검색
   └ ⚪ 고객 선택 (스킵)
```

---

## 5. 코드 구조

```python
import os
import json
import requests
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv

load_dotenv(override=True)

SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")
KST = timezone(timedelta(hours=9))

# === 데이터 로드 함수 ===

def load_test_results(file_path="data/test_results.json"):
    """테스트 결과 로드"""
    if not os.path.exists(file_path):
        return []
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def load_confluence_url(file_path="data/confluence_report_url.txt"):
    """Confluence 리포트 URL 로드"""
    if not os.path.exists(file_path):
        return None
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read().strip()

def load_version(file_path="tests/version_info.json"):
    """버전 정보 로드"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return f"pc {data.get('pc_version', '-')} | mobile {data.get('mobile_version', '-')}"
    except:
        return "버전 정보 없음"

# === 메시지 구성 ===

def format_duration(total_seconds):
    """초를 '분 초' 형식으로 변환"""
    minutes = int(total_seconds // 60)
    seconds = int(total_seconds % 60)
    return f"{minutes}분 {seconds}초"

def build_slack_message(test_results, confluence_url):
    """슬랙 메시지 구성"""
    version = load_version()

    # 통계 계산
    success_count = sum(1 for r in test_results if r.get("status") == "PASS")
    fail_count = sum(1 for r in test_results if r.get("status") == "FAIL")
    skip_count = sum(1 for r in test_results if r.get("status") == "SKIP")
    total = len(test_results)
    success_rate = (success_count / total * 100) if total > 0 else 0

    # 수행 시간 계산
    total_duration = sum(float(r.get("duration", "0").replace("초", "")) for r in test_results)

    # 메인 텍스트
    now = datetime.now(KST).strftime("%Y-%m-%d %H:%M:%S")
    main_text = f":mega: *[프로젝트명] 자동화 테스트 결과* ({now})\n"
    main_text += f"버전: `{version}`\n"
    main_text += f"Total: {total} | ✅ PASS: {success_count} | ❌ FAIL: {fail_count} | ⚪ SKIP: {skip_count}\n"
    main_text += f"📈 성공률: {success_rate:.1f}%\n"
    main_text += f":stopwatch: 전체 수행 시간: {format_duration(total_duration)}\n"

    # 링크 섹션
    if confluence_url:
        main_text += f"\n*📎 링크 바로가기*\n• <{confluence_url}|Confluence 상세 리포트>\n"

    # 파일별 상세 결과 (attachment용)
    grouped = {}
    for r in test_results:
        file_name = os.path.basename(r.get("file", ""))
        grouped.setdefault(file_name, []).append(r)

    detail_text = ""
    for file_name, tests in grouped.items():
        detail_text += f"*{file_name}*\n"
        for t in tests:
            status = t.get("status", "")
            test_name = t.get("test_name", "")
            icon = {"PASS": "✅", "FAIL": "❌", "SKIP": "⚪"}.get(status, "")
            detail_text += f"   └ {icon} {test_name}\n"
        detail_text += "\n"

    return {
        "main_text": main_text,
        "detail_text": detail_text,
        "fail_count": fail_count
    }

# === 슬랙 전송 ===

def send_slack_message(message_data):
    """슬랙 메시지 전송 (attachment 사용)"""
    if not SLACK_WEBHOOK_URL:
        print("⚠️ SLACK_WEBHOOK_URL 설정 없음")
        return False

    main_text = message_data.get("main_text", "")
    detail_text = message_data.get("detail_text", "")
    fail_count = message_data.get("fail_count", 0)

    # 실패 있으면 빨강, 없으면 초록
    color = "#dc3545" if fail_count > 0 else "#28a745"

    payload = {
        "text": main_text,
        "attachments": [
            {
                "color": color,
                "title": "📂 파일별 상세 결과",
                "text": detail_text,
                "mrkdwn_in": ["text"]
            }
        ]
    }

    try:
        response = requests.post(SLACK_WEBHOOK_URL, json=payload)
        if response.status_code == 200:
            print("✅ 슬랙 알림 전송 완료")
            return True
        else:
            print(f"❌ 슬랙 전송 실패: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 슬랙 전송 오류: {e}")
        return False

# === 메인 실행 ===

if __name__ == "__main__":
    test_results = load_test_results()
    confluence_url = load_confluence_url()

    message_data = build_slack_message(test_results, confluence_url)
    send_slack_message(message_data)
```

---

## 6. 핵심 규칙

### Slack Webhook

- **Webhook URL**: `.env`의 `SLACK_WEBHOOK_URL` 사용
- **전송 방식**: `requests.post(url, json=payload)`
- **Attachment**: 긴 내용은 attachment로 분리하여 자동 접힘 적용
- **색상**: 실패 있으면 빨강(`#dc3545`), 전체 성공이면 초록(`#28a745`)

### 메시지 포맷

- **링크**: `<URL|텍스트>` 형식
- **굵게**: `*텍스트*`
- **코드**: `` `텍스트` ``
- **이모지**: `:emoji_name:` 또는 유니코드 직접 사용

---

## 7. 확장 옵션

프로젝트 필요에 따라 추가 가능:

| 기능 | 설명 |
|------|------|
| 테스트명 한글 매핑 | `test_name_mapping` 딕셔너리로 한글 표시 |
