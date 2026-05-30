from __future__ import annotations

import statistics
from collections import deque

from systemlens.detection.baseline import HourlyBaseline
from systemlens.detection.rules import build_recommendation
from systemlens.storage.models import Alert, MetricSample
from systemlens.utils import utc_now_iso


class AnomalyDetector:
    def __init__(self, window: int = 60) -> None:
        self.window = window
        self.cpu = deque(maxlen=window)
        self.mem = deque(maxlen=window)
        self.disk = deque(maxlen=window)
        self.net_recv = deque(maxlen=window)
        self.net_sent = deque(maxlen=window)
        self._cpu_spike_count = 0
        self._cpu_baseline = HourlyBaseline(window=48)
        self._mem_baseline = HourlyBaseline(window=48)
        self._disk_baseline = HourlyBaseline(window=48)
        self._proc_baseline: dict[str, dict[str, float]] = {}

    def update(self, sample: MetricSample) -> list[Alert]:
        alerts: list[Alert] = []
        cpu = sample.cpu.get("percent") or 0.0
        mem = sample.memory.get("percent") or 0.0
        disk = sample.disk.get("percent") or 0.0
        net_recv = sample.network.get("recv_rate") or 0.0
        net_sent = sample.network.get("sent_rate") or 0.0

        self.cpu.append(cpu)
        self.mem.append(mem)
        self.disk.append(disk)
        self.net_recv.append(net_recv)
        self.net_sent.append(net_sent)

        baseline_cpu = self._cpu_baseline.update(cpu, sample.timestamp)
        baseline_mem = self._mem_baseline.update(mem, sample.timestamp)
        baseline_disk = self._disk_baseline.update(disk, sample.timestamp)

        if baseline_cpu and self._zscore(cpu, baseline_cpu) > 3.2:
            alerts.append(self._make_alert("cpu", "CPU spike vs baseline", sample))
        if baseline_mem and self._zscore(mem, baseline_mem) > 3.2:
            alerts.append(self._make_alert("memory", "Memory spike vs baseline", sample))
        if baseline_disk and self._zscore(disk, baseline_disk) > 3.2:
            alerts.append(self._make_alert("disk", "Disk usage spike vs baseline", sample))

        if cpu >= 90:
            self._cpu_spike_count += 1
        else:
            self._cpu_spike_count = max(self._cpu_spike_count - 1, 0)

        if self._cpu_spike_count >= 3:
            alerts.append(self._make_alert("cpu", "High CPU usage", sample))

        if mem >= 85:
            alerts.append(self._make_alert("memory", "High memory usage", sample))

        if disk >= 90:
            alerts.append(self._make_alert("disk", "Low disk space", sample))

        if self._robust_z(net_recv, self.net_recv) > 3.5:
            alerts.append(self._make_alert("network", "Network receive spike", sample))

        if self._robust_z(net_sent, self.net_sent) > 3.5:
            alerts.append(self._make_alert("network", "Network send spike", sample))

        alerts.extend(self._process_baseline_alerts(sample))

        return alerts

    def _robust_z(self, value: float, series: deque) -> float:
        if len(series) < 8:
            return 0.0
        median = statistics.median(series)
        mad = statistics.median([abs(x - median) for x in series]) or 1e-6
        return 0.6745 * (value - median) / mad

    def _make_alert(self, category: str, message: str, sample: MetricSample) -> Alert:
        recommendation = build_recommendation(category, sample)
        severity = "critical" if category in {"cpu", "memory", "disk"} else "warning"
        return Alert(
            timestamp=utc_now_iso(),
            severity=severity,
            category=category,
            message=message,
            recommendation=recommendation,
            details={"top_processes": sample.processes},
        )

    def _zscore(self, value: float, baseline: tuple[float, float]) -> float:
        median, mad = baseline
        return 0.6745 * (value - median) / (mad or 1e-6)

    def _process_baseline_alerts(self, sample: MetricSample) -> list[Alert]:
        alerts: list[Alert] = []
        for proc in sample.processes:
            name = proc.get("name") or "unknown"
            cpu = float(proc.get("cpu") or 0.0)
            mem = float(proc.get("memory") or 0.0)

            baseline = self._proc_baseline.setdefault(name, {"cpu": cpu, "mem": mem})
            baseline["cpu"] = baseline["cpu"] * 0.9 + cpu * 0.1
            baseline["mem"] = baseline["mem"] * 0.9 + mem * 0.1

            if cpu > max(50.0, baseline["cpu"] * 3):
                alerts.append(
                    Alert(
                        timestamp=utc_now_iso(),
                        severity="warning",
                        category="process",
                        message=f"{name} CPU spike",
                        recommendation=f"Consider closing or restarting {name}.",
                        details={"process": proc},
                    )
                )
            if mem > max(500_000_000.0, baseline["mem"] * 3):
                alerts.append(
                    Alert(
                        timestamp=utc_now_iso(),
                        severity="warning",
                        category="process",
                        message=f"{name} memory spike",
                        recommendation=f"Consider closing or restarting {name}.",
                        details={"process": proc},
                    )
                )
        return alerts
