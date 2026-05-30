from systemlens.detection.anomaly import AnomalyDetector
from systemlens.storage.models import MetricSample


def _sample(cpu=10, mem=20, disk=30, recv=5, sent=3):
    return MetricSample(
        timestamp="2026-01-01T00:00:00Z",
        cpu={"percent": cpu},
        memory={"percent": mem},
        disk={"percent": disk},
        network={"recv_rate": recv, "sent_rate": sent},
        processes=[],
        battery=None,
        gpu=None,
        thermal=None,
    )


def test_detects_cpu_spike():
    detector = AnomalyDetector(window=10)
    for _ in range(3):
        alerts = detector.update(_sample(cpu=95))
    assert any(alert.category == "cpu" for alert in alerts)
