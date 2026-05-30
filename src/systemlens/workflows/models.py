from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ActionResult:
    status: str
    message: str
    details: dict

    def to_dict(self) -> dict:
        return {"status": self.status, "message": self.message, "details": self.details}
