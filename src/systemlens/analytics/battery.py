from __future__ import annotations

from datetime import datetime


def estimate_battery_drain(samples: list[dict]) -> dict | None:
    points = [s for s in samples if s.get("battery")]
    if len(points) < 2:
        return None

    first = points[0]
    last = points[-1]
    try:
        t1 = datetime.fromisoformat(first["timestamp"].replace("Z", "+00:00"))
        t2 = datetime.fromisoformat(last["timestamp"].replace("Z", "+00:00"))
    except Exception:
        return None

    elapsed_hours = max((t2 - t1).total_seconds() / 3600, 1e-6)
    p1 = first["battery"].get("percent")
    p2 = last["battery"].get("percent")
    if p1 is None or p2 is None:
        return None
    drain_per_hour = (p1 - p2) / elapsed_hours
    return {
        "drain_per_hour": round(drain_per_hour, 2),
        "elapsed_hours": round(elapsed_hours, 2),
        "start_percent": p1,
        "end_percent": p2,
    }
