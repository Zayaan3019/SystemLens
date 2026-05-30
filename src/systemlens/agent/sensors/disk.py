from __future__ import annotations

from pathlib import Path

import psutil


def _primary_path() -> str:
    try:
        return Path.cwd().anchor or "/"
    except Exception:
        return "/"


def read_disk() -> dict:
    path = _primary_path()
    usage = psutil.disk_usage(path)
    return {
        "path": path,
        "total": int(usage.total),
        "used": int(usage.used),
        "free": int(usage.free),
        "percent": float(usage.percent),
    }
