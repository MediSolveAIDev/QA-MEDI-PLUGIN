"""Spec Reviewer + QA Reviewer 판정 병합."""

import json
from dataclasses import dataclass, field
from typing import Optional

from orchestrator.skills.invoker import SkillResult
from orchestrator.state import PipelineState


@dataclass
class MergedVerdict:
    passed: bool
    spec_verdict: str
    qa_verdict: str
    final_verdict: str
    feedback_paths: list[str] = field(default_factory=list)
    summary: str = ""


def merge_review_verdicts(
    review_results: list[tuple[str, SkillResult]],
    state: PipelineState,
) -> MergedVerdict:
    """
    Spec Reviewer + QA Reviewer 결과 병합.

    규칙 (SKILL.md):
    - 둘 다 Pass → Pass
    - 하나라도 Feedback → Feedback
    - 하나라도 Fail → Fail (재작업 목적상 Feedback으로 처리)
    """
    spec_verdict = "PASS"
    qa_verdict = "PASS"
    feedback_paths = []

    for skill_name, result in review_results:
        if not result.success:
            if "review-spec" in skill_name:
                spec_verdict = "FEEDBACK"
            elif "review-qa" in skill_name:
                qa_verdict = "FEEDBACK"
            continue

        verdict = _extract_verdict(result)

        if "review-spec" in skill_name:
            spec_verdict = verdict
            if result.output_file:
                feedback_paths.append(result.output_file)
        elif "review-qa" in skill_name:
            qa_verdict = verdict
            if result.output_file:
                feedback_paths.append(result.output_file)

    if spec_verdict == "PASS" and qa_verdict == "PASS":
        final = "PASS"
        passed = True
    else:
        final = "FEEDBACK"
        passed = False

    return MergedVerdict(
        passed=passed,
        spec_verdict=spec_verdict,
        qa_verdict=qa_verdict,
        final_verdict=final,
        feedback_paths=feedback_paths,
        summary=f"Spec: {spec_verdict}, QA: {qa_verdict} → {final}",
    )


def _extract_verdict(result: SkillResult) -> str:
    """리뷰 JSON 출력에서 verdict 필드 추출."""
    if result.output_file:
        try:
            with open(result.output_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            verdict = data.get("verdict", data.get("result", "FEEDBACK"))
            return verdict.upper()
        except (json.JSONDecodeError, FileNotFoundError):
            pass

    text = result.output.upper()
    if '"VERDICT": "PASS"' in text or '"RESULT": "PASS"' in text:
        return "PASS"
    return "FEEDBACK"
