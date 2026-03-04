"""claude -p subprocess 래퍼. 스킬 단일/병렬 호출."""

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

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=timeout_seconds,
            cwd=str(BASE_DIR),
        )

        duration = time.time() - start_time

        if result.returncode == 0:
            output_file = _detect_output_file(skill_name, state)
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
