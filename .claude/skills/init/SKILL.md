# /init - 로컬 작업 환경 초기화

> 플러그인 설치 후 로컬에 폴더 구조와 템플릿 파일을 생성합니다.

---

## 1. 개요

- **역할**: 각 프로젝트 루트에 필요한 폴더 구조 + 기본 파일 생성
- **실행 시점**: 각 프로젝트에서 최초 1회 실행 (`/setup` 전에)
- **목표**: 현재 프로젝트 루트에 스킬이 산출물을 저장하고 설정을 읽을 수 있는 환경을 만든다

---

## 2. 실행

```
사용자: /init
```

---

## 3. 생성할 폴더 구조

현재 프로젝트 루트에 아래 구조를 생성한다. **이미 존재하는 폴더/파일은 건드리지 않는다.**

```
./                             ← 프로젝트 루트 (say-admin/, bay-admin/ 등)
├── config/
├── data/
│   ├── scenarios/
│   ├── tc/
│   ├── reviews/
│   ├── assessments/
│   ├── fail_analysis/
│   ├── bugs/
│   ├── rules/
│   ├── test_results/
│   └── pipeline/
├── figma_output/              ← Figma export 데이터 저장 (enrich-figma 스킬 참조)
├── tools/                     ← 유틸리티 스크립트
│   └── poll_sheet.py          ← 구글 시트 FAIL 폴링 스크립트 (report-bug 스킬 연동)
├── templates/
└── tests/
```

---

## 4. 생성할 파일

### 4.1 config/common.json (없을 때만 생성)

```json
{
  "jira": {
    "base_url": "",
    "email": ""
  },
  "confluence": {
    "base_url": ""
  },
  "figma": {
    "base_url": "https://api.figma.com"
  },
  "github": {
    "org": "MediSolveAIDev",
    "actions_repo": ""
  },
  "slack": {
    "webhook_url": ""
  },
  "env_file": {
    "_comment": "민감 정보는 .env에서 관리. 아래는 필요한 키 목록.",
    "required_keys": [
      "JIRA_API_TOKEN",
      "CONFLUENCE_API_TOKEN",
      "FIGMA_ACCESS_TOKEN",
      "SLACK_WEBHOOK_URL",
      "SLACK_WEBHOOK_APPROVAL"
    ]
  }
}
```

### 4.2 config/project.json (없을 때만 생성)

현재 프로젝트의 설정 파일. `/setup`에서 값을 채운다.

```json
{
  "name": "",
  "platform": "",
  "current_version": "",
  "jira": {
    "project_key": "",
    "board_id": ""
  },
  "confluence": {
    "space_key": "",
    "parent_page_id": "",
    "pages": {
      "scenarios": "",
      "test_cases": "",
      "reports": ""
    }
  },
  "figma": {
    "file_id": ""
  },
  "automation": {
    "test_repo": "",
    "script_path": "",
    "base_url": "",
    "framework": "pytest"
  },
  "features": {}
}
```

### 4.5 templates/figma_review_prompt.md (없을 때만 생성)

```markdown
# Figma 검수 가이드

> 이 문서는 Claude in Chrome이 Figma 화면과 시나리오를 대조 검수할 때 참고하는 가이드입니다.

---

## 검수 항목

현재 보이는 Figma 화면과 사용자가 제공한 시나리오를 대조하여 아래 항목을 확인하세요.

1. **UI 요소 누락**: 시나리오의 버튼, 입력 필드, 텍스트 등이 Figma에 모두 존재하는지
2. **문구 일치**: 레이블, placeholder, 토스트, Alert 문구가 Figma와 정확히 일치하는지
3. **상태별 화면**: Default / Active / Disabled / Error 등 상태가 Figma에 정의되어 있는지
4. **시나리오 미반영**: Figma에는 있지만 시나리오에 빠진 UI 요소나 인터랙션이 있는지
5. **불일치 리포트 확인**: 사용자가 불일치 리포트를 함께 제공한 경우, 해당 항목이 실제 Figma에서 확인되는지

---

## 출력 형식

불일치 항목을 아래 표로 정리하세요.

| # | 항목 | Figma | 시나리오 | 판정 | 비고 |
|---|------|-------|----------|------|------|
| 1 | 버튼 레이블 | "저장하기" | "저장" | 불일치 | Figma 기준으로 수정 필요 |

판정 기호: 일치 / 불일치 / Figma 미정의 / 확인 필요

---

## 종합 판단

마지막에 아래 중 하나로 종합 판단하세요.

| 판정 | 기준 |
|------|------|
| **PASS** | 불일치 없음, 시나리오 확정 가능 |
| **수정 필요 (N건)** | 불일치 N건, 시나리오 수정 후 확정 |
| **기획자 확인 필요** | Figma와 기획서 모두 불명확한 항목 있음 |
```

### 4.6 .env (없을 때만 생성)

```
JIRA_API_TOKEN=
CONFLUENCE_URL=
CONFLUENCE_EMAIL=
CONFLUENCE_API_TOKEN=
FIGMA_ACCESS_TOKEN=
```

### 4.7 tools/poll_sheet.py (없을 때만 생성)

구글 시트 FAIL 폴링 스크립트. report-bug 스킬의 폴링 기능에서 사용한다.

**핵심 기능:**
- 지정된 구글 시트를 주기적으로 읽어 FAIL 행 감지 (J컬럼=F + N컬럼(BTS ID) 비어있음)
- 상위 행에서 경로 정보(A~G컬럼) fill-down으로 조합
- 신규 FAIL만 슬랙 알림 (중복 방지: alerted_rows 관리)
- 분석 결과를 `data/bugs/pending_bugs.json`에 저장
- ON/OFF 플래그 파일로 제어 (`data/bugs/.poll_active`, `data/bugs/.poll_stop`)

**실행:**
```bash
python tools/poll_sheet.py --sheet {SHEET_ID} --tab {TAB_NAME} [--interval 600]
```

**의존성:** `google-auth`, `google-auth-oauthlib`, `google-api-python-client`, `python-dotenv`

**스크립트 스펙:**

```python
#!/usr/bin/env python3
"""
Google Sheet FAIL Polling Script
- 구글 시트에서 FAIL 행을 주기적으로 감지
- 신규 FAIL 발견 시 슬랙 알림 + pending_bugs.json 저장
- report-bug 스킬과 연동하여 Jira 등록 플로우 지원

Usage:
    python tools/poll_sheet.py --sheet SHEET_ID --tab TAB_NAME [--interval 600]

Flags:
    data/bugs/.poll_active → 존재하면 폴링 활성화
    data/bugs/.poll_stop   → 존재하면 스크립트 종료
"""
import argparse, json, os, time, urllib.request
from datetime import datetime
from pathlib import Path

# Google Sheets API
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

# 설정
SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']
ENV_PATH = '.env'
PENDING_FILE = 'data/bugs/pending_bugs.json'
FLAG_ACTIVE = 'data/bugs/.poll_active'
FLAG_STOP = 'data/bugs/.poll_stop'

# 시트 컬럼 매핑 (0-indexed)
COL_COMPONENT = 0    # A: JIRA 컴포넌트
COL_DEPTH_START = 1  # B~G: 1~6 Depth
COL_DEPTH_END = 6
COL_PRIORITY = 7     # H: Priority
COL_EXPECTED = 8     # I: Expected Result
COL_RESULT = 9       # J: Result (F = FAIL)
COL_BTS_ID = 13      # N: BTS ID

def load_env():
    """Load .env file"""
    env = {}
    if os.path.exists(ENV_PATH):
        with open(ENV_PATH, encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, val = line.split('=', 1)
                    env[key.strip()] = val.strip().split('#')[0].strip()
    return env

def get_sheets_service():
    """Google Sheets API 서비스 생성"""
    creds = None
    token_path = os.path.join('credentials', 'token.json')
    creds_path = os.path.join('credentials', 'credentials.json')

    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(creds_path, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(token_path, 'w') as token:
            token.write(creds.to_json())

    return build('sheets', 'v4', credentials=creds)

def read_sheet(service, sheet_id, tab_name):
    """시트 전체 데이터 읽기"""
    result = service.spreadsheets().values().get(
        spreadsheetId=sheet_id,
        range=f"'{tab_name}'!A5:N"
    ).execute()
    return result.get('values', [])

def fill_down_path(rows, row_idx):
    """상위 행에서 경로 정보 fill-down (A~G 컬럼)"""
    path_parts = [''] * 7  # A~G
    for i in range(row_idx + 1):
        row = rows[i] if i < len(rows) else []
        for col in range(7):
            val = row[col] if col < len(row) else ''
            if val:
                path_parts[col] = val
                # 하위 depth 초기화
                for j in range(col + 1, 7):
                    if i < row_idx:
                        pass  # 상위 행은 유지
    # 현재 행 기준으로 다시 계산
    path_parts = [''] * 7
    for col in range(7):
        for i in range(row_idx, -1, -1):
            row = rows[i] if i < len(rows) else []
            val = row[col] if col < len(row) else ''
            if val:
                path_parts[col] = val
                break
    return path_parts

def find_fails(rows):
    """FAIL 행 찾기 (J=F + N=비어있음)"""
    fails = []
    for idx, row in enumerate(rows):
        result = row[COL_RESULT] if len(row) > COL_RESULT else ''
        bts_id = row[COL_BTS_ID] if len(row) > COL_BTS_ID else ''

        if result == 'F' and not bts_id:
            path_parts = fill_down_path(rows, idx)
            component = path_parts[0]
            path = ' > '.join([p for p in path_parts[1:] if p])
            priority = row[COL_PRIORITY] if len(row) > COL_PRIORITY else ''
            expected = row[COL_EXPECTED] if len(row) > COL_EXPECTED else ''

            fails.append({
                'row': idx + 5,  # 시트 행 번호 (데이터는 5행부터)
                'component': component,
                'path': path,
                'priority': priority,
                'expected': expected,
                'status': 'pending'
            })
    return fails

def load_alerted_rows():
    """이미 알림한 행 목록 로드"""
    if os.path.exists(PENDING_FILE):
        with open(PENDING_FILE, encoding='utf-8') as f:
            data = json.load(f)
            return set(data.get('alerted_rows', []))
    return set()

def save_pending(sheet_id, tab_name, bugs, alerted_rows):
    """pending_bugs.json 저장"""
    os.makedirs(os.path.dirname(PENDING_FILE), exist_ok=True)
    data = {
        'analyzed_at': datetime.now().isoformat(),
        'sheet_id': sheet_id,
        'tab': tab_name,
        'bugs': bugs,
        'alerted_rows': list(alerted_rows)
    }
    with open(PENDING_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def send_slack(webhook_url, tab_name, new_bugs):
    """슬랙 알림 발송"""
    bug_lines = []
    for i, bug in enumerate(new_bugs):
        bug_lines.append(
            f"• BUG-{i+1:03d} (행 {bug['row']}): "
            f"[{bug['component']}] {bug['path']} — {bug['priority']}"
        )

    text = (
        f"*[QA Agent] FAIL 감지*\n\n"
        f"시트: {tab_name}\n"
        f"신규 FAIL {len(new_bugs)}건 발견\n\n"
        + '\n'.join(bug_lines) +
        f"\n\nClaude Code에서 \"FAIL 분석 결과 확인해줘\"로 등록을 진행하세요."
    )

    payload = json.dumps({'text': text}).encode('utf-8')
    req = urllib.request.Request(
        webhook_url,
        data=payload,
        headers={'Content-Type': 'application/json; charset=utf-8'}
    )
    urllib.request.urlopen(req)

def main():
    parser = argparse.ArgumentParser(description='Google Sheet FAIL Polling')
    parser.add_argument('--sheet', required=True, help='Google Sheet ID')
    parser.add_argument('--tab', required=True, help='Tab(sheet) name')
    parser.add_argument('--interval', type=int, default=600, help='Polling interval (seconds)')
    args = parser.parse_args()

    env = load_env()
    webhook_url = env.get('SLACK_WEBHOOK_URL', '')
    if not webhook_url:
        print('[ERROR] SLACK_WEBHOOK_URL not found in .env')
        return

    service = get_sheets_service()
    print(f'[POLL] Started — sheet: {args.tab}, interval: {args.interval}s')

    # 활성화 플래그 생성
    os.makedirs(os.path.dirname(FLAG_ACTIVE), exist_ok=True)
    Path(FLAG_ACTIVE).touch()

    try:
        while True:
            # 종료 플래그 확인
            if os.path.exists(FLAG_STOP):
                print('[POLL] Stop flag detected. Exiting.')
                os.remove(FLAG_STOP)
                break

            # 활성화 플래그 확인
            if not os.path.exists(FLAG_ACTIVE):
                print(f'[POLL] Paused (no .poll_active). Waiting...')
                time.sleep(args.interval)
                continue

            # 시트 읽기 + FAIL 감지
            print(f'[POLL] {datetime.now().strftime("%H:%M:%S")} Checking...')
            rows = read_sheet(service, args.sheet, args.tab)
            fails = find_fails(rows)

            if fails:
                alerted = load_alerted_rows()
                new_fails = [f for f in fails if f['row'] not in alerted]

                if new_fails:
                    # 알림 발송
                    new_rows = {f['row'] for f in new_fails}
                    all_alerted = alerted | new_rows
                    save_pending(args.sheet, args.tab, fails, all_alerted)
                    send_slack(webhook_url, args.tab, new_fails)
                    print(f'[POLL] New FAIL {len(new_fails)}건 → Slack sent')
                else:
                    print(f'[POLL] FAIL {len(fails)}건 (all alerted)')
            else:
                print(f'[POLL] No FAIL found')

            time.sleep(args.interval)

    except KeyboardInterrupt:
        print('\n[POLL] Interrupted by user')
    finally:
        if os.path.exists(FLAG_ACTIVE):
            os.remove(FLAG_ACTIVE)
        print('[POLL] Stopped')

if __name__ == '__main__':
    main()
```

> `/init` 실행 시 위 스크립트를 `tools/poll_sheet.py`에 생성한다. 이미 존재하면 건너뛴다.

### 4.8 .gitignore (없을 때만 생성)

```
.env
*.pyc
__pycache__/
.pytest_cache/
node_modules/
```

---

## 5. 의존성 설치

폴더/파일 생성 완료 후, Python 의존성을 설치한다:

```bash
pip install -r requirements.txt
```

- `requirements.txt`는 플러그인에 포함되어 있음 (orchestrator 패키지 의존성)
- 설치 실패 시 에러 메시지를 표시하되, 초기화 자체는 완료로 처리
- Python 3.10 이상 필요

---

## 6. 처리 규칙

1. **이미 존재하는 폴더/파일은 절대 덮어쓰지 않는다** (건너뛰기)
2. 폴더 생성 시 `mkdir -p` 방식으로 중간 경로도 함께 생성
3. 의존성 설치 (`pip install -r requirements.txt`)
4. 모든 작업 완료 후 결과를 요약 출력
5. **초기화 완료 후 `/setup`을 자동으로 이어서 실행** (온보딩 원스텝 완료)

---

## 7. 완료 출력 형식

```
초기화 완료!

[폴더]
  생성됨: config/, data/scenarios/, data/tc/, ...
  이미 존재: (해당 시 표시)

[파일]
  생성됨: config/common.json, config/project.json, templates/figma_review_prompt.md, ...
  이미 존재: (해당 시 표시)

다음 단계: /setup 을 실행하여 설정값을 입력하세요.
```
