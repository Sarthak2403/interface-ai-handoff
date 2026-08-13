from urllib.parse import urlparse
from cua.agent.model import ProposedAction
from cua.artifact.schema import SafetyPolicy

class SafetyViolation(Exception):
    pass

def validate_action(action: ProposedAction, policy: SafetyPolicy, current_url: str) -> None:
    if action.type == "done":
        return
    if action.type not in policy.allowed_actions:
        raise SafetyViolation(f"Action '{action.type}' is not allowed.")

    host = urlparse(current_url).hostname
    if host not in policy.allowed_domains:
        raise SafetyViolation(f"Domain '{host}' is not allowlisted.")

    if action.type in {"click", "fill", "extract"} and not action.target:
        raise SafetyViolation("Target is required for this action.")
