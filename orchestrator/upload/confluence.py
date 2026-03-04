"""Confluence REST API: 시나리오 업로드."""

import re

import requests
from requests.auth import HTTPBasicAuth

from orchestrator.config import CommonConfig, EnvConfig
from orchestrator.state import PipelineState
from orchestrator.utils.logger import log


def upload_scenario_to_confluence(
    scenario_path: str,
    target: str,
    env_config: EnvConfig,
    common_config: CommonConfig,
    state: PipelineState,
) -> str:
    """
    시나리오 마크다운을 Confluence에 업로드.

    Args:
        scenario_path: 시나리오 .md 파일 경로
        target: Confluence Page ID 또는 URL
        env_config: .env 설정
        common_config: common.json 설정
        state: 파이프라인 상태

    Returns:
        페이지 URL (성공시), 빈 문자열 (실패시)
    """
    base_url = env_config.confluence_url or common_config.confluence_base_url
    email = env_config.confluence_email
    token = env_config.confluence_api_token

    if not all([base_url, email, token]):
        log("WARN", "Confluence 인증 정보 누락. 업로드 건너뜀.")
        return ""

    try:
        with open(scenario_path, "r", encoding="utf-8") as f:
            content = f.read()
    except FileNotFoundError:
        log("ERROR", f"시나리오 파일 없음: {scenario_path}")
        return ""

    page_id = _extract_page_id(target)
    title = f"{state.project} {state.version} {state.feature} 시나리오"
    auth = HTTPBasicAuth(email, token)

    if page_id:
        return _update_page(base_url, page_id, title, content, auth)
    else:
        space_key = _extract_space_key(target)
        return _create_page(base_url, space_key, title, content, auth, target)


def _create_page(
    base_url: str, space_key: str, title: str,
    content: str, auth, parent_id: str = "",
) -> str:
    url = f"{base_url}/rest/api/content"

    payload = {
        "type": "page",
        "title": title,
        "space": {"key": space_key},
        "body": {
            "storage": {
                "value": content,
                "representation": "wiki",
            }
        },
    }

    if parent_id and parent_id.isdigit():
        payload["ancestors"] = [{"id": parent_id}]

    try:
        resp = requests.post(
            url, json=payload, auth=auth,
            headers={"Content-Type": "application/json"},
        )

        if resp.status_code == 200:
            data = resp.json()
            page_url = f"{base_url}/pages/viewpage.action?pageId={data['id']}"
            log("INFO", f"Confluence 페이지 생성: {page_url}")
            return page_url
        else:
            log("ERROR", f"Confluence 생성 실패: {resp.status_code} {resp.text[:200]}")
            return ""
    except Exception as e:
        log("ERROR", f"Confluence 업로드 오류: {e}")
        return ""


def _update_page(
    base_url: str, page_id: str, title: str, content: str, auth,
) -> str:
    get_url = f"{base_url}/rest/api/content/{page_id}"
    try:
        resp = requests.get(get_url, auth=auth)
        if resp.status_code != 200:
            log("ERROR", f"페이지 조회 실패 {page_id}: {resp.status_code}")
            return ""

        current = resp.json()
        version = current["version"]["number"] + 1

        payload = {
            "type": "page",
            "title": title,
            "version": {"number": version},
            "body": {
                "storage": {
                    "value": content,
                    "representation": "wiki",
                }
            },
        }

        put_url = f"{base_url}/rest/api/content/{page_id}"
        resp = requests.put(
            put_url, json=payload, auth=auth,
            headers={"Content-Type": "application/json"},
        )

        if resp.status_code == 200:
            page_url = f"{base_url}/pages/viewpage.action?pageId={page_id}"
            log("INFO", f"Confluence 페이지 업데이트: {page_url}")
            return page_url
        else:
            log("ERROR", f"Confluence 업데이트 실패: {resp.status_code}")
            return ""
    except Exception as e:
        log("ERROR", f"Confluence 업데이트 오류: {e}")
        return ""


def _extract_page_id(target: str) -> str:
    if target.isdigit():
        return target
    match = re.search(r"pageId=(\d+)", target)
    if match:
        return match.group(1)
    match = re.search(r"/pages/(\d+)", target)
    if match:
        return match.group(1)
    return ""


def _extract_space_key(target: str) -> str:
    match = re.search(r"/spaces/([A-Za-z]+)", target)
    if match:
        return match.group(1)
    return ""
