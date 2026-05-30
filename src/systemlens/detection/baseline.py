from __future__ import annotations

from collections import deque
from datetime import datetime
from statistics import median


class HourlyBaseline:
    def __init__(self, window: int = 24) -> None:
        self.window = window
        self.series: dict[int, deque] = {hour: deque(maxlen=window) for hour in range(24)}

    def update(self, value: float, timestamp: str) -> tuple[float, float] | None:
        hour = self._hour(timestamp)
        bucket = self.series[hour]
        bucket.append(value)
        if len(bucket) < max(6, self.window // 3):
            return None
        med = median(bucket)
        mad = median([abs(x - med) for x in bucket]) or 1e-6
        return med, mad

    @staticmethod
    def _hour(timestamp: str) -> int:
        try:
            dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            return dt.hour
        except Exception:
            return 0
