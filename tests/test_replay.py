import pytest
from cua.replay.errors import CheckpointFailed

def test_failure_class_is_distinct():
    exc = CheckpointFailed("Application Error")
    assert exc.code == "CHECKPOINT_FAILED"
