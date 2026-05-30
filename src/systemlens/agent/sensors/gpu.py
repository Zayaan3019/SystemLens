from __future__ import annotations

import subprocess


def _from_nvidia_smi() -> list[dict]:
    try:
        result = subprocess.run(
            [
                "nvidia-smi",
                "--query-gpu=utilization.gpu,temperature.gpu,fan.speed,name",
                "--format=csv,noheader,nounits",
            ],
            capture_output=True,
            text=True,
            check=True,
        )
    except Exception:
        return []

    gpus: list[dict] = []
    for line in result.stdout.strip().splitlines():
        parts = [p.strip() for p in line.split(",")]
        if len(parts) >= 4:
            gpus.append(
                {
                    "utilization": float(parts[0]),
                    "temperature": float(parts[1]),
                    "fan": float(parts[2]) if parts[2] else None,
                    "name": parts[3],
                }
            )
    return gpus


def _from_pynvml() -> list[dict]:
    try:
        import pynvml

        pynvml.nvmlInit()
        count = pynvml.nvmlDeviceGetCount()
        gpus = []
        for idx in range(count):
            handle = pynvml.nvmlDeviceGetHandleByIndex(idx)
            name = pynvml.nvmlDeviceGetName(handle).decode("utf-8")
            util = pynvml.nvmlDeviceGetUtilizationRates(handle).gpu
            temp = pynvml.nvmlDeviceGetTemperature(handle, pynvml.NVML_TEMPERATURE_GPU)
            try:
                fan = pynvml.nvmlDeviceGetFanSpeed(handle)
            except Exception:
                fan = None
            gpus.append(
                {
                    "utilization": float(util),
                    "temperature": float(temp),
                    "fan": float(fan) if fan is not None else None,
                    "name": name,
                }
            )
        return gpus
    except Exception:
        return []


def read_gpu() -> dict:
    gpus = _from_pynvml()
    if not gpus:
        gpus = _from_nvidia_smi()
    return {
        "available": bool(gpus),
        "gpus": gpus,
    }
