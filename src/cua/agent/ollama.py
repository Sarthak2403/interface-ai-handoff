from __future__ import annotations
import json
import os
import requests
from .model import ProposedAction, AgentObservation

class OllamaPlanner:
    def __init__(self):
        self.base_url = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
        self.model = os.getenv("OLLAMA_MODEL", "llama3.2:3b")

    def next_action(self, goal: str, observation: AgentObservation) -> ProposedAction:
        prompt = f"""
You are a computer-use discovery agent.

Goal:
{goal}

Current browser state:
URL: {observation.url}
Title: {observation.title}
Visible text:
{observation.visible_text[:10000]}

Return ONLY JSON with:
type: navigate|click|fill|wait|extract|done
strategy: role|label|text|css|xpath|null
target: string|null
value: string|null
output_name: string|null
reason: string

Use only information visible in the page. Never invent credentials or perform
unsafe actions. If the goal is complete, return type=done.
"""
        r = requests.post(
            f"{self.base_url}/api/generate",
            json={"model": self.model, "prompt": prompt, "stream": False, "format": "json"},
            timeout=60,
        )
        r.raise_for_status()
        raw = r.json()["response"]
        return ProposedAction.model_validate(json.loads(raw))
