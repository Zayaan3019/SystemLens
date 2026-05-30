from __future__ import annotations

from dataclasses import asdict
from pathlib import Path

from systemlens.utils import utc_now_iso, ensure_dir


def build_report(system: dict, latest: dict | None, alerts: list[dict], battery_drain: dict | None) -> dict:
    return {
        "generated_at": utc_now_iso(),
        "system": system,
        "latest": latest,
        "alerts": alerts,
        "battery_drain": battery_drain,
    }


def save_report(report: dict, report_dir: Path) -> Path:
    ensure_dir(report_dir)
    filename = f"report_{report['generated_at'].replace(':', '-')}.json"
    path = report_dir / filename
    path.write_text(__import__("json").dumps(report, indent=2), encoding="utf-8")
    return path
