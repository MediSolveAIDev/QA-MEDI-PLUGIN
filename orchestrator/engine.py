"""메인 오케스트레이션 엔진: 페이즈 조율, 상태 관리, 병렬 실행."""

import asyncio
from datetime import datetime
from typing import Optional

from orchestrator.cli import ask_input, set_auto_approve
from orchestrator.config import (
    CommonConfig,
    EnvConfig,
    ProjectConfig,
    load_common_config,
    load_env,
    load_project_config,
    validate_setup,
)
from orchestrator.state import PipelineState
from orchestrator.utils.logger import log


class PipelineEngine:
    def __init__(self, args):
        self.args = args
        self.common_config: Optional[CommonConfig] = None
        self.env_config: Optional[EnvConfig] = None

    def _preflight_check(self):
        """실행 전 환경 검증."""
        issues = validate_setup()
        if issues:
            print("\n  환경 설정 문제 발견:")
            for issue in issues:
                print(f"    - {issue}")
            raise SystemExit(1)

        self.common_config = load_common_config()
        self.env_config = load_env()

    def run(self):
        """단일 프로젝트 파이프라인 실행."""
        self._preflight_check()
        if self.args.auto_approve:
            set_auto_approve(True)
        no_slack = self.args.no_slack

        # 기획서 변경 대응
        if self.args.resume and self.args.spec_update:
            state = PipelineState.load(self.args.resume)
            project_config = load_project_config(state.project)
            self._handle_spec_update(state, project_config, no_slack)
            return

        # 재개 또는 신규
        if self.args.resume:
            state = PipelineState.load(self.args.resume)
            log("INFO", f"파이프라인 재개: {state.pipeline_id} (Phase {state.current_phase})")
        else:
            state = self._collect_input()

        project_config = load_project_config(state.project)
        start_phase = self.args.phase or state.current_phase

        try:
            self._run_from_phase(state, project_config, start_phase, no_slack)
        except KeyboardInterrupt:
            state.status = "paused"
            state.save()
            log("INFO", f"파이프라인 일시정지: {state.pipeline_id}")
            print(f"\n  파이프라인 일시정지됨. 재개:")
            print(f"  python -m orchestrator --resume {state.pipeline_id}")

    def _run_from_phase(
        self,
        state: PipelineState,
        project_config: ProjectConfig,
        start_phase: str,
        no_slack: bool = False,
    ):
        """지정 Phase부터 순차 실행."""
        from orchestrator.phases.phase0_input import run_phase0
        from orchestrator.phases.phase1a_scenario import run_phase1a
        from orchestrator.phases.phase1b_tc import run_phase1b
        from orchestrator.phases.phase3_automation import run_phase3
        from orchestrator.phases.phase4_report import run_phase4

        phases = [
            ("0", run_phase0),
            ("1-A", run_phase1a),
            ("1-B", run_phase1b),
            ("3", run_phase3),
            ("4", run_phase4),
        ]

        phase_names = [p[0] for p in phases]
        try:
            start_idx = phase_names.index(start_phase)
        except ValueError:
            start_idx = 0

        # 단일 Phase 실행
        if self.args.phase:
            phase_name, phase_fn = phases[start_idx]
            state.current_phase = phase_name
            state.status = "in_progress"
            state.save()
            phase_fn(state, project_config, self.common_config, self.env_config, no_slack)
            return

        # 전체 실행
        for phase_name, phase_fn in phases[start_idx:]:
            state.current_phase = phase_name
            state.status = "in_progress"
            state.save()

            log("INFO", f"Phase {phase_name} 시작")
            result = phase_fn(
                state, project_config, self.common_config, self.env_config, no_slack
            )

            if result == "escalated":
                state.status = "escalated"
                state.save()
                log("WARN", f"Phase {phase_name}에서 에스컬레이션")
                return
            elif result == "rejected":
                state.status = "failed"
                state.save()
                log("ERROR", f"Phase {phase_name}에서 거부됨")
                return

        state.status = "completed"
        state.save()
        log("INFO", f"파이프라인 완료: {state.pipeline_id}")

    def _collect_input(self) -> PipelineState:
        """신규 파이프라인 정보 수집."""
        projects = self.args.parallel_projects
        project = projects[0] if projects else None
        version = self.args.version
        feature = self.args.feature
        spec_url = self.args.spec_url

        if not project:
            project = ask_input("프로젝트 코드 (SAY/BAY/SSO)", required=True).upper()
        if not version:
            try:
                pc = load_project_config(project)
                default_ver = pc.current_version
            except FileNotFoundError:
                default_ver = ""
            version = ask_input(f"버전 (기본: {default_ver})") or default_ver
        if not feature:
            feature = ask_input("기능명", required=True)
        if not spec_url:
            spec_url = ask_input("Confluence 기획서 URL 또는 Page ID", required=True)

        state = PipelineState(
            project=project,
            version=version,
            feature=feature,
            spec_url=spec_url,
            started_at=datetime.now().isoformat(),
            current_phase="0",
            status="in_progress",
        )
        state.save()
        return state

    def _handle_spec_update(
        self, state: PipelineState, project_config: ProjectConfig, no_slack: bool
    ):
        """기획서 변경 대응 실행."""
        from orchestrator.phases.spec_update import run_spec_update

        result = run_spec_update(
            state,
            self.args.spec_update,
            project_config,
            self.common_config,
            self.env_config,
            no_slack=no_slack,
        )

        if result == "tc_update":
            # Phase 1-B부터 재실행
            self._run_from_phase(state, project_config, "1-B", no_slack)

    async def run_parallel(self, projects: list[str]):
        """복수 프로젝트 병렬 실행."""
        self._preflight_check()

        tasks = []
        for project_code in projects:
            task = asyncio.to_thread(self._run_single_project, project_code)
            tasks.append(task)

        await asyncio.gather(*tasks)

    def _run_single_project(self, project_code: str):
        """단일 프로젝트 파이프라인 (병렬용)."""
        log("INFO", f"병렬 파이프라인 시작: {project_code}")

        project_config = load_project_config(project_code)

        state = PipelineState(
            project=project_code,
            version=self.args.version or project_config.current_version,
            feature=self.args.feature or "",
            spec_url=self.args.spec_url or "",
            started_at=datetime.now().isoformat(),
            current_phase="0",
            status="in_progress",
        )
        state.save()

        self._run_from_phase(state, project_config, "0", self.args.no_slack)
