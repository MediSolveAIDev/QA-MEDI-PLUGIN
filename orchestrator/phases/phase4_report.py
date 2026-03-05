"""Phase 4: 최종 보고 → 크로스 프로젝트 영향도."""

from orchestrator.cli import ask_approval
from orchestrator.config import CommonConfig, EnvConfig, ProjectConfig
from orchestrator.notify.slack import send_approval_notification, send_progress_notification
from orchestrator.skills.invoker import invoke_skill
from orchestrator.state import PipelineState
from orchestrator.utils.logger import log


def run_phase4(
    state: PipelineState,
    project_config: ProjectConfig,
    common_config: CommonConfig,
    env_config: EnvConfig,
    no_slack: bool = False,
) -> str:
    """
    Phase 4: 최종 보고.

    ① 프로젝트 리포트 생성
    ② 크로스 프로젝트 영향 → 승인 6

    Returns: "continue", "escalated", "rejected"
    """
    # ---- Step 1: 프로젝트 리포트 ----
    log("INFO", "Phase 4 Step 1: 프로젝트 리포트 생성")
    report_result = invoke_skill(
        "report-project",
        f"{state.project} {state.version}",
        state,
        phase="4",
    )

    if report_result.success and report_result.output_file:
        state.artifacts["report"] = report_result.output_file
        state.save()

    send_progress_notification(
        common_config, env_config, state,
        "프로젝트 리포트 생성 완료.",
        no_slack=no_slack,
    )

    # ---- Step 2: 크로스 프로젝트 영향 ----
    is_cross = (
        state.project == "SSO"
        or input("\n  크로스 프로젝트 영향이 있습니까? (Y/N): ").strip().upper() == "Y"
    )

    if is_cross:
        log("INFO", "Phase 4 Step 2: 크로스 프로젝트 영향도 분석")
        impact_result = invoke_skill(
            "analyze-impact",
            f"{state.project} {state.version} {state.feature}",
            state,
            phase="4",
        )

        if impact_result.success and impact_result.output_file:
            state.artifacts["impact"] = impact_result.output_file
            state.save()

        send_approval_notification(
            common_config, env_config, state, "6_cross_project",
            "크로스 프로젝트 영향도 분석이 완료되었습니다. 확인 부탁드립니다.",
            no_slack=no_slack,
        )

        approval = ask_approval(
            "6", "크로스 프로젝트 영향도 확인",
            f"  영향도 분석: {state.artifacts.get('impact', 'N/A')}",
        )
        state.set_approval("6_cross_project", approval)

    # ---- 최종 요약 ----
    _print_summary(state)

    send_progress_notification(
        common_config, env_config, state,
        "파이프라인 완료.",
        no_slack=no_slack,
    )

    return "continue"


def _print_summary(state: PipelineState):
    """파이프라인 완료 요약."""
    print(f"\n{'='*60}")
    print(f"  PIPELINE COMPLETE: {state.project} {state.version}")
    print(f"{'='*60}")
    print(f"  기능: {state.feature}")
    print(f"  시작: {state.started_at}")
    print(f"  완료: {state.updated_at}")
    print()
    print("  산출물:")
    for key, path in state.artifacts.items():
        if path:
            print(f"    {key}: {path}")
    print()
    print("  승인:")
    for key, status in state.approvals.items():
        icon = {"approved": "V", "rejected": "X", "pending": "?", None: "-"}
        print(f"    [{icon.get(status, '?')}] {key}: {status or 'N/A'}")
    print()
    if state.upload_urls.get("scenario_confluence"):
        print(f"  Confluence: {state.upload_urls['scenario_confluence']}")
    if state.upload_urls.get("tc_gsheet"):
        print(f"  Google Sheet: {state.upload_urls['tc_gsheet']}")
    print(f"{'='*60}")
