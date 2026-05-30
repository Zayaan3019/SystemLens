from __future__ import annotations

from dataclasses import dataclass

import psutil


@dataclass
class NetworkTracker:
    last_sent: int = 0
    last_recv: int = 0


def read_network(tracker: NetworkTracker) -> dict:
    counters = psutil.net_io_counters()
    sent = int(counters.bytes_sent)
    recv = int(counters.bytes_recv)

    sent_rate = max(sent - tracker.last_sent, 0) if tracker.last_sent else 0
    recv_rate = max(recv - tracker.last_recv, 0) if tracker.last_recv else 0

    tracker.last_sent = sent
    tracker.last_recv = recv

    return {
        "bytes_sent": sent,
        "bytes_recv": recv,
        "sent_rate": float(sent_rate),
        "recv_rate": float(recv_rate),
        "packets_sent": int(counters.packets_sent),
        "packets_recv": int(counters.packets_recv),
    }
