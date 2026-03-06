"""Slack 알림: 승인 요청 + 산출물 진행 상황 알림."""

import requests

from orchestrator.config import CommonConfig, EnvConfig
from orchestrator.state import PipelineState
from orchestrator.utils.logger import log

APPROVAL_DESCRIPTIONS = {
    "0_plan": "진행 계획 확인",
    "1_scenario_review": "1차 시나리오 리뷰 Pass 확인",
    "2_scenario_final": "Figma 검수 후 시나리오 확정",
    "3_tc_final": "TC 확정",
    "4_automation": "자동화 구현 여부 결정",
    "5_fail_analysis": "FAIL 분석 결과",
    "6_cross_project": "크로스 프로젝트 영향도",
    "escalation": "에스컬레이션 (팀장 확인 필요)",
}


def send_approval_notification(
    common_config: CommonConfig,
    env_config: EnvConfig,
    state: PipelineState,
    approval_key: str,
    message: str,
    no_slack: bool = False,
):
    """Slack Webhook으로 승인 요청 알림 발송."""
    if no_slack:
        return

    webhook_url = (
        env_config.slack_webhook_approval
        or common_config.slack_webhook_url
        or env_config.slack_webhook_url
    )
    if not webhook_url:
        log("WARN", "Slack webhook URL 미설정. 알림 건너뜀.")
        return

    approval_desc = APPROVAL_DESCRIPTIONS.get(approval_key, approval_key)
    approval_num = approval_key.split("_")[0] if approval_key[0].isdigit() else ""

    text = (
        f":bell: *QA Agent 승인 요청*\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"프로젝트: `{state.project} {state.version}`\n"
        f"기능: {state.feature}\n"
    )

    if approval_num:
        text += f"단계: *승인 {approval_num}: {approval_desc}*\n"
    else:
        text += f"단계: *{approval_desc}*\n"

    text += f"\n{message}\n━━━━━━━━━━━━━━━━━━━━"

    color = "#dc3545" if "escalation" in approval_key else "#0288d1"

    payload = {
        "text": text,
        "attachments": [
            {
                "color": color,
                "title": f"[{state.project} {state.version}]",
                "text": f"Phase: {state.current_phase} | Pipeline: {state.pipeline_id}",
            }
        ],
    }

    try:
        response = requests.post(webhook_url, json=payload, timeout=10)
        if response.status_code == 200:
            log("INFO", f"Slack 알림 발송: {approval_key}")
        else:
            log("WARN", f"Slack 알림 실패: {response.status_code}")
    except Exception as e:
        log("WARN", f"Slack 알림 오류: {e}")


def send_progress_notification(
    common_config: CommonConfig,
    env_config: EnvConfig,
    state: PipelineState,
    message: str,
    no_slack: bool = False,
):
    """Slack Webhook으로 진행 상황 알림 발송."""
    if no_slack:
        return

    webhook_url = (
        common_config.slack_webhook_url
        or env_config.slack_webhook_url
        or env_config.slack_webhook_approval
    )
    if not webhook_url:
        log("WARN", "Slack webhook URL 미설정. 알림 건너뜀.")
        return

    text = (
        f":arrows_counterclockwise: *QA Agent 진행 알림*\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"프로젝트: `{state.project} {state.version}`\n"
        f"기능: {state.feature}\n"
        f"Phase: {state.current_phase}\n"
        f"\n{message}\n━━━━━━━━━━━━━━━━━━━━"
    )

    payload = {
        "text": text,
        "attachments": [
            {
                "color": "#36a64f",
                "title": f"[{state.project} {state.version}]",
                "text": f"Phase: {state.current_phase} | Pipeline: {state.pipeline_id}",
            }
        ],
    }

    try:
        response = requests.post(webhook_url, json=payload, timeout=10)
        if response.status_code == 200:
            log("INFO", f"Slack 진행 알림 발송: {message[:50]}")
        else:
            log("WARN", f"Slack 진행 알림 실패: {response.status_code}")
    except Exception as e:
        log("WARN", f"Slack 진행 알림 오류: {e}")
