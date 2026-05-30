from __future__ import annotations

import platform

import psutil

from systemlens.utils import utc_now_iso


def read_system() -> dict:
    boot_time = psutil.boot_time()
    return {
        "hostname": platform.node(),
        "os": platform.platform(),
        "cpu": platform.processor(),
        "cores": psutil.cpu_count(logical=True) or 0,
        "boot_time": boot_time,
        "collected_at": utc_now_iso(),
    }
