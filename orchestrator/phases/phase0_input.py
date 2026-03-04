"""Phase 0: 정보 수집 + 계획 승인."""

from datetime import datetime

from orchestrator.cli import ask_approval, ask_input
from orchestrator.config import CommonConfig, EnvConfig, ProjectConfig, load_project_config
from orchestrator.notify.slack import send_approval_notification
from orchestrator.state import PipelineState
from orchestrator.utils.logger import log


def run_phase0(
    state: PipelineState,
    project_config: ProjectConfig,
    common_config: CommonConfig,
    env_config: EnvConfig,
    no_slack: bool = False,
) -> str:
    """
    Phase 0: 정보 수집 → 계획 보고 → 승인 0.

    Returns: "continue", "rejected"
    """
    log("INFO", "Phase 0: 진행 계획 수립")

    # 계획 보고
    plan_summary = (
        f"프로젝트: {state.project} {state.version}\n"
        f"  기능: {state.feature}\n"
        f"  기획서: {state.spec_url}\n"
        f"\n"
        f"  진행 계획:\n"
        f"    Phase 1-A: 시나리오 작성 → 리뷰 → Figma 보강 → 확정\n"
        f"    Phase 1-B: TC 작성 → 포맷검증 → 리뷰 → 확정\n"
        f"    Phase 3:   자동화 검토 → 테스트코드 → FAIL 분석\n"
        f"    Phase 4:   최종 보고 → 크로스 프로젝트 영향도\n"
    )

    send_approval_notification(
        common_config, env_config, state, "0_plan",
        "진행 계획이 수립되었습니다. 확인 부탁드립니다.",
        no_slack=no_slack,
    )

    approval = ask_approval("0", "진행 계획 확인", plan_summary)
    state.set_approval("0_plan", approval)

    if approval == "rejected":
        return "rejected"

    state.advance_phase("1-A")
    return "continue"
