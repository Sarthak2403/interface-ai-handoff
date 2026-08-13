import pytest
from cua.agent.model import ProposedAction
from cua.artifact.schema import SafetyPolicy
from cua.safety.policy import validate_action, SafetyViolation

def test_allowed_action():
    policy = SafetyPolicy(
        allowed_domains=["127.0.0.1"],
        allowed_actions=["click"]
    )
    validate_action(
        ProposedAction(type="click", strategy="role", target="Search"),
        policy,
        "http://127.0.0.1:8000"
    )

def test_disallowed_action():
    policy = SafetyPolicy(
        allowed_domains=["127.0.0.1"],
        allowed_actions=["click"]
    )
    with pytest.raises(SafetyViolation):
        validate_action(
            ProposedAction(type="navigate", value="http://127.0.0.1"),
            policy,
            "http://127.0.0.1:8000"
        )
