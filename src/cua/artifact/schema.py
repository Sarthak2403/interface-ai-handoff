from __future__ import annotations
from typing import Any, Literal
from pydantic import BaseModel, Field

LocatorStrategy = Literal["role", "label", "text", "css", "xpath"]

class Locator(BaseModel):
    strategy: LocatorStrategy
    value: str
    name: str | None = None
    fallback: "Locator | None" = None

class InputSpec(BaseModel):
    type: Literal["string", "number", "boolean"]
    required: bool = True

class Checkpoint(BaseModel):
    type: Literal["text_present", "text_absent", "url_contains", "element_visible"]
    expected: str
    target: Locator | None = None

class Action(BaseModel):
    id: str
    type: Literal["navigate", "click", "fill", "wait", "extract", "checkpoint"]
    target: Locator | None = None
    value: str | None = None
    output_name: str | None = None
    checkpoint: Checkpoint | None = None
    timeout_ms: int = Field(default=5000, ge=100, le=30000)

class SafetyPolicy(BaseModel):
    allowed_domains: list[str]
    allowed_actions: list[str]
    requires_confirmation: list[str] = []

class CapabilityArtifact(BaseModel):
    schema_version: str = "1.0"
    capability_id: str
    name: str
    application: str
    surface: str
    entry_point: str
    inputs: dict[str, InputSpec]
    steps: list[Action]
    outcomes: dict[str, dict[str, Any]]
    safety: SafetyPolicy
