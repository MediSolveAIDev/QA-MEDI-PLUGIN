"""기획서 변경 대응: 시나리오 diff 업데이트 사이클."""

import shutil
from pathlib import Path

from orchestrator.cli import ask_approval, ask_choice, ask_url
from orchestrator.config import CommonConfig, EnvConfig, ProjectConfig
from orchestrator.notify.slack import send_approval_notification
from orchestrator.review.gate import run_review_gate
from orchestrator.skills.invoker import invoke_skill
from orchestrator.state import PipelineState
from orchestrator.upload.confluence import upload_scenario_to_confluence
from orchestrator.utils.logger import log


def run_spec_update(
    state: PipelineState,
    new_spec_url: str,
    project_config: ProjectConfig,
    common_config: CommonConfig,
    env_config: EnvConfig,
    no_slack: bool = False,
) -> str:
    """
    기획서 변경 대응 사이클.

    ① 기존 시나리오 백업
    ② /write-scenario (diff 모드)
    ③ /review-spec + /review-qa 병렬 리뷰
    ④ 리뷰 루프 (최대 3회)
    ⑤ 승인: 시나리오 업데이트 확정
    ⑥ Confluence 재업로드
    ⑦ 선택: [A] 원래 단계 복귀 / [B] TC 수정까지 진행

    Returns: "resume" (원래 단계 복귀) 또는 "tc_update" (TC 재실행)
    """
    log("INFO", "Spec Update Cycle 시작")
    saved_phase = state.current_phase

    scenario_file = state.artifacts.get("scenario")
    if not scenario_file:
        log("ERROR", "기존 시나리오 없음. Phase 1-A를 먼저 실행하세요.")
        return "resume"

    # ---- Step 1: 기존 시나리오 백업 ----
    update_count = len(state.spec_updates) + 1
    backup_path = f"{scenario_file}_backup_{update_count}.md"
    try:
        shutil.copy2(scenario_file, backup_path)
        log("INFO", f"시나리오 백업: {backup_path}")
    except FileNotFoundError:
        log("WARN", "기존 시나리오 파일 없음. 백업 건너뜀.")

    # ---- Step 2: 시나리오 diff 업데이트 ----
    log("INFO", "Spec Update Step 2: 시나리오 diff 업데이트")
    result = invoke_skill(
        "write-scenario",
        new_spec_url,
        state,
        phase="spec-update",
        extra_context=(
            f"기존 시나리오 파일: {scenario_file}\n"
            f"새 기획서 URL: {new_spec_url}\n"
            f"기존 시나리오와 새 기획서를 비교하여 변경점만 추출하고 반영하세요.\n"
            f"변경 목록을 시나리오 상단에 명시하세요."
        ),
    )

    if not result.success:
        log("ERROR", f"시나리오 업데이트 실패: {result.error}")
        return "resume"

    if result.output_file:
        state.artifacts["scenario"] = result.output_file
        state.save()

    # ---- Step 3-4: 리뷰 루프 ----
    log("INFO", "Spec Update Step 3: 리뷰 게이트")
    updated_scenario = state.artifacts["scenario"]

    def rework_builder(feedback_paths):
        feedback_str = ", ".join(feedback_paths)
        extra = f"리뷰 피드백 파일: {feedback_str}\n피드백을 반영하여 시나리오를 수정하세요."
        return ("write-scenario", new_spec_url, extra)

    review_skills = [
        ("review-spec", updated_scenario),
        ("review-qa", updated_scenario),
    ]

    passed, _ = run_review_gate(
        writer_skill="write-scenario",
        writer_args=new_spec_url,
        reviewer_skills=review_skills,
        state=state,
        phase="spec-update",
        rework_prompt_builder=rework_builder,
    )

    if not passed:
        send_approval_notification(
            common_config, env_config, state, "escalation",
            "기획 변경 시나리오 리뷰가 통과하지 못했습니다.",
            no_slack=no_slack,
        )
        return "resume"

    # ---- Step 5: 승인 ----
    send_approval_notification(
        common_config, env_config, state, "2_scenario_final",
        "기획 변경 반영 시나리오가 준비되었습니다. 확정 부탁드립니다.",
        no_slack=no_slack,
    )

    approval = ask_approval(
        "업데이트", "시나리오 업데이트 확정",
        f"  시나리오 파일: {state.artifacts['scenario']}\n"
        f"  백업 파일: {backup_path}",
    )

    if approval == "rejected":
        # 백업 복원
        try:
            shutil.copy2(backup_path, scenario_file)
            state.artifacts["scenario"] = scenario_file
            state.save()
            log("INFO", "시나리오 복원 완료.")
        except FileNotFoundError:
            pass
        return "resume"

    # ---- Step 6: Confluence 재업로드 ----
    existing_url = state.upload_urls.get("scenario_confluence")
    if existing_url:
        print(f"  기존 Confluence URL: {existing_url}")
        reupload = input("  기존 URL에 재업로드할까요? (Y/N): ").strip().upper()
        if reupload == "Y":
            upload_url = upload_scenario_to_confluence(
                state.artifacts["scenario"],
                existing_url,
                env_config,
                common_config,
                state,
            )
            if upload_url:
                state.upload_urls["scenario_confluence"] = upload_url
                state.save()
                print(f"  Confluence 재업로드 완료: {upload_url}")

    # ---- Step 7: 선택 ----
    choice = ask_choice(
        "다음 단계를 선택하세요:",
        [
            ("A", f"원래 진행 중이던 단계로 복귀 (Phase {saved_phase})"),
            ("B", "TC도 변경사항 반영하여 수정 진행 (Phase 1-B부터)"),
        ],
    )

    state.record_spec_update(new_spec_url, "resume" if choice == "A" else "tc_update")

    if choice == "A":
        state.current_phase = saved_phase
        state.save()
        log("INFO", f"Phase {saved_phase}로 복귀")
        return "resume"
    else:
        state.current_phase = "1-B"
        state.save()
        log("INFO", "Phase 1-B부터 재실행")
        return "tc_update"
