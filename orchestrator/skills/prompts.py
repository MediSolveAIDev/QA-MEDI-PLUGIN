"""스킬별 프롬프트 템플릿. claude -p에 전달할 프롬프트 생성."""

from orchestrator.utils.files import build_artifact_path


def get_skill_prompt(
    skill_name: str,
    arguments: str,
    extra_context: str = "",
    project: str = "",
    version: str = "",
    feature: str = "",
) -> str:
    """스킬 이름에 맞는 프롬프트 반환."""
    # 산출물 저장 경로 생성
    save_path = ""
    if project and version and feature:
        path = build_artifact_path(skill_name, project, version, feature)
        if path:
            save_path = str(path)

    builders = {
        "write-scenario": _write_scenario,
        "write-tc": _write_tc,
        "review-spec": _review_spec,
        "review-qa": _review_qa,
        "check-format": _check_format,
        "assess-automation": _assess_automation,
        "write-test-code": _write_test_code,
        "analyze-fail": _analyze_fail,
        "report-project": _report_project,
        "analyze-impact": _analyze_impact,
        "upload-report": _upload_report,
        "share-slack": _share_slack,
    }

    builder = builders.get(skill_name)
    if not builder:
        prompt = f"/{skill_name} {arguments}"
        if extra_context:
            prompt += f"\n\n{extra_context}"
        if save_path:
            prompt += f"\n\n결과를 반드시 다음 경로에 저장하세요: {save_path}"
        return prompt

    prompt = builder(arguments, extra_context)
    if save_path:
        prompt += f"\n\n결과를 반드시 다음 경로에 저장하세요: {save_path}"
    return prompt


def _write_scenario(args: str, extra: str) -> str:
    prompt = f"""/write-scenario {args}

Confluence 기획서/정책서를 참고하여 테스트 시나리오를 작성해주세요.
시나리오 작성 시 반드시 기획서/정책서 내용(우선순위 1)을 기준으로 작성하세요."""
    if extra:
        prompt += f"\n\n추가 컨텍스트:\n{extra}"
    return prompt


def _write_tc(args: str, extra: str) -> str:
    prompt = f"""/write-tc {args}

확정 시나리오를 기반으로 TC를 JSON 형식으로 작성해주세요.
모든 TC 작성 규칙(Depth 구조, Expected Result 규칙, 금지 용어 등)을 준수하세요."""
    if extra:
        prompt += f"\n\n추가 컨텍스트:\n{extra}"
    return prompt


def _review_spec(args: str, extra: str) -> str:
    prompt = f"""/review-spec {args}

기획서/정책서 기준으로 리뷰해주세요.
"기획서에 있는 걸 다 했나?" 관점에서 커버리지와 누락사항을 분석하세요.
결과를 JSON 형식으로 출력하세요."""
    if extra:
        prompt += f"\n\n{extra}"
    return prompt


def _review_qa(args: str, extra: str) -> str:
    prompt = f"""/review-qa {args}

QA 관점에서 크로스 체크해주세요.
"기획서에 없지만 놓치면 안 되는 건?" 관점에서 엣지케이스, 네거티브 시나리오를 분석하세요.
결과를 JSON 형식으로 출력하세요."""
    if extra:
        prompt += f"\n\n{extra}"
    return prompt


def _check_format(args: str, extra: str) -> str:
    prompt = f"""/check-format {args}

TC의 양식 준수 여부를 검증해주세요.
Depth 구조, Expected Result 규칙, 금지 용어, Priority 등 모든 양식 규칙을 체크하세요.
결과를 JSON 형식으로 출력하세요."""
    if extra:
        prompt += f"\n\n{extra}"
    return prompt


def _assess_automation(args: str, extra: str) -> str:
    prompt = f"""/assess-automation {args}

확정된 TC의 자동화 가능 여부를 검토해주세요.
TC별 자동화 가능성, 우선순위, 제약 사항을 분석하세요.
결과를 JSON 형식으로 출력하세요."""
    if extra:
        prompt += f"\n\n{extra}"
    return prompt


def _write_test_code(args: str, extra: str) -> str:
    prompt = f"""/write-test-code {args}

TC를 기반으로 pytest + playwright 자동화 테스트 코드를 생성해주세요.
Soft Assertion(ChecklistReporter) 패턴을 적용하세요."""
    if extra:
        prompt += f"\n\n{extra}"
    return prompt


def _analyze_fail(args: str, extra: str) -> str:
    prompt = f"""/analyze-fail {args}

FAIL 테스트 결과를 분석하고 분류해주세요.
코드 이슈 / 실제 버그 / 환경 이슈 / TC 오류로 분류하세요.
결과를 JSON 형식으로 출력하세요."""
    if extra:
        prompt += f"\n\n{extra}"
    return prompt


def _report_project(args: str, extra: str) -> str:
    prompt = f"""/report-project {args}

프로젝트 QA 현황을 종합하여 리포트를 생성해주세요.
TC 현황, 실행 현황, 자동화 현황을 포함하세요."""
    if extra:
        prompt += f"\n\n{extra}"
    return prompt


def _analyze_impact(args: str, extra: str) -> str:
    prompt = f"""/analyze-impact {args}

크로스 프로젝트 영향도를 분석해주세요.
현재 변경이 다른 프로젝트에 미치는 영향을 파악하세요."""
    if extra:
        prompt += f"\n\n{extra}"
    return prompt


def _upload_report(args: str, extra: str) -> str:
    prompt = f"""/upload-report {args}"""
    if extra:
        prompt += f"\n\n{extra}"
    return prompt


def _share_slack(args: str, extra: str) -> str:
    prompt = f"""/share-slack {args}"""
    if extra:
        prompt += f"\n\n{extra}"
    return prompt
