from __future__ import annotations

import asyncio
import json
from pathlib import Path

import csv
import io

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, Response
from fastapi.staticfiles import StaticFiles
from starlette.responses import StreamingResponse

from systemlens.analytics.battery import estimate_battery_drain
from systemlens.agent.collector import Collector
from systemlens.agent.sampler import Agent
from systemlens.agent.sensors.network import NetworkTracker
from systemlens.config import load_config
from systemlens.detection.anomaly import AnomalyDetector
from systemlens.reports.generator import build_report, save_report
from systemlens.security import require_role
from systemlens.storage.db import Storage
from systemlens.utils import ensure_dir
from systemlens.workflows.actions import clear_temp, kill_process, stop_service

WEB_DIR = Path(__file__).resolve().parents[1] / "web"

app = FastAPI(title="SystemLens")
if WEB_DIR.exists():
    app.mount("/static", StaticFiles(directory=WEB_DIR), name="static")

config = load_config()


class EventBroker:
    def __init__(self) -> None:
        self._queues: list[asyncio.Queue] = []

    def subscribe(self) -> asyncio.Queue:
        queue: asyncio.Queue = asyncio.Queue(maxsize=10)
        self._queues.append(queue)
        return queue

    def unsubscribe(self, queue: asyncio.Queue) -> None:
        if queue in self._queues:
            self._queues.remove(queue)

    async def publish(self, payload: dict) -> None:
        for queue in list(self._queues):
            if queue.full():
                _ = queue.get_nowait()
            await queue.put(payload)


@app.on_event("startup")
async def _startup() -> None:
    ensure_dir(config.data_dir)
    app.state.storage = Storage(config.db_path)
    await app.state.storage.connect()

    collector = Collector(network_tracker=NetworkTracker())
    app.state.system_info = collector.collect_system()

    detector = AnomalyDetector(window=60)
    broker = EventBroker()

    async def on_event(payload: dict) -> None:
        await broker.publish(payload)

    app.state.broker = broker
    app.state.agent = Agent(
        collector=collector,
        storage=app.state.storage,
        detector=detector,
        interval=config.sample_interval,
        retention_hours=config.retention_hours,
        on_event=on_event,
    )
    await app.state.agent.start()


@app.on_event("shutdown")
async def _shutdown() -> None:
    if getattr(app.state, "agent", None):
        await app.state.agent.stop()
    if getattr(app.state, "storage", None):
        await app.state.storage.close()


@app.get("/")
async def root() -> HTMLResponse:
    index_path = WEB_DIR / "index.html"
    if index_path.exists():
        return HTMLResponse(index_path.read_text(encoding="utf-8"))
    return HTMLResponse("UI assets missing", status_code=500)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}


@app.get("/api/system", dependencies=[require_role("viewer")])
async def system_info() -> dict:
    return app.state.system_info


@app.get("/api/summary", dependencies=[require_role("viewer")])
async def summary() -> dict:
    latest = await app.state.storage.latest_metrics()
    alerts = await app.state.storage.recent_alerts(limit=10)
    recent = await app.state.storage.recent_metrics(limit=30)
    for row in recent:
        if latest and row.get("battery_percent") is not None:
            row["battery"] = {"percent": row.get("battery_percent")}
    battery_drain = estimate_battery_drain(recent)
    return {
        "latest": latest,
        "alerts": alerts,
        "system": app.state.system_info,
        "battery_drain": battery_drain,
    }


@app.get("/api/metrics", dependencies=[require_role("viewer")])
async def metrics(limit: int = 120) -> list[dict]:
    return await app.state.storage.recent_metrics(limit=limit)


@app.get("/api/alerts", dependencies=[require_role("viewer")])
async def alerts(limit: int = 20) -> list[dict]:
    return await app.state.storage.recent_alerts(limit=limit)


@app.get("/api/stream", dependencies=[require_role("viewer")])
async def stream() -> StreamingResponse:
    queue = app.state.broker.subscribe()

    async def event_generator():
        try:
            while True:
                payload = await queue.get()
                yield f"data: {json.dumps(payload)}\n\n"
        finally:
            app.state.broker.unsubscribe(queue)

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@app.get("/api/timeline", dependencies=[require_role("viewer")])
async def timeline(limit: int = 50) -> list[dict]:
    return await app.state.storage.recent_alerts(limit=limit)


@app.get("/api/reports/latest", dependencies=[require_role("viewer")])
async def report() -> dict:
    latest = await app.state.storage.latest_metrics()
    alerts = await app.state.storage.recent_alerts(limit=20)
    recent = await app.state.storage.recent_metrics(limit=30)
    for row in recent:
        if row.get("battery_percent") is not None:
            row["battery"] = {"percent": row.get("battery_percent")}
    battery_drain = estimate_battery_drain(recent)
    report = build_report(app.state.system_info, latest, alerts, battery_drain)
    path = save_report(report, config.data_dir / "reports")
    report["report_path"] = str(path)
    return report


@app.get("/api/exports/report.json", dependencies=[require_role("viewer")])
async def export_report() -> Response:
    latest = await app.state.storage.latest_metrics()
    alerts = await app.state.storage.recent_alerts(limit=20)
    recent = await app.state.storage.recent_metrics(limit=30)
    for row in recent:
        if row.get("battery_percent") is not None:
            row["battery"] = {"percent": row.get("battery_percent")}
    battery_drain = estimate_battery_drain(recent)
    report = build_report(app.state.system_info, latest, alerts, battery_drain)
    output = json.dumps(report, indent=2)
    return Response(
        content=output,
        media_type="application/json",
        headers={"Content-Disposition": "attachment; filename=report.json"},
    )


def _csv_response(rows: list[dict], filename: str) -> Response:
    output = io.StringIO()
    if not rows:
        return Response(content="", media_type="text/csv")
    writer = csv.DictWriter(output, fieldnames=rows[0].keys())
    writer.writeheader()
    writer.writerows(rows)
    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@app.get("/api/exports/metrics.csv", dependencies=[require_role("viewer")])
async def export_metrics_csv(limit: int = 500) -> Response:
    rows = await app.state.storage.recent_metrics(limit=limit)
    return _csv_response(rows, "metrics.csv")


@app.get("/api/exports/metrics.json", dependencies=[require_role("viewer")])
async def export_metrics_json(limit: int = 500) -> list[dict]:
    return await app.state.storage.recent_metrics(limit=limit)


@app.get("/api/exports/alerts.csv", dependencies=[require_role("viewer")])
async def export_alerts_csv(limit: int = 200) -> Response:
    rows = await app.state.storage.recent_alerts(limit=limit)
    return _csv_response(rows, "alerts.csv")


@app.get("/api/exports/alerts.json", dependencies=[require_role("viewer")])
async def export_alerts_json(limit: int = 200) -> list[dict]:
    return await app.state.storage.recent_alerts(limit=limit)


@app.post("/api/actions/kill", dependencies=[require_role("admin")])
async def action_kill(payload: dict) -> dict:
    pid = int(payload.get("pid"))
    result = kill_process(pid)
    return result.to_dict()


@app.post("/api/actions/clear-temp", dependencies=[require_role("admin")])
async def action_clear_temp(payload: dict) -> dict:
    max_age = int(payload.get("max_age_hours", 24))
    result = clear_temp(max_age_hours=max_age)
    return result.to_dict()


@app.post("/api/actions/stop-service", dependencies=[require_role("admin")])
async def action_stop_service(payload: dict) -> dict:
    name = str(payload.get("service"))
    result = stop_service(name)
    return result.to_dict()
