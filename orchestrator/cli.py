"""CLI 인자 파싱 + 터미널 input() 승인/URL 입력."""

import argparse
from typing import Optional


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="QA Agent Orchestrator")
    parser.add_argument(
        "--phase",
        choices=["0", "1-A", "1-B", "3", "4"],
        help="특정 Phase만 실행",
    )
    parser.add_argument(
        "--resume",
        metavar="PIPELINE_ID",
        help="중단된 파이프라인 재개 (예: SAY_v1.4.0)",
    )
    parser.add_argument(
        "--project",
        action="append",
        dest="parallel_projects",
        help="프로젝트 코드 (반복 가능, 병렬 실행)",
    )
    parser.add_argument("--version", help="프로젝트 버전 (예: v1.4.0)")
    parser.add_argument("--feature", help="기능명 (예: AI_가이드_대시보드)")
    parser.add_argument("--spec-url", help="Confluence 기획서 URL 또는 Page ID")
    parser.add_argument(
        "--spec-update",
        help="기획서 변경 대응: 새 기획서 URL",
    )
    parser.add_argument(
        "--status",
        metavar="PIPELINE_ID",
        nargs="?",
        const="latest",
        help="파이프라인 진행 상황 조회 (예: SAY_v1.4.0, 생략 시 최근)",
    )
    parser.add_argument(
        "--no-slack",
        action="store_true",
        help="Slack 알림 비활성화",
    )
    parser.add_argument(
        "--auto-approve",
        action="store_true",
        help="모든 승인 포인트 자동 통과 (Claude Code 내 실행 시 사용)",
    )
    return parser.parse_args(argv)


_auto_approve = False

# 수동 승인이 필요한 포인트 (팀장 확인 필수)
MANUAL_APPROVALS = {"0", "1", "2", "3", "4", "6"}

# 자동 승인 포인트 (Slack 알림만 보내고 진행)
# "5" (FAIL 분석): FAIL 없으면 자동 통과, 있으면 phase 코드에서 수동 처리


def set_auto_approve(enabled: bool):
    """Claude Code 내 실행 시 자동 승인 모드 설정."""
    global _auto_approve
    _auto_approve = enabled


def ask_approval(approval_id: str, description: str, details: str = "") -> str:
    """승인 요청. 'approved', 'rejected', 'rework' 반환."""
    print(f"\n{'='*60}")
    print(f"  승인 {approval_id}: {description}")
    print(f"{'='*60}")
    if details:
        print(details)

    # --auto-approve 모드: 수동 승인 포인트만 멈추고 나머지 자동 통과
    if _auto_approve and approval_id not in MANUAL_APPROVALS:
        print("  → 자동 승인")
        return "approved"

    print()
    while True:
        choice = input("  [A]승인 / [R]거부 / [W]재작업? ").strip().upper()
        if choice in ("A", "APPROVE", "APPROVED"):
            return "approved"
        elif choice in ("R", "REJECT", "REJECTED"):
            return "rejected"
        elif choice in ("W", "REWORK"):
            return "rework"
        print("  A, R, W 중 하나를 입력해주세요.")


def ask_url(prompt: str) -> Optional[str]:
    """URL 입력. 빈 값이면 None 반환."""
    if _auto_approve:
        return None
    url = input(f"  {prompt} (Enter로 건너뛰기): ").strip()
    return url if url else None


def ask_input(prompt: str, required: bool = False) -> str:
    """자유 입력."""
    if _auto_approve:
        return ""
    while True:
        value = input(f"  {prompt}: ").strip()
        if value or not required:
            return value
        print("  필수 입력입니다.")


def ask_choice(prompt: str, options: list[tuple[str, str]]) -> str:
    """선택지 제시. 키 반환."""
    print(f"\n  {prompt}")
    for key, label in options:
        print(f"    [{key}] {label}")
    if _auto_approve:
        first_key = options[0][0]
        print(f"  → 자동 선택: {first_key} (--auto-approve)")
        return first_key
    valid_keys = [k for k, _ in options]
    while True:
        choice = input("  선택: ").strip().upper()
        if choice in valid_keys:
            return choice
        print(f"  {', '.join(valid_keys)} 중 하나를 입력해주세요.")
