from __future__ import annotations

import psutil


def read_battery() -> dict | None:
    try:
        battery = psutil.sensors_battery()
    except Exception:
        return None
    if battery is None:
        return None
    return {
        "percent": float(battery.percent),
        "secs_left": int(battery.secsleft),
        "power_plugged": bool(battery.power_plugged),
    }
