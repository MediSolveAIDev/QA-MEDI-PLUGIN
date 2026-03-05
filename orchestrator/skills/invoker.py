"""claude -p subprocess 래퍼. 스킬 단일/병렬 호출."""

import json
import os
import re
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from orchestrator.config import BASE_DIR
from orchestrator.state import AgentLogEntry, PipelineState
from orchestrator.utils.logger import log

MAX_PROMPT_LENGTH = 50000


@dataclass
class SkillResult:
    success: bool
    output: str
    output_file: Optional[str]
    duration_seconds: float
    error: Optional[str] = None


def invoke_skill(
    skill_name: str,
    arguments: str,
    state: PipelineState,
    phase: str,
    timeout_seconds: int = 600,
    retry_number: int = 0,
    extra_context: str = "",
) -> SkillResult:
    """claude -p로 스킬 1회 호출."""
    from orchestrator.skills.prompts import get_skill_prompt

    prompt = get_skill_prompt(skill_name, arguments, extra_context)
    if len(prompt) > MAX_PROMPT_LENGTH:
        log("WARN", f"프롬프트 길이 초과, {MAX_PROMPT_LENGTH}자로 절삭")
        prompt = prompt[:MAX_PROMPT_LENGTH]

    log_entry = AgentLogEntry(
        timestamp=time.strftime("%Y-%m-%dT%H:%M:%S"),
        agent=skill_name,
        action="invoke",
        phase=phase,
        retry_number=retry_number,
    )

    start_time = time.time()

    try:
        cmd = [
            "claude",
            "-p",
            prompt,
            "--dangerously-skip-permissions",
        ]

        log("INFO", f"스킬 호출: /{skill_name}", {"phase": phase})

        env = os.environ.copy()
        env.pop("CLAUDECODE", None)

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=timeout_seconds,
            cwd=str(BASE_DIR),
            env=env,
        )

        duration = time.time() - start_time

        if result.returncode == 0:
            output_file = _detect_output_file(skill_name, state)
            # 스킬이 파일을 직접 저장하지 않은 경우, stdout에서 JSON을 추출하여 저장
            if not output_file:
                output_file = _save_output_from_stdout(
                    skill_name, state, result.stdout
                )
            log_entry.action = "complete"
            log_entry.output_files = [output_file] if output_file else []
            log_entry.duration_seconds = duration
            state.log_agent(log_entry)

            return SkillResult(
                success=True,
                output=result.stdout,
                output_file=output_file,
                duration_seconds=duration,
            )
        else:
            log_entry.action = "fail"
            log_entry.error = result.stderr[:500]
            log_entry.duration_seconds = duration
            state.log_agent(log_entry)

            return SkillResult(
                success=False,
                output=result.stdout,
                output_file=None,
                duration_seconds=duration,
                error=result.stderr[:500],
            )

    except subprocess.TimeoutExpired:
        duration = time.time() - start_time
        log_entry.action = "fail"
        log_entry.error = f"타임아웃 ({timeout_seconds}초)"
        log_entry.duration_seconds = duration
        state.log_agent(log_entry)

        return SkillResult(
            success=False,
            output="",
            output_file=None,
            duration_seconds=duration,
            error=f"스킬 타임아웃 ({timeout_seconds}초 초과)",
        )

    except Exception as e:
        duration = time.time() - start_time
        log_entry.action = "fail"
        log_entry.error = str(e)[:500]
        log_entry.duration_seconds = duration
        state.log_agent(log_entry)

        return SkillResult(
            success=False,
            output="",
            output_file=None,
            duration_seconds=duration,
            error=str(e),
        )


def invoke_parallel_skills(
    skills: list[tuple[str, str]],
    state: PipelineState,
    phase: str,
    timeout_seconds: int = 600,
) -> list[tuple[str, SkillResult]]:
    """복수 스킬 병렬 호출 (review-spec + review-qa 등)."""
    results = []
    with ThreadPoolExecutor(max_workers=len(skills)) as executor:
        futures = {
            executor.submit(
                invoke_skill, name, args, state, phase, timeout_seconds
            ): name
            for name, args in skills
        }

        for future in as_completed(futures):
            skill_name = futures[future]
            try:
                result = future.result()
                results.append((skill_name, result))
            except Exception as e:
                results.append((skill_name, SkillResult(
                    success=False, output="", output_file=None,
                    duration_seconds=0, error=str(e),
                )))

    return results


def _detect_output_file(skill_name: str, state: PipelineState) -> Optional[str]:
    """스킬 실행 후 네이밍 규칙으로 산출물 파일 탐지."""
    from orchestrator.utils.files import build_artifact_path
    expected_path = build_artifact_path(
        skill_name, state.project, state.version, state.feature
    )
    if expected_path and Path(expected_path).exists():
        return str(expected_path)
    return None


def _save_output_from_stdout(
    skill_name: str, state: PipelineState, stdout: str
) -> Optional[str]:
    """stdout에서 산출물을 추출하여 예상 경로에 저장."""
    from orchestrator.utils.files import build_artifact_path

    expected_path = build_artifact_path(
        skill_name, state.project, state.version, state.feature
    )
    if not expected_path:
        return None

    suffix = expected_path.suffix.lower()

    if suffix == ".json":
        content = _extract_json_from_text(stdout)
    elif suffix == ".md":
        content = _extract_markdown_from_text(stdout)
    elif suffix == ".py":
        content = _extract_code_from_text(stdout, "python")
    else:
        content = None

    if not content:
        return None

    # 디렉토리 생성 후 저장
    expected_path.parent.mkdir(parents=True, exist_ok=True)
    expected_path.write_text(content, encoding="utf-8")
    log("INFO", f"산출물 저장: {expected_path}")
    return str(expected_path)


def _extract_json_from_text(text: str) -> Optional[str]:
    """텍스트에서 JSON 블록을 추출. 코드블록 우선, 없으면 최상위 {} 탐지."""
    # 1) ```json ... ``` 코드블록에서 추출
    pattern = r"```json\s*\n(.*?)\n\s*```"
    matches = re.findall(pattern, text, re.DOTALL)
    if matches:
        # 가장 큰 JSON 블록 사용 (리뷰 결과가 보통 가장 큼)
        candidate = max(matches, key=len)
        try:
            parsed = json.loads(candidate)
            return json.dumps(parsed, ensure_ascii=False, indent=2)
        except json.JSONDecodeError:
            pass

    # 2) 최상위 { ... } 블록 탐지
    brace_depth = 0
    start = -1
    for i, ch in enumerate(text):
        if ch == "{":
            if brace_depth == 0:
                start = i
            brace_depth += 1
        elif ch == "}":
            brace_depth -= 1
            if brace_depth == 0 and start >= 0:
                candidate = text[start : i + 1]
                try:
                    parsed = json.loads(candidate)
                    # 리뷰 결과 JSON인지 확인 (verdict 또는 reviewer 키 존재)
                    if isinstance(parsed, dict) and (
                        "verdict" in parsed or "reviewer" in parsed
                    ):
                        return json.dumps(parsed, ensure_ascii=False, indent=2)
                except json.JSONDecodeError:
                    pass
                start = -1

    return None


def _extract_markdown_from_text(text: str) -> Optional[str]:
    """stdout에서 마크다운 콘텐츠를 추출. ```markdown 코드블록 우선, 없으면 헤딩 기반 추출."""
    # 1) ```markdown ... ``` 코드블록
    pattern = r"```markdown\s*\n(.*?)\n\s*```"
    matches = re.findall(pattern, text, re.DOTALL)
    if matches:
        return max(matches, key=len).strip()

    # 2) 마크다운 헤딩(#)이 포함된 구간 추출
    lines = text.split("\n")
    md_start = -1
    for i, line in enumerate(lines):
        if re.match(r"^#{1,3}\s+", line):
            md_start = i
            break

    if md_start >= 0:
        return "\n".join(lines[md_start:]).strip()

    return None


def _extract_code_from_text(text: str, language: str) -> Optional[str]:
    """stdout에서 코드 블록을 추출."""
    pattern = rf"```{language}\s*\n(.*?)\n\s*```"
    matches = re.findall(pattern, text, re.DOTALL)
    if matches:
        return max(matches, key=len).strip()
    return None
