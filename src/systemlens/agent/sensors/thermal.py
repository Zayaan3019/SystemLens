from __future__ import annotations

import psutil


def read_thermal() -> dict:
    temps = []
    fans = []

    if hasattr(psutil, "sensors_temperatures"):
        for name, entries in (psutil.sensors_temperatures() or {}).items():
            for entry in entries:
                temps.append(
                    {
                        "label": entry.label or name,
                        "current": float(entry.current),
                        "high": float(entry.high) if entry.high else None,
                    }
                )

    if hasattr(psutil, "sensors_fans"):
        for name, entries in (psutil.sensors_fans() or {}).items():
            for entry in entries:
                fans.append(
                    {
                        "label": entry.label or name,
                        "rpm": float(entry.current),
                    }
                )

    return {
        "temperatures": temps,
        "fans": fans,
    }
