"""품질 게이트: 리뷰 → 재작업 루프 (최대 3회)."""

from typing import Callable

from orchestrator.review.merger import merge_review_verdicts, MergedVerdict
from orchestrator.skills.invoker import (
    invoke_skill,
    invoke_parallel_skills,
    SkillResult,
)
from orchestrator.state import PipelineState
from orchestrator.utils.logger import log

MAX_RETRIES = 3


def run_review_gate(
    writer_skill: str,
    writer_args: str,
    reviewer_skills: list[tuple[str, str]],
    state: PipelineState,
    phase: str,
    rework_prompt_builder: Callable,
) -> tuple[bool, list[tuple[str, SkillResult]]]:
    """
    작성 → 리뷰 → 재작업 루프 실행.

    Returns:
        (passed, review_results)
    """
    review_results = []

    for attempt in range(MAX_RETRIES + 1):
        if attempt > 0:
            log("INFO", f"재작업 {attempt}/{MAX_RETRIES}: {writer_skill}")

        # 리뷰어 병렬 호출
        review_results = invoke_parallel_skills(reviewer_skills, state, phase)

        # 판정 병합
        merged = merge_review_verdicts(review_results, state)
        log("INFO", f"리뷰 결과: {merged.summary}")

        if merged.passed:
            log("INFO", f"리뷰 게이트 PASS: {writer_skill}")
            return True, review_results

        # 재작업 횟수 확인
        current_count = state.increment_rework(writer_skill)
        if current_count > MAX_RETRIES:
            log("WARN", f"재작업 한도 초과: {writer_skill}. 에스컬레이션.")
            return False, review_results

        # 재작업 프롬프트 생성
        rework_skill, rework_args, rework_extra = rework_prompt_builder(
            merged.feedback_paths
        )

        # writer에 재작업 지시
        rework_result = invoke_skill(
            rework_skill,
            rework_args,
            state,
            phase,
            retry_number=current_count,
            extra_context=(
                f"이것은 재작업 {current_count}회차입니다. "
                f"리뷰 피드백을 반드시 반영하세요.\n{rework_extra}"
            ),
        )

        if not rework_result.success:
            log("ERROR", f"재작업 실패: {writer_skill}")
            return False, review_results

    return False, review_results
