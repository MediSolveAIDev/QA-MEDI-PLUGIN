"""파이프라인 상태 영속화. data/pipeline/{PROJECT}_{ver}_pipeline.json"""

import json
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Optional, Literal

ApprovalStatus = Literal["pending", "approved", "rejected", "rework", None]
PipelineStatus = Literal[
    "not_started", "in_progress", "paused", "completed", "failed", "escalated"
]


@dataclass
class AgentLogEntry:
    timestamp: str
    agent: str
    action: str  # "invoke", "complete", "fail", "retry"
    phase: str
    input_files: list[str] = field(default_factory=list)
    output_files: list[str] = field(default_factory=list)
    verdict: Optional[str] = None
    duration_seconds: Optional[float] = None
    error: Optional[str] = None
    retry_number: int = 0


@dataclass
class PipelineState:
    project: str
    version: str
    feature: str
    spec_url: str = ""
    started_at: str = ""
    updated_at: str = ""
    current_phase: str = "0"
    status: PipelineStatus = "not_started"

    approvals: dict = field(default_factory=lambda: {
        "0_plan": None,
        "1_scenario_review": None,
        "2_scenario_final": None,
        "3_tc_final": None,
        "4_automation": None,
        "5_fail_analysis": None,
        "6_cross_project": None,
    })

    rework_count: dict = field(default_factory=lambda: {
        "write-scenario": 0,
        "write-tc": 0,
    })

    artifacts: dict = field(default_factory=lambda: {
        "scenario": None,
        "scenario_review_spec": None,
        "scenario_review_qa": None,
        "tc": None,
        "format_check": None,
        "tc_review_spec": None,
        "tc_review_qa": None,
        "assessment": None,
        "test_code": None,
        "fail_analysis": None,
        "report": None,
        "impact": None,
    })

    upload_urls: dict = field(default_factory=lambda: {
        "scenario_confluence": None,
        "tc_gsheet": None,
    })

    spec_updates: list = field(default_factory=list)
    agents_log: list = field(default_factory=list)

    # --- 편의 프로퍼티 ---

    @property
    def pipeline_id(self) -> str:
        return f"{self.project}_{self.version}"

    @property
    def file_path(self) -> Path:
        from orchestrator.utils.files import BASE_DIR
        return BASE_DIR / "data" / "pipeline" / f"{self.pipeline_id}_pipeline.json"

    # --- 영속화 ---

    def save(self):
        self.updated_at = datetime.now().isoformat()
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump(asdict(self), f, ensure_ascii=False, indent=2)

    @classmethod
    def load(cls, pipeline_id: str) -> "PipelineState":
        from orchestrator.utils.files import BASE_DIR
        path = BASE_DIR / "data" / "pipeline" / f"{pipeline_id}_pipeline.json"
        if not path.exists():
            raise FileNotFoundError(f"파이프라인 상태 파일 없음: {path}")
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        state = cls(
            project=data["project"],
            version=data["version"],
            feature=data["feature"],
        )
        for key, val in data.items():
            if hasattr(state, key):
                setattr(state, key, val)
        return state

    @classmethod
    def exists(cls, pipeline_id: str) -> bool:
        from orchestrator.utils.files import BASE_DIR
        path = BASE_DIR / "data" / "pipeline" / f"{pipeline_id}_pipeline.json"
        return path.exists()

    # --- 상태 조작 ---

    def log_agent(self, entry: AgentLogEntry):
        self.agents_log.append(asdict(entry))
        self.save()

    def set_approval(self, key: str, value: ApprovalStatus):
        self.approvals[key] = value
        self.save()

    def increment_rework(self, skill: str) -> int:
        if skill not in self.rework_count:
            self.rework_count[skill] = 0
        self.rework_count[skill] += 1
        self.save()
        return self.rework_count[skill]

    def advance_phase(self, next_phase: str):
        self.current_phase = next_phase
        self.save()

    def record_spec_update(self, new_url: str, choice: str):
        self.spec_updates.append({
            "timestamp": datetime.now().isoformat(),
            "new_spec_url": new_url,
            "choice": choice,  # "resume" or "tc_update"
        })
        self.save()
