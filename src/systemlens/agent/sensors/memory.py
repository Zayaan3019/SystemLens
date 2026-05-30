from __future__ import annotations

import psutil


def read_memory() -> dict:
    mem = psutil.virtual_memory()
    swap = psutil.swap_memory()
    return {
        "total": int(mem.total),
        "available": int(mem.available),
        "used": int(mem.used),
        "percent": float(mem.percent),
        "swap_used": int(swap.used),
        "swap_percent": float(swap.percent),
    }
