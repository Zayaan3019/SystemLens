from __future__ import annotations

import psutil


def read_processes(limit: int = 6) -> list[dict]:
    processes = []
    for proc in psutil.process_iter(["pid", "name", "cpu_percent", "memory_info"]):
        try:
            info = proc.info
            memory = info.get("memory_info")
            processes.append(
                {
                    "pid": int(info.get("pid") or 0),
                    "name": info.get("name") or "unknown",
                    "cpu": float(info.get("cpu_percent") or 0.0),
                    "memory": int(memory.rss) if memory else 0,
                }
            )
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    processes.sort(key=lambda item: (item["cpu"], item["memory"]), reverse=True)
    return processes[:limit]
