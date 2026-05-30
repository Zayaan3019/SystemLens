from __future__ import annotations

from dataclasses import dataclass


@dataclass
class MetricSample:
    timestamp: str
    cpu: dict
    memory: dict
    disk: dict
    network: dict
    processes: list[dict]
    battery: dict | None
    gpu: dict | None
    thermal: dict | None

    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp,
            "cpu": self.cpu,
            "memory": self.memory,
            "disk": self.disk,
            "network": self.network,
            "processes": self.processes,
            "battery": self.battery,
            "gpu": self.gpu,
            "thermal": self.thermal,
        }


@dataclass
class Alert:
    timestamp: str
    severity: str
    category: str
    message: str
    recommendation: str
    details: dict

    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp,
            "severity": self.severity,
            "category": self.category,
            "message": self.message,
            "recommendation": self.recommendation,
            "details": self.details,
        }


@dataclass
class SystemInfo:
    hostname: str
    os: str
    cpu: str
    cores: int
    boot_time: float
    collected_at: str
