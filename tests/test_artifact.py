from cua.artifact.compiler import demo_member_balance_artifact

def test_artifact_is_parameterized():
    a = demo_member_balance_artifact("http://127.0.0.1:8000")
    assert a.inputs["member_id"].required
    fill = next(x for x in a.steps if x.id == "fill_member_id")
    assert fill.value == "{{member_id}}"

def test_artifact_has_checkpoint_and_outcome():
    a = demo_member_balance_artifact("http://127.0.0.1:8000")
    assert any(x.type == "checkpoint" for x in a.steps)
    assert "MEMBER_NOT_FOUND" in a.outcomes
