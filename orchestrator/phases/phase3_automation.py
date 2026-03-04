"""Phase 3: 자동화 검토 → 테스트코드 → FAIL 분석."""

from orchestrator.cli import ask_approval
from orchestrator.config import CommonConfig, EnvConfig, ProjectConfig
from orchestrator.notify.slack import send_approval_notification
from orchestrator.skills.invoker import invoke_skill
from orchestrator.state import PipelineState
from orchestrator.utils.logger import log


def run_phase3(
    state: PipelineState,
    project_config: ProjectConfig,
    common_config: CommonConfig,
    env_config: EnvConfig,
    no_slack: bool = False,
) -> str:
    """
    Phase 3: 자동화.

    ① 자동화 검토
    ② 승인 4: 자동화 구현 여부
    ③ 테스트 코드 생성
    ④ GitHub Actions (수동)
    ⑤ FAIL 분석
    ⑥ 승인 5: FAIL 분석 결과

    Returns: "continue", "escalated", "rejected"
    """
    tc_path = state.artifacts.get("tc")
    if not tc_path:
        log("ERROR", "확정 TC 없음. Phase 1-B를 먼저 실행하세요.")
        return "escalated"

    # ---- Step 1: 자동화 검토 ----
    log("INFO", "Phase 3 Step 1: 자동화 검토")
    assess_result = invoke_skill("assess-automation", tc_path, state, phase="3")

    if assess_result.success and assess_result.output_file:
        state.artifacts["assessment"] = assess_result.output_file
        state.save()

    # ---- Step 2: 승인 4 ----
    send_approval_notification(
        common_config, env_config, state, "4_automation",
        "자동화 검토가 완료되었습니다. 자동화 구현 여부 결정 부탁드립니다.",
        no_slack=no_slack,
    )

    approval = ask_approval(
        "4", "자동화 구현 여부 결정",
        f"  자동화 검토 결과: {state.artifacts.get('assessment', 'N/A')}",
    )
    state.set_approval("4_automation", approval)

    if approval == "rejected":
        log("INFO", "자동화 거부. Phase 4로 이동.")
        state.advance_phase("4")
        return "continue"

    # ---- Step 3: 테스트 코드 생성 ----
    log("INFO", "Phase 3 Step 3: 테스트 코드 생성")
    test_result = invoke_skill(
        "write-test-code", tc_path, state, phase="3",
        extra_context=f"자동화 검토 결과: {state.artifacts.get('assessment', '')}",
    )

    if test_result.success and test_result.output_file:
        state.artifacts["test_code"] = test_result.output_file
        state.save()

    # ---- Step 4: GitHub Actions (수동) ----
    print(f"\n  [안내] 테스트 코드가 생성되었습니다.")
    print(f"  테스트 파일: {state.artifacts.get('test_code', 'N/A')}")
    print("  GitHub Actions에서 테스트를 실행한 후, 결과를 확인하세요.")

    has_failures = input("\n  테스트 실행 결과에 FAIL이 있습니까? (Y/N): ").strip().upper()

    if has_failures == "Y":
        # ---- Step 5: FAIL 분석 ----
        log("INFO", "Phase 3 Step 5: FAIL 분석")
        fail_result = invoke_skill(
            "analyze-fail",
            "data/test_results/test_results.json",
            state,
            phase="3",
        )

        if fail_result.success and fail_result.output_file:
            state.artifacts["fail_analysis"] = fail_result.output_file
            state.save()

        # ---- Step 6: 승인 5 ----
        send_approval_notification(
            common_config, env_config, state, "5_fail_analysis",
            "FAIL 분석 결과가 준비되었습니다. 확인 부탁드립니다.",
            no_slack=no_slack,
        )

        approval = ask_approval(
            "5", "FAIL 분석 결과 확인",
            f"  분석 결과: {state.artifacts.get('fail_analysis', 'N/A')}",
        )
        state.set_approval("5_fail_analysis", approval)
    else:
        state.set_approval("5_fail_analysis", "approved")
        log("INFO", "FAIL 없음.")

    state.advance_phase("4")
    return "continue"
