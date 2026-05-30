from __future__ import annotations

import asyncio
import logging

from systemlens.agent.collector import Collector
from systemlens.detection.anomaly import AnomalyDetector
from systemlens.storage.db import Storage
from systemlens.utils import utc_now_iso


class Agent:
    def __init__(
        self,
        collector: Collector,
        storage: Storage,
        detector: AnomalyDetector,
        interval: float,
        on_event=None,
        retention_hours: int = 72,
    ) -> None:
        self.collector = collector
        self.storage = storage
        self.detector = detector
        self.interval = interval
        self.on_event = on_event
        self.retention_hours = retention_hours
        self._task: asyncio.Task | None = None
        self._stop_event = asyncio.Event()
        self._logger = logging.getLogger("systemlens.agent")

    async def start(self) -> None:
        if self._task:
            return
        self._stop_event.clear()
        self._task = asyncio.create_task(self._run_loop())

    async def stop(self) -> None:
        if not self._task:
            return
        self._stop_event.set()
        await self._task
        self._task = None

    async def _run_loop(self) -> None:
        self._logger.info("Agent started")
        while not self._stop_event.is_set():
            sample = self.collector.collect()
            await self.storage.insert_metrics(sample)
            alerts = self.detector.update(sample)
            for alert in alerts:
                await self.storage.insert_alert(alert)

            if self.on_event:
                payload = {
                    "timestamp": utc_now_iso(),
                    "sample": sample.to_dict(),
                    "alerts": [alert.to_dict() for alert in alerts],
                }
                await self.on_event(payload)

            await self.storage.purge_old(self.retention_hours)
            await asyncio.sleep(self.interval)

        self._logger.info("Agent stopped")
