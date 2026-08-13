from .schema import ( CapabilityArtifact, InputSpec, Action, Locator, Checkpoint, SafetyPolicy, )


def demo_member_balance_artifact(url: str) -> CapabilityArtifact:
    """
    Compile the discovered member-balance capability into a reusable,
    parameterized artifact.

    Discovery determines that the savings balance is the second cell
    in the savings row. Replay uses this deterministic locator without
    invoking an LLM.
    """

    return CapabilityArtifact(
        capability_id="member.savings_balance.v1",
        name="Look up member savings balance",
        application="synthetic-member-servicing",
        surface="browser",
        entry_point=url,
        inputs={
            "member_id": InputSpec(type="string"),
        },
        steps=[
            Action(
                id="navigate",
                type="navigate",
                value=url,
            ),
            Action(
                id="fill_member_id",
                type="fill",
                target=Locator(
                    strategy="label",
                    value="Member ID",
                ),
                value="{{member_id}}",
            ),
            Action(
                id="search",
                type="click",
                target=Locator(
                    strategy="role",
                    value="Search",
                ),
            ),
            Action(
                id="member_checkpoint",
                type="checkpoint",
                checkpoint=Checkpoint(
                    type="text_present",
                    expected="Member Details",
                ),
            ),
            # Action(
            #     id="not_found_checkpoint",
            #     type="checkpoint",
            #     checkpoint=Checkpoint(
            #         type="text_present",
            #         expected="Member not found",
            #     ),
            # ),
            Action(
                id="extract_savings",
                type="extract",
                target=Locator(
                    strategy="css",
                    value="table tr:nth-child(2) td:nth-child(2)",
                ),
                output_name="savings_balance",
            ),
        ],
        outcomes={
            "MEMBER_NOT_FOUND": {
                "type": "business_outcome",
                "description": "The requested member does not exist.",
            },
            "APPLICATION_ERROR": {
                "type": "hard_failure",
                "description": "The application returned an unexpected error.",
            },
        },
        safety=SafetyPolicy(
            allowed_domains=["127.0.0.1", "localhost"],
            allowed_actions=[
                "navigate",
                "click",
                "fill",
                "wait",
                "extract",
                "checkpoint",
            ],
            requires_confirmation=[],
        ),
    )