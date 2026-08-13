from __future__ import annotations
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
import json
import uuid

@dataclass
class InterventionRequest:
    id: str
    status: str
    reason: str
    step_id: str
    url: str
    last_successful_checkpoint: str | None
    context: dict
    created_at: str

class InterventionManager:
    def __init__(self, directory: str = "evidence/interventions"):
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)

    def create(self, reason: str, step_id: str, url: str,
               checkpoint: str | None, context: dict) -> InterventionRequest:
        req = InterventionRequest(
            id=f"int_{uuid.uuid4().hex[:10]}",
            status="PENDING",
            reason=reason,
            step_id=step_id,
            url=url,
            last_successful_checkpoint=checkpoint,
            context=context,
            created_at=datetime.now(timezone.utc).isoformat(),
        )
        (self.directory / f"{req.id}.json").write_text(
            json.dumps(asdict(req), indent=2), encoding="utf-8"
        )
        return req

    def list(self):
        return sorted(self.directory.glob("int_*.json"))
