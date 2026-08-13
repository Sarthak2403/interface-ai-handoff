from __future__ import annotations
import json
import os
import requests
from .model import ProposedAction, AgentObservation


class OllamaPlanner:
    def __init__(self):
        self.base_url = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
        self.model = os.getenv("OLLAMA_MODEL", "llama3.2:3b")

    def _format_elements(self, elements: list[dict]) -> str:
        if not elements:
            return ""
        lines = ["\nCLICKABLE/FILLABLE ELEMENTS ON PAGE (target ONLY these, do not invent selectors):"]
        for e in elements:
            if e.get("id"):
                sel = f'#{e["id"]}'
            elif e.get("name"):
                sel = f'{e["tag"]}[name=\'{e["name"]}\']'
            else:
                sel = None
            value_note = f' current_value="{e["value"]}"' if e.get("value") else ""
            if sel:
                lines.append(f'- tag={e["tag"]} text="{e["text"]}"{value_note} strategy=css target="{sel}"')
            else:
                lines.append(f'- tag={e["tag"]} text="{e["text"]}"{value_note} strategy=text target="{e["text"]}"')
        return "\n".join(lines) + "\n"

    def _allowed_targets(self, elements: list[dict]) -> set[str]:
        allowed = set()
        for e in elements:
            if e.get("id"):
                allowed.add(f'#{e["id"]}')
            if e.get("name"):
                allowed.add(f'{e["tag"]}[name=\'{e["name"]}\']')
            if e.get("text"):
                allowed.add(e["text"])
        return allowed

    def _format_history(self, history: list[str]) -> str:
        if not history:
            return ""
        recent = history[-6:]
        lines = ["\nACTIONS ALREADY TAKEN THIS RUN (do not repeat these):"]
        lines += [f"- {h}" for h in recent]
        return "\n".join(lines) + "\n"

    def _build_prompt(self, goal: str, observation: AgentObservation,
                       elements: list[dict] | None, history: list[str] | None = None,
                       retry_hint: str | None = None) -> str:
        hint_block = f"\nPREVIOUS ATTEMPT REJECTED: {retry_hint}\nFix this and try again, using ONLY a target listed below.\n" if retry_hint else ""
        elements_block = self._format_elements(elements or [])
        history_block = self._format_history(history or [])
        return f"""
                You are a computer-use discovery agent.

                Goal:
                {goal}

                Current browser state:
                URL: {observation.url}
                Title: {observation.title}
                {elements_block}{history_block}{hint_block}
                Return ONLY JSON with:
                type: navigate|click|fill|wait|extract|done
                strategy: role|label|text|css|xpath|null
                target: string|null
                value: string|null
                output_name: string|null
                reason: string

                RULES:
                1. Copy strategy and target EXACTLY as shown for one of the listed elements above.
                NEVER write your own xpath. NEVER invent a selector not shown to you.
                2. Fill required inputs before clicking a submit/search button.
                3. If ACTIONS ALREADY TAKEN shows you already filled a field, do NOT fill it
                again — move on to the next step (e.g. click submit/search).
                4. If none of the listed elements let you proceed, return type="done" with
                reason explaining you cannot proceed safely.
                5. If the goal is already complete based on visible state, return type="done".

                Never invent credentials or perform unsafe actions.
                """

    def _coerce_strategy(self, action: ProposedAction) -> ProposedAction:
        if not action.target:
            return action
        t = action.target.strip()
        looks_like_xpath = t.startswith(("/", "//", "(("))
        looks_like_css = (
            t.startswith(("#", ".", "["))
            or t.split("[")[0] in {"input", "button", "div", "span", "a", "select", "textarea", "form"}
        )
        if looks_like_css and not looks_like_xpath and action.strategy != "css":
            action.strategy = "css"
        return action

    def next_action(self, goal: str, observation: AgentObservation,
                     elements: list[dict] | None = None, history: list[str] | None = None) -> ProposedAction:
        allowed = self._allowed_targets(elements or [])
        last_error: str | None = None
        max_attempts = 4

        for attempt in range(1, max_attempts + 1):
            prompt = self._build_prompt(goal, observation, elements, history=history, retry_hint=last_error)
            try:
                r = requests.post(
                    f"{self.base_url}/api/generate",
                    json={"model": self.model, "prompt": prompt, "stream": False, "format": "json"},
                    timeout=60,
                )
                r.raise_for_status()
                raw = r.json()["response"]
                action = ProposedAction.model_validate(json.loads(raw))
                action = self._coerce_strategy(action)

                if action.type in ("click", "fill", "extract") and allowed:
                    if action.target not in allowed:
                        last_error = (
                            f"target '{action.target}' is not one of the listed elements. "
                            f"You must copy an exact target string from the list."
                        )
                        continue

                return action
            except (json.JSONDecodeError, ValueError, KeyError, requests.RequestException) as e:
                last_error = f"attempt {attempt} failed to produce valid action JSON: {e}"
                continue

        raise RuntimeError(
            f"OllamaPlanner failed to produce a valid, in-scope action after {max_attempts} attempts. "
            f"Last error: {last_error}"
        )