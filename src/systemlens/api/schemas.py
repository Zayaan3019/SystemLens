from __future__ import annotations

from pydantic import BaseModel


class SummaryResponse(BaseModel):
    latest: dict | None
    alerts: list[dict]
    system: dict | None
