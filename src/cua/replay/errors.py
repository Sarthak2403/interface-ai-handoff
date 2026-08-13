class ReplayError(Exception):
    code = "REPLAY_ERROR"

class ArtifactError(ReplayError):
    code = "ARTIFACT_INVALID"

class CheckpointFailed(ReplayError):
    code = "CHECKPOINT_FAILED"

class BusinessOutcome(ReplayError):
    def __init__(self, outcome: str, message: str):
        super().__init__(message)
        self.outcome = outcome
        self.code = "BUSINESS_OUTCOME"

class InterventionRequired(ReplayError):
    code = "INTERVENTION_REQUIRED"
