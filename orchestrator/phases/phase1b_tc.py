"""Phase 1-B: TC 작성 → 포맷검증 → 리뷰 → 승인 → Google Sheet 업로드."""

import json

from orchestrator.cli import ask_approval, ask_url
from orchestrator.config import CommonConfig, EnvConfig, ProjectConfig
from orchestrator.notify.slack import send_approval_notification, send_progress_notification
from orchestrator.review.gate import MAX_RETRIES, run_review_gate
from orchestrator.skills.invoker import invoke_skill
from orchestrator.state import PipelineState
from orchestrator.upload.gsheet import upload_tc_to_gsheet
from orchestrator.utils.files import build_artifact_path
from orchestrator.utils.logger import log


def run_phase1b(
    state: PipelineState,
    project_config: ProjectConfig,
    common_config: CommonConfig,
    env_config: EnvConfig,
    no_slack: bool = False,
) -> str:
    """
    Phase 1-B: TC.

    ① TC 작성
    ② 포맷 검증 (실패시 재작업)
    ③ 리뷰 (spec + qa 병렬)
    ④ 리뷰 루프 (최대 3회)
    ⑤ 승인 3: TC 확정 → Google Sheet 업로드

    Returns: "continue", "escalated", "rejected"
    """
    scenario_file = state.artifacts.get("scenario")
    if not scenario_file:
        log("ERROR", "확정 시나리오 없음. Phase 1-A를 먼저 실행하세요.")
        return "escalated"

    # ---- Step 1: TC 작성 ----
    log("INFO", "Phase 1-B Step 1: TC 작성")
    tc_result = invoke_skill(
        "write-tc",
        scenario_file,
        state,
        phase="1-B",
        extra_context=f"프로젝트: {state.project}, 버전: {state.version}, 기능: {state.feature}",
    )

    if not tc_result.success:
        log("ERROR", f"TC 작성 실패: {tc_result.error}")
        return "escalated"

    tc_path = tc_result.output_file or str(
        build_artifact_path("write-tc", state.project, state.version, state.feature)
    )
    state.artifacts["tc"] = tc_path
    state.save()

    # ---- Step 2: 포맷 검증 ----
    for fmt_attempt in range(MAX_RETRIES + 1):
        log("INFO", f"Phase 1-B Step 2: 포맷 검증 (시도 {fmt_attempt + 1})")
        format_result = invoke_skill("check-format", tc_path, state, phase="1-B")

        if not format_result.success:
            log("ERROR", f"포맷 검증 호출 실패: {format_result.error}")
            return "escalated"

        state.artifacts["format_check"] = format_result.output_file
        state.save()

        format_verdict = _parse_format_verdict(format_result)

        if format_verdict == "PASS":
            log("INFO", "포맷 검증 PASS")
            send_progress_notification(
                common_config, env_config, state,
                "TC 작성 완료, 포맷 검증 Pass. 내용 리뷰 진행합니다.",
                no_slack=no_slack,
            )
            break

        if fmt_attempt >= MAX_RETRIES:
            log("WARN", "포맷 검증 한도 초과. 에스컬레이션.")
            return "escalated"

        log("INFO", f"포맷 검증 FAIL. TC 재작업 ({fmt_attempt + 1}회)")
        state.increment_rework("write-tc")

        rework_result = invoke_skill(
            "write-tc", scenario_file, state, phase="1-B",
            retry_number=fmt_attempt + 1,
            extra_context=f"양식 검증에서 오류가 발견되었습니다.\n"
                         f"양식 검증 결과 파일: {format_result.output_file}\n"
                         f"오류를 모두 수정하세요.",
        )

        if rework_result.success and rework_result.output_file:
            tc_path = rework_result.output_file
            state.artifacts["tc"] = tc_path
            state.save()

    # ---- Step 3-4: 내용 리뷰 루프 ----
    log("INFO", "Phase 1-B Step 3: 내용 리뷰 게이트")

    def rework_builder(feedback_paths):
        feedback_str = ", ".join(feedback_paths)
        extra = f"리뷰 피드백 파일: {feedback_str}\n피드백을 모두 반영하여 TC를 수정하세요."
        return ("write-tc", scenario_file, extra)

    review_skills = [
        ("review-spec", tc_path),
        ("review-qa", tc_path),
    ]

    passed, review_results = run_review_gate(
        writer_skill="write-tc",
        writer_args=scenario_file,
        reviewer_skills=review_skills,
        state=state,
        phase="1-B",
        rework_prompt_builder=rework_builder,
    )

    if not passed:
        log("WARN", "TC 리뷰 게이트 실패. 에스컬레이션.")
        send_approval_notification(
            common_config, env_config, state, "escalation",
            "TC 리뷰 3회 재작업 후에도 통과하지 못했습니다.",
            no_slack=no_slack,
        )
        return "escalated"

    for skill_name, result in review_results:
        if "review-spec" in skill_name and result.output_file:
            state.artifacts["tc_review_spec"] = result.output_file
        elif "review-qa" in skill_name and result.output_file:
            state.artifacts["tc_review_qa"] = result.output_file
    state.save()

    # ---- Step 5: 승인 3 ----
    send_approval_notification(
        common_config, env_config, state, "3_tc_final",
        "TC 리뷰가 Pass 되었습니다. TC 확정 확인 부탁드립니다.",
        no_slack=no_slack,
    )

    approval = ask_approval(
        "3", "TC 확정",
        f"  TC 파일: {state.artifacts['tc']}\n  포맷 검증: PASS\n  리뷰 결과: 전원 PASS",
    )
    state.set_approval("3_tc_final", approval)

    if approval == "rejected":
        return "rejected"

    # ---- Google Sheet 업로드 ----
    gsheet_url = project_config.gsheet_url
    if gsheet_url:
        print(f"  저장된 Google Sheet URL 사용: {gsheet_url}")
    else:
        gsheet_url = ask_url("Google Sheet URL")
        if gsheet_url:
            from orchestrator.config import save_project_gsheet_url
            save_project_gsheet_url(state.project, gsheet_url)

    if gsheet_url:
        sheet_name = f"{state.project}_{state.feature}"
        print(f"\n  업로드 대상:")
        print(f"    Google Sheet: {gsheet_url}")
        print(f"    시트명: {sheet_name}")
        print(f"    TC 파일: {state.artifacts['tc']}")

        upload_url = upload_tc_to_gsheet(
            state.artifacts["tc"], gsheet_url, env_config, state,
        )
        if upload_url:
            state.upload_urls["tc_gsheet"] = upload_url
            state.save()
            print(f"  Google Sheet 업로드 완료: {upload_url}")

    state.advance_phase("3")
    return "continue"


def _parse_format_verdict(result) -> str:
    """포맷 검증 결과에서 PASS/FAIL 추출."""
    if result.output_file:
        try:
            with open(result.output_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data.get("result", "FAIL").upper()
        except Exception:
            pass
    text = result.output.upper()
    if '"RESULT": "PASS"' in text:
        return "PASS"
    return "FAIL"
