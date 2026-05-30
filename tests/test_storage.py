import asyncio
from pathlib import Path

from systemlens.storage.db import Storage
from systemlens.storage.models import MetricSample


def test_storage_insert_and_fetch(tmp_path: Path):
    async def run_test():
        store = Storage(tmp_path / "systemlens.db")
        await store.connect()
        sample = MetricSample(
            timestamp="2026-01-01T00:00:00Z",
            cpu={"percent": 10, "freq_mhz": 2000},
            memory={"percent": 20, "used": 1, "total": 2},
            disk={"percent": 30, "used": 1, "total": 2},
            network={"bytes_sent": 1, "bytes_recv": 2, "sent_rate": 0, "recv_rate": 0},
            processes=[],
            battery=None,
            gpu=None,
            thermal=None,
        )
        await store.insert_metrics(sample)
        latest = await store.latest_metrics()
        await store.close()
        assert latest is not None
        assert latest["cpu_percent"] == 10

    asyncio.run(run_test())
