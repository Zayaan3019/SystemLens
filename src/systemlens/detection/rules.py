from __future__ import annotations

from systemlens.storage.models import MetricSample


def build_recommendation(category: str, sample: MetricSample) -> str:
    processes = sample.processes or []
    top = processes[0]["name"] if processes else "unknown"

    if category == "cpu":
        return f"Close or restart {top} and reduce background tasks."
    if category == "memory":
        return f"Free memory by closing {top} or restarting heavy apps."
    if category == "disk":
        return "Delete unused files or move large folders to external storage."
    if category == "network":
        return "Pause large downloads or check for background sync tasks."
    return "Monitor system and retry if the issue persists."
