from __future__ import annotations

import os
import platform
import subprocess
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

import psutil

from systemlens.workflows.models import ActionResult


def kill_process(pid: int) -> ActionResult:
    try:
        proc = psutil.Process(pid)
        proc.terminate()
        proc.wait(timeout=3)
        return ActionResult(status="ok", message=f"Process {pid} terminated", details={"pid": pid})
    except Exception as exc:
        return ActionResult(status="error", message=str(exc), details={"pid": pid})


def clear_temp(max_age_hours: int = 24) -> ActionResult:
    temp_dir = Path(tempfile.gettempdir())
    cutoff = datetime.utcnow() - timedelta(hours=max_age_hours)
    freed = 0
    removed = 0

    for item in temp_dir.glob("**/*"):
        try:
            if item.is_dir():
                continue
            mtime = datetime.utcfromtimestamp(item.stat().st_mtime)
            if mtime > cutoff:
                continue
            size = item.stat().st_size
            item.unlink(missing_ok=True)
            freed += size
            removed += 1
        except Exception:
            continue

    return ActionResult(
        status="ok",
        message=f"Cleared {removed} temp files",
        details={"freed_bytes": freed, "path": str(temp_dir)},
    )


def stop_service(name: str) -> ActionResult:
    system = platform.system().lower()
    try:
        if "windows" in system:
            subprocess.run(["sc", "stop", name], check=True, capture_output=True)
        elif "linux" in system:
            subprocess.run(["systemctl", "stop", name], check=True, capture_output=True)
        elif "darwin" in system:
            subprocess.run(["launchctl", "stop", name], check=True, capture_output=True)
        else:
            return ActionResult(status="error", message="Unsupported OS", details={"os": system})
        return ActionResult(status="ok", message=f"Service {name} stopped", details={"service": name})
    except Exception as exc:
        return ActionResult(status="error", message=str(exc), details={"service": name})
