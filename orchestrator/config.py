"""설정 로딩: config/common.json, config/projects/*.json, .env"""

import json
import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent  # qa_agent/


@dataclass
class ProjectConfig:
    name: str
    platform: str
    current_version: str
    confluence_space_key: str
    confluence_parent_page_id: str
    confluence_pages: dict
    figma_file_id: str
    automation_framework: str
    automation_test_repo: str
    automation_base_url: str


@dataclass
class CommonConfig:
    slack_team_lead_user_id: str
    slack_webhook_url: str
    jira_base_url: str
    jira_email: str
    confluence_base_url: str
    github_org: str
    github_actions_repo: str


@dataclass
class EnvConfig:
    confluence_api_token: str
    confluence_email: str
    confluence_url: str
    slack_webhook_url: str
    figma_access_token: str
    jira_api_token: str


def load_common_config() -> CommonConfig:
    config_path = BASE_DIR / "config" / "common.json"
    if not config_path.exists():
        raise FileNotFoundError(
            "config/common.json not found. Run /init then /setup first."
        )
    with open(config_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return CommonConfig(
        slack_team_lead_user_id=data.get("slack", {}).get("team_lead_user_id", ""),
        slack_webhook_url=data.get("slack", {}).get("webhook_url", ""),
        jira_base_url=data.get("jira", {}).get("base_url", ""),
        jira_email=data.get("jira", {}).get("email", ""),
        confluence_base_url=data.get("confluence", {}).get("base_url", ""),
        github_org=data.get("github", {}).get("org", ""),
        github_actions_repo=data.get("github", {}).get("actions_repo", ""),
    )


def load_project_config(project_code: str) -> ProjectConfig:
    config_path = BASE_DIR / "config" / "projects" / f"{project_code.lower()}.json"
    if not config_path.exists():
        raise FileNotFoundError(
            f"config/projects/{project_code.lower()}.json not found."
        )
    with open(config_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return ProjectConfig(
        name=data["name"],
        platform=data.get("platform", "admin"),
        current_version=data.get("current_version", ""),
        confluence_space_key=data.get("confluence", {}).get("space_key", ""),
        confluence_parent_page_id=data.get("confluence", {}).get("parent_page_id", ""),
        confluence_pages=data.get("confluence", {}).get("pages", {}),
        figma_file_id=data.get("figma", {}).get("file_id", ""),
        automation_framework=data.get("automation", {}).get("framework", "pytest"),
        automation_test_repo=data.get("automation", {}).get("test_repo", ""),
        automation_base_url=data.get("automation", {}).get("base_url", ""),
    )


def load_env() -> EnvConfig:
    load_dotenv(BASE_DIR / ".env", override=True)
    return EnvConfig(
        confluence_api_token=os.getenv("CONFLUENCE_API_TOKEN", ""),
        confluence_email=os.getenv("CONFLUENCE_EMAIL", ""),
        confluence_url=os.getenv("CONFLUENCE_URL", ""),
        slack_webhook_url=os.getenv("SLACK_WEBHOOK_URL", ""),
        figma_access_token=os.getenv("FIGMA_ACCESS_TOKEN", ""),
        jira_api_token=os.getenv("JIRA_API_TOKEN", ""),
    )


def validate_setup() -> list[str]:
    """미설정 항목 확인. 문제가 있으면 메시지 리스트 반환."""
    issues = []
    config_dir = BASE_DIR / "config"
    if not config_dir.exists():
        issues.append("config/ 폴더가 없습니다. /init을 먼저 실행해주세요.")
        return issues

    common_path = config_dir / "common.json"
    if not common_path.exists():
        issues.append("config/common.json이 없습니다. /init을 먼저 실행해주세요.")
        return issues

    common = load_common_config()
    if not common.slack_webhook_url:
        issues.append("slack.webhook_url이 비어있습니다. /setup을 실행해주세요.")
    if not common.confluence_base_url:
        issues.append("confluence.base_url이 비어있습니다. /setup을 실행해주세요.")

    env_path = BASE_DIR / ".env"
    if not env_path.exists():
        issues.append(".env 파일이 없습니다. /setup을 실행해주세요.")

    return issues
