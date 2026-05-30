from __future__ import annotations

import os
import psutil


def read_cpu() -> dict:
    psutil.cpu_percent(interval=None)
    per_cpu = psutil.cpu_percent(interval=None, percpu=True)
    percent = psutil.cpu_percent(interval=None)
    freq = psutil.cpu_freq()
    load_avg = None
    if hasattr(os, "getloadavg"):
        try:
            load_avg = list(os.getloadavg())
        except OSError:
            load_avg = None

    return {
        "percent": float(percent),
        "per_cpu": [float(value) for value in per_cpu],
        "freq_mhz": float(freq.current) if freq else None,
        "load_avg": load_avg,
        "cores": psutil.cpu_count(logical=True) or 0,
    }
