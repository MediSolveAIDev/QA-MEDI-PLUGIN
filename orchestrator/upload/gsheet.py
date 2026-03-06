"""Google Sheets API: TC JSON 업로드."""

import json
from pathlib import Path

from orchestrator.config import EnvConfig
from orchestrator.state import PipelineState
from orchestrator.utils.files import BASE_DIR
from orchestrator.utils.logger import log


def upload_tc_to_gsheet(
    tc_path: str,
    sheet_url: str,
    env_config: EnvConfig,
    state: PipelineState,
) -> str:
    """
    TC JSON을 Google Sheets에 업로드.

    Args:
        tc_path: TC .json 파일 경로
        sheet_url: Google Sheet URL
        env_config: .env 설정
        state: 파이프라인 상태

    Returns:
        Sheet URL (성공시), 빈 문자열 (실패시)
    """
    try:
        with open(tc_path, "r", encoding="utf-8") as f:
            tc_data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        log("ERROR", f"TC JSON 로드 실패: {e}")
        return ""

    try:
        import gspread
    except ImportError:
        log("ERROR", "gspread 미설치. pip install gspread google-auth")
        return ""

    gc = _get_gspread_client()
    if not gc:
        log("WARN", "Google Sheets 인증 정보 미설정. 업로드 건너뜀.")
        return ""

    try:
        spreadsheet = gc.open_by_url(sheet_url)

        sheet_name = f"{state.project}_{state.feature}"
        try:
            worksheet = spreadsheet.worksheet(sheet_name)
            worksheet.clear()
        except Exception:
            worksheet = spreadsheet.add_worksheet(
                title=sheet_name, rows=1000, cols=15
            )

        # 헤더 (tc_template.csv 구조)
        headers = [
            "JIRA 컴포넌트", "1 Depth", "2 Depth", "3 Depth",
            "4 Depth", "5 Depth", "6 Depth", "Priority",
            "Expected Result", "Result", "담당자", "Date",
            "Test Version", "BTS ID", "비고",
        ]

        rows = [headers]
        test_cases = tc_data.get("test_cases", [])

        # 이전 행의 depth 값 (중복 제거용)
        prev_depths = [""] * 7

        for tc in test_cases:
            depths = [
                tc.get("jira_component", ""),
                tc.get("depth_1", ""),
                tc.get("depth_2", ""),
                tc.get("depth_3", ""),
                tc.get("depth_4", ""),
                tc.get("depth_5", ""),
                tc.get("depth_6", ""),
            ]

            # 셀 병합 패턴: 상위 depth가 변경된 지점부터만 값 표시
            display = list(depths)
            changed = False
            for i in range(len(depths)):
                if changed or depths[i] != prev_depths[i]:
                    changed = True
                else:
                    display[i] = ""

            prev_depths = list(depths)

            row = display + [
                tc.get("priority", ""),
                tc.get("expected", ""),
                "",  # Result
                "",  # 담당자
                "",  # Date
                "",  # Test Version
                "",  # BTS ID
                tc.get("note", ""),
            ]
            rows.append(row)

        worksheet.update(rows, value_input_option="USER_ENTERED")

        log("INFO", f"TC Google Sheet 업로드 완료: {sheet_url}")
        return sheet_url

    except Exception as e:
        log("ERROR", f"Google Sheet 업로드 실패: {e}")
        return ""


def _get_gspread_client():
    """gspread 인증 클라이언트. credentials/ 폴더의 OAuth 파일 사용."""
    import gspread

    creds_dir = BASE_DIR / "credentials"
    creds_path = creds_dir / "credentials.json"
    token_path = creds_dir / "token.json"

    if creds_path.exists():
        return gspread.oauth(
            credentials_filename=str(creds_path),
            authorized_user_filename=str(token_path),
        )

    return None
