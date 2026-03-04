"""파일명 규칙 빌더. CLAUDE.md Section 5 네이밍 규칙 준수."""

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent  # qa_agent/


def sanitize_feature_name(feature: str) -> str:
    """공백을 언더스코어로 치환. 한글 유지."""
    return feature.replace(" ", "_")


def build_artifact_path(
    skill_name: str,
    project: str,
    version: str,
    feature: str,
) -> Path:
    """스킬별 산출물 파일 경로 생성. {PROJECT}_{version}_{feature}_{type}.{ext}"""
    project_upper = project.upper()
    safe_feature = sanitize_feature_name(feature)
    prefix = f"{project_upper}_{version}_{safe_feature}"

    paths = {
        "write-scenario": BASE_DIR / "data" / "scenarios" / f"{prefix}_scenario.md",
        "write-tc": BASE_DIR / "data" / "tc" / f"{prefix}_tc.json",
        "review-spec": BASE_DIR / "data" / "reviews" / f"{prefix}_review-spec.json",
        "review-qa": BASE_DIR / "data" / "reviews" / f"{prefix}_review-qa.json",
        "check-format": BASE_DIR / "data" / "reviews" / f"{prefix}_format-check.json",
        "assess-automation": BASE_DIR / "data" / "assessments" / f"{prefix}_assessment.json",
        "write-test-code": BASE_DIR / "tests" / f"test_{prefix}.py",
        "analyze-fail": BASE_DIR / "data" / "fail_analysis" / f"{prefix}_fail-analysis.json",
        "report-project": BASE_DIR / "data" / "pipeline" / f"{project_upper}_{version}_report.json",
        "analyze-impact": BASE_DIR / "data" / "reviews" / f"{prefix}_impact.json",
        "report-bug": BASE_DIR / "data" / "bugs" / f"{prefix}_bug.json",
    }

    return paths.get(skill_name, BASE_DIR / "data" / f"{prefix}_{skill_name}.json")
