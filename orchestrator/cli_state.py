"""파이프라인 상태 CLI 유틸. Claude Code 대화에서 Bash로 호출."""

import json
import sys
from pathlib import Path

from orchestrator.config import BASE_DIR
from orchestrator.state import PipelineState


def cmd_init(project: str, version: str, feature: str, spec_url: str):
    """신규 파이프라인 생성."""
    from datetime import datetime

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
    print(json.dumps({"pipeline_id": state.pipeline_id, "path": str(state.file_path)}))


def cmd_status(pipeline_id: str):
    """파이프라인 상태 조회."""
    if pipeline_id == "latest":
        pipeline_dir = BASE_DIR / "data" / "pipeline"
        if not pipeline_dir.exists():
            print(json.dumps({"error": "파이프라인 기록 없음"}))
            return
        files = sorted(pipeline_dir.glob("*_pipeline.json"), key=lambda f: f.stat().st_mtime, reverse=True)
        if not files:
            print(json.dumps({"error": "파이프라인 기록 없음"}))
            return
        pipeline_id = files[0].stem.replace("_pipeline", "")

    try:
        state = PipelineState.load(pipeline_id)
    except FileNotFoundError:
        print(json.dumps({"error": f"파이프라인 없음: {pipeline_id}"}))
        return

    from dataclasses import asdict
    print(json.dumps(asdict(state), ensure_ascii=False, indent=2))


def cmd_update(pipeline_id: str, field: str, value: str):
    """파이프라인 필드 업데이트."""
    state = PipelineState.load(pipeline_id)

    if field == "phase":
        state.advance_phase(value)
    elif field == "status":
        state.status = value
        state.save()
    elif field.startswith("approval."):
        key = field.split(".", 1)[1]
        state.set_approval(key, value)
    elif field.startswith("artifact."):
        key = field.split(".", 1)[1]
        state.artifacts[key] = value
        state.save()
    elif field.startswith("upload."):
        key = field.split(".", 1)[1]
        state.upload_urls[key] = value
        state.save()
    elif field == "rework":
        count = state.increment_rework(value)
        print(json.dumps({"skill": value, "count": count}))
        return
    elif field == "spec_url":
        state.spec_url = value
        state.save()
    else:
        print(json.dumps({"error": f"알 수 없는 필드: {field}"}))
        return

    print(json.dumps({"ok": True, "field": field, "value": value}))


def cmd_notify(pipeline_id: str, notify_type: str, message: str):
    """Slack 알림 발송."""
    from orchestrator.config import load_common_config, load_env
    from orchestrator.notify.slack import send_approval_notification, send_progress_notification

    state = PipelineState.load(pipeline_id)
    common = load_common_config()
    env = load_env()

    if notify_type == "approval":
        approval_key = message.split("|", 1)[0]
        msg = message.split("|", 1)[1] if "|" in message else ""
        send_approval_notification(common, env, state, approval_key, msg)
    elif notify_type == "progress":
        send_progress_notification(common, env, state, message)

    print(json.dumps({"ok": True, "type": notify_type}))


def cmd_list():
    """진행 중인 파이프라인 목록."""
    pipeline_dir = BASE_DIR / "data" / "pipeline"
    if not pipeline_dir.exists():
        print(json.dumps([]))
        return

    pipelines = []
    for f in sorted(pipeline_dir.glob("*_pipeline.json"), key=lambda f: f.stat().st_mtime, reverse=True):
        with open(f, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        pipelines.append({
            "pipeline_id": f.stem.replace("_pipeline", ""),
            "project": data.get("project"),
            "version": data.get("version"),
            "feature": data.get("feature"),
            "phase": data.get("current_phase"),
            "status": data.get("status"),
            "updated_at": data.get("updated_at"),
        })

    print(json.dumps(pipelines, ensure_ascii=False, indent=2))


def main():
    if len(sys.argv) < 2:
        print("Usage: python -m orchestrator.cli_state <command> [args]")
        print("Commands: init, status, update, notify, list")
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "init" and len(sys.argv) >= 6:
        cmd_init(sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5])
    elif cmd == "status" and len(sys.argv) >= 3:
        cmd_status(sys.argv[2])
    elif cmd == "update" and len(sys.argv) >= 5:
        cmd_update(sys.argv[2], sys.argv[3], sys.argv[4])
    elif cmd == "notify" and len(sys.argv) >= 5:
        cmd_notify(sys.argv[2], sys.argv[3], sys.argv[4])
    elif cmd == "list":
        cmd_list()
    else:
        print(f"Unknown command or missing args: {cmd}")
        sys.exit(1)


if __name__ == "__main__":
    main()
