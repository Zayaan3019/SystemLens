from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

import aiosqlite

from systemlens.storage.models import Alert, MetricSample
from systemlens.utils import ensure_dir


class Storage:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self._conn: aiosqlite.Connection | None = None

    async def connect(self) -> None:
        ensure_dir(self.db_path.parent)
        self._conn = await aiosqlite.connect(self.db_path.as_posix())
        await self._conn.execute("PRAGMA journal_mode=WAL;")
        await self._conn.execute("PRAGMA synchronous=NORMAL;")
        await self._create_tables()

    async def close(self) -> None:
        if self._conn:
            await self._conn.close()
            self._conn = None

    async def _create_tables(self) -> None:
        if not self._conn:
            return
        await self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS metrics (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              ts TEXT NOT NULL,
              cpu_percent REAL,
              cpu_freq REAL,
              mem_percent REAL,
              mem_used INTEGER,
              mem_total INTEGER,
              disk_percent REAL,
              disk_used INTEGER,
              disk_total INTEGER,
              net_sent INTEGER,
              net_recv INTEGER,
              net_sent_rate REAL,
              net_recv_rate REAL,
              processes_json TEXT,
                            battery_json TEXT,
                            battery_percent REAL,
                            battery_plugged INTEGER,
                            gpu_json TEXT,
                            thermal_json TEXT
            )
            """
        )
        await self._conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_metrics_ts ON metrics(ts);"
        )
        await self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS alerts (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              ts TEXT NOT NULL,
              severity TEXT,
              category TEXT,
              message TEXT,
              recommendation TEXT,
              details_json TEXT
            )
            """
        )
        await self._conn.execute("CREATE INDEX IF NOT EXISTS idx_alerts_ts ON alerts(ts);")
        await self._conn.commit()

        await self._ensure_column("metrics", "battery_percent", "REAL")
        await self._ensure_column("metrics", "battery_plugged", "INTEGER")
        await self._ensure_column("metrics", "gpu_json", "TEXT")
        await self._ensure_column("metrics", "thermal_json", "TEXT")

    async def _ensure_column(self, table: str, column: str, column_type: str) -> None:
        if not self._conn:
            return
        cursor = await self._conn.execute(f"PRAGMA table_info({table});")
        cols = [row[1] for row in await cursor.fetchall()]
        if column not in cols:
            await self._conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {column_type};")
            await self._conn.commit()

    async def insert_metrics(self, sample: MetricSample) -> None:
        if not self._conn:
            return
        battery_percent = sample.battery.get("percent") if sample.battery else None
        battery_plugged = int(sample.battery.get("power_plugged")) if sample.battery else None
        await self._conn.execute(
            """
            INSERT INTO metrics (
              ts, cpu_percent, cpu_freq, mem_percent, mem_used, mem_total,
              disk_percent, disk_used, disk_total, net_sent, net_recv,
              net_sent_rate, net_recv_rate, processes_json, battery_json,
              battery_percent, battery_plugged, gpu_json, thermal_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                sample.timestamp,
                sample.cpu.get("percent"),
                sample.cpu.get("freq_mhz"),
                sample.memory.get("percent"),
                sample.memory.get("used"),
                sample.memory.get("total"),
                sample.disk.get("percent"),
                sample.disk.get("used"),
                sample.disk.get("total"),
                sample.network.get("bytes_sent"),
                sample.network.get("bytes_recv"),
                sample.network.get("sent_rate"),
                sample.network.get("recv_rate"),
                json.dumps(sample.processes),
                json.dumps(sample.battery) if sample.battery else None,
                battery_percent,
                battery_plugged,
                json.dumps(sample.gpu) if sample.gpu else None,
                json.dumps(sample.thermal) if sample.thermal else None,
            ),
        )
        await self._conn.commit()

    async def insert_alert(self, alert: Alert) -> None:
        if not self._conn:
            return
        await self._conn.execute(
            """
            INSERT INTO alerts (ts, severity, category, message, recommendation, details_json)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                alert.timestamp,
                alert.severity,
                alert.category,
                alert.message,
                alert.recommendation,
                json.dumps(alert.details),
            ),
        )
        await self._conn.commit()

    async def latest_metrics(self) -> dict | None:
        if not self._conn:
            return None
        cursor = await self._conn.execute(
            """
            SELECT ts, cpu_percent, mem_percent, disk_percent, net_sent_rate, net_recv_rate,
                   processes_json, battery_json, gpu_json, thermal_json, battery_percent, battery_plugged
            FROM metrics
            ORDER BY ts DESC
            LIMIT 1
            """
        )
        row = await cursor.fetchone()
        if not row:
            return None
        return {
            "timestamp": row[0],
            "cpu_percent": row[1],
            "mem_percent": row[2],
            "disk_percent": row[3],
            "net_sent_rate": row[4],
            "net_recv_rate": row[5],
            "processes": json.loads(row[6]) if row[6] else [],
            "battery": json.loads(row[7]) if row[7] else None,
            "gpu": json.loads(row[8]) if row[8] else None,
            "thermal": json.loads(row[9]) if row[9] else None,
            "battery_percent": row[10],
            "battery_plugged": bool(row[11]) if row[11] is not None else None,
        }

    async def recent_metrics(self, limit: int = 120) -> list[dict]:
        if not self._conn:
            return []
        cursor = await self._conn.execute(
            """
            SELECT ts, cpu_percent, mem_percent, disk_percent, net_sent_rate, net_recv_rate,
                   battery_percent
            FROM metrics
            ORDER BY ts DESC
            LIMIT ?
            """,
            (limit,),
        )
        rows = await cursor.fetchall()
        return [
            {
                "timestamp": row[0],
                "cpu_percent": row[1],
                "mem_percent": row[2],
                "disk_percent": row[3],
                "net_sent_rate": row[4],
                "net_recv_rate": row[5],
                "battery_percent": row[6],
            }
            for row in reversed(rows)
        ]

    async def recent_alerts(self, limit: int = 20) -> list[dict]:
        if not self._conn:
            return []
        cursor = await self._conn.execute(
            """
            SELECT ts, severity, category, message, recommendation, details_json
            FROM alerts
            ORDER BY ts DESC
            LIMIT ?
            """,
            (limit,),
        )
        rows = await cursor.fetchall()
        return [
            {
                "timestamp": row[0],
                "severity": row[1],
                "category": row[2],
                "message": row[3],
                "recommendation": row[4],
                "details": json.loads(row[5]) if row[5] else {},
            }
            for row in rows
        ]

    async def purge_old(self, retention_hours: int) -> None:
        if not self._conn:
            return
        await self._conn.execute(
            "DELETE FROM metrics WHERE ts < datetime('now', ?)",
            (f"-{retention_hours} hours",),
        )
        await self._conn.execute(
            "DELETE FROM alerts WHERE ts < datetime('now', ?)",
            (f"-{retention_hours} hours",),
        )
        await self._conn.commit()
