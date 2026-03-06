"""Phase 1-A: 시나리오 작성 → 리뷰 → Figma 보강 → 승인 → Confluence 업로드."""

from orchestrator.cli import ask_approval, ask_url
from orchestrator.config import CommonConfig, EnvConfig, ProjectConfig
from orchestrator.notify.slack import send_approval_notification, send_progress_notification
from orchestrator.review.gate import run_review_gate
from orchestrator.skills.invoker import invoke_skill
from orchestrator.state import PipelineState
from orchestrator.upload.confluence import upload_scenario_to_confluence
from orchestrator.utils.files import build_artifact_path
from orchestrator.utils.logger import log


def run_phase1a(
    state: PipelineState,
    project_config: ProjectConfig,
    common_config: CommonConfig,
    env_config: EnvConfig,
    no_slack: bool = False,
) -> str:
    """
    Phase 1-A: 시나리오.

    ① 시나리오 작성
    ② 리뷰 (spec + qa 병렬)
    ③ 리뷰 루프 (최대 3회)
    ④ 승인 1: 시나리오 리뷰 Pass
    ⑤ Figma 보강
    ⑥ 승인 2: 시나리오 확정 → Confluence 업로드

    Returns: "continue", "escalated", "rejected"
    """
    # ---- Step 1: 시나리오 작성 ----
    log("INFO", "Phase 1-A Step 1: 시나리오 작성")
    scenario_path = build_artifact_path(
        "write-scenario", state.project, state.version, state.feature
    )

    result = invoke_skill(
        "write-scenario",
        state.spec_url,
        state,
        phase="1-A",
        extra_context=f"프로젝트: {state.project}, 버전: {state.version}, 기능: {state.feature}",
    )

    if not result.success:
        log("ERROR", f"시나리오 작성 실패: {result.error}")
        return "escalated"

    state.artifacts["scenario"] = result.output_file or str(scenario_path)
    state.save()

    send_progress_notification(
        common_config, env_config, state,
        "시나리오 작성 완료, 리뷰 진행합니다.",
        no_slack=no_slack,
    )

    # ---- Step 2-3: 리뷰 루프 ----
    log("INFO", "Phase 1-A Step 2: 리뷰 게이트")
    scenario_file = state.artifacts["scenario"]

    def rework_builder(feedback_paths):
        feedback_str = ", ".join(feedback_paths)
        extra = f"리뷰 피드백 파일: {feedback_str}\n피드백을 모두 반영하여 시나리오를 수정하세요."
        return ("write-scenario", state.spec_url, extra)

    review_skills = [
        ("review-spec", scenario_file),
        ("review-qa", scenario_file),
    ]

    passed, review_results, latest_artifact = run_review_gate(
        writer_skill="write-scenario",
        writer_args=state.spec_url,
        reviewer_skills=review_skills,
        state=state,
        phase="1-A",
        rework_prompt_builder=rework_builder,
    )

    # 재작업으로 산출물이 갱신되었으면 state 반영
    if latest_artifact:
        state.artifacts["scenario"] = latest_artifact
        state.save()

    if not passed:
        log("WARN", "리뷰 게이트 실패. 에스컬레이션.")
        send_approval_notification(
            common_config, env_config, state, "escalation",
            "시나리오 리뷰 3회 재작업 후에도 통과하지 못했습니다.",
            no_slack=no_slack,
        )
        return "escalated"

    # 리뷰 산출물 경로 저장
    for skill_name, result in review_results:
        if "review-spec" in skill_name and result.output_file:
            state.artifacts["scenario_review_spec"] = result.output_file
        elif "review-qa" in skill_name and result.output_file:
            state.artifacts["scenario_review_qa"] = result.output_file
    state.save()

    # ---- Step 4: 승인 1 ----
    send_approval_notification(
        common_config, env_config, state, "1_scenario_review",
        "시나리오 리뷰가 Pass 되었습니다. 확인 부탁드립니다.",
        no_slack=no_slack,
    )

    approval = ask_approval(
        "1", "시나리오 리뷰 Pass 확인",
        f"  시나리오 파일: {state.artifacts['scenario']}\n  리뷰 결과: 전원 PASS",
    )
    state.set_approval("1_scenario_review", approval)

    if approval == "rejected":
        return "rejected"

    # ---- Step 5: Figma 보강 ----
    log("INFO", "Phase 1-A Step 5: Figma 보강")
    figma_result = invoke_skill(
        "write-scenario",
        scenario_file,
        state,
        phase="1-A",
        extra_context="Figma 디자인 기준 시나리오를 업데이트하세요. "
                      "Figma 디자인에서 문구, UI 값, 상태를 확인하여 보강하세요.",
    )

    if figma_result.success and figma_result.output_file:
        state.artifacts["scenario"] = figma_result.output_file
        state.save()

    # ---- Step 6: 승인 2 ----
    print("\n  [안내] 팀장이 Chrome + Claude in Chrome으로 Figma 직접 검수를 진행해주세요.")
    print(f"  시나리오 파일: {state.artifacts['scenario']}")

    send_approval_notification(
        common_config, env_config, state, "2_scenario_final",
        "Figma 보강 시나리오가 준비되었습니다. Figma 검수 후 확정 부탁드립니다.",
        no_slack=no_slack,
    )

    approval = ask_approval(
        "2", "시나리오 확정 (Figma 검수 후)",
        f"  시나리오 파일: {state.artifacts['scenario']}",
    )
    state.set_approval("2_scenario_final", approval)

    if approval == "rejected":
        return "rejected"

    # ---- Confluence 업로드 ----
    confluence_url = project_config.confluence_parent_page_id
    if confluence_url:
        print(f"  저장된 Confluence Page ID 사용: {confluence_url}")
    else:
        confluence_url = ask_url("Confluence 업로드 대상 URL 또는 Page ID")

    if confluence_url:
        page_title = f"{state.project} {state.version} {state.feature} 시나리오"
        print(f"\n  업로드 대상:")
        print(f"    Confluence: {confluence_url}")
        print(f"    페이지 제목: {page_title}")
        print(f"    시나리오 파일: {state.artifacts['scenario']}")

        upload_url = upload_scenario_to_confluence(
            state.artifacts["scenario"],
            confluence_url,
            env_config,
            common_config,
            state,
        )
        if upload_url:
            state.upload_urls["scenario_confluence"] = upload_url
            state.save()
            print(f"  Confluence 업로드 완료: {upload_url}")

    state.advance_phase("1-B")
    return "continue"
