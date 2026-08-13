from __future__ import annotations
from typing import Literal
from pydantic import BaseModel

class ProposedAction(BaseModel):
    type: Literal["navigate", "click", "fill", "wait", "extract", "done"]
    strategy: str | None = None
    target: str | None = None
    value: str | None = None
    output_name: str | None = None
    reason: str = ""

class AgentObservation(BaseModel):
    url: str
    title: str
    visible_text: str
