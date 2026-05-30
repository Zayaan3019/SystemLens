from __future__ import annotations

from dataclasses import dataclass

from systemlens.agent.sensors.battery import read_battery
from systemlens.agent.sensors.cpu import read_cpu
from systemlens.agent.sensors.disk import read_disk
from systemlens.agent.sensors.gpu import read_gpu
from systemlens.agent.sensors.network import NetworkTracker, read_network
from systemlens.agent.sensors.processes import read_processes
from systemlens.agent.sensors.system import read_system
from systemlens.agent.sensors.memory import read_memory
from systemlens.agent.sensors.thermal import read_thermal
from systemlens.storage.models import MetricSample, SystemInfo
from systemlens.utils import utc_now_iso


@dataclass
class Collector:
    network_tracker: NetworkTracker

    def collect(self) -> MetricSample:
        cpu = read_cpu()
        memory = read_memory()
        disk = read_disk()
        network = read_network(self.network_tracker)
        processes = read_processes()
        battery = read_battery()
        gpu = read_gpu()
        thermal = read_thermal()

        return MetricSample(
            timestamp=utc_now_iso(),
            cpu=cpu,
            memory=memory,
            disk=disk,
            network=network,
            processes=processes,
            battery=battery,
            gpu=gpu,
            thermal=thermal,
        )

    def collect_system(self) -> SystemInfo:
        return read_system()
