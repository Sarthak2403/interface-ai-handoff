from __future__ import annotations
import re
from pathlib import Path
from playwright.async_api import TimeoutError as PlaywrightTimeoutError

from cua.artifact.schema import CapabilityArtifact
from cua.replay.errors import BusinessOutcome, CheckpointFailed, InterventionRequired
from cua.safety.policy import validate_action
from cua.escalation.manager import InterventionManager
from cua.surfaces.browser import BrowserSurface

SENSITIVE_NAMES = {"savings_balance", "balance", "account_number", "ssn"}

class ReplayEngine:
    def __init__(self, artifact: CapabilityArtifact, surface: BrowserSurface,
                 intervention: InterventionManager | None = None,
                 escalate: bool = False):
        self.artifact = artifact
        self.surface = surface
        self.intervention = intervention
        self.escalate = escalate
        self.last_checkpoint = None
        self.outputs = {}

    async def run(self, inputs: dict[str, str]) -> dict:
        for step in self.artifact.steps:
            try:
                if step.type == "navigate":
                    validate_action(
                        type("A", (), {"type": "navigate"})(),
                        self.artifact.safety,
                        self.artifact.entry_point
                    )
                    await self.surface.navigate(step.value)

                elif step.type == "fill":
                    value = step.value or ""
                    for k, v in inputs.items():
                        value = value.replace("{{" + k + "}}", str(v))
                    validate_action(
                        type("A", (), {"type": "fill", "target": step.target})(),
                        self.artifact.safety,
                        self.artifact.entry_point
                    )
                    await self.surface.fill(step.target.strategy, step.target.value, value)

                elif step.type == "click":
                    validate_action(
                        type("A", (), {"type": "click", "target": step.target})(),
                        self.artifact.safety,
                        self.artifact.entry_point
                    )
                    await self.surface.click(step.target.strategy, step.target.value)

                elif step.type == "checkpoint":
                    await self._checkpoint(step.checkpoint)
                    self.last_checkpoint = step.id

                elif step.type == "extract":
                    value = await self.surface.extract(step.target.strategy, step.target.value)
                    if step.output_name:
                        self.outputs[step.output_name] = value

                elif step.type == "wait":
                    continue

                # A legitimate not-found page is classified before the normal
                # success checkpoint is considered complete.
                obs = await self.surface.observe()
                lower = obs["visible_text"].lower()
                if "member not found" in lower:
                    raise BusinessOutcome(
                        "MEMBER_NOT_FOUND",
                        "The requested member does not exist."
                    )
                if "application error" in lower:
                    raise CheckpointFailed(
                        "Unexpected application error state."
                    )

            except BusinessOutcome:
                raise
            except (CheckpointFailed, PlaywrightTimeoutError) as exc:
                if self.escalate and self.intervention:
                    req = self.intervention.create(
                        reason=str(exc),
                        step_id=step.id,
                        url=(await self.surface.observe())["url"],
                        checkpoint=self.last_checkpoint,
                        context={"error": str(exc)}
                    )
                    raise InterventionRequired(
                        f"Human intervention required: {req.id}"
                    )
                raise

        return {
            "status": "SUCCESS",
            "outputs": self.outputs,
            "redacted_outputs": {
                k: "[REDACTED]" if k in SENSITIVE_NAMES else v
                for k, v in self.outputs.items()
            }
        }

    async def _checkpoint(self, checkpoint):
        obs = await self.surface.observe()
        text = obs["visible_text"]
        if checkpoint.type == "text_present" and checkpoint.expected not in text:
            raise CheckpointFailed(
                f"Expected text {checkpoint.expected!r} was not present."
            )
