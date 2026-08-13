from .model import ProposedAction, AgentObservation


class OfflinePlanner:
    """
    No-key demo planner.

    Intentionally narrow: demonstrates the discovery-to-artifact seam
    without requiring a hosted model.
    """

    def __init__(self):
        self.seen_search = False
        self.seen_details = False
        self.extracted = False

    def next_action(
        self,
        goal: str,
        observation: AgentObservation
    ) -> ProposedAction:

        text = observation.visible_text.lower()

        # Initial member search page
        if (
            "member id" in text
            and "search" in text
            and not self.seen_search
        ):
            self.seen_search = True

            import re

            m = re.search(r"\b(\d{4,})\b", goal)
            member_id = m.group(1) if m else "12345"

            return ProposedAction(
                type="fill",
                strategy="label",
                target="Member ID",
                value=member_id,
                reason="Enter the member identifier from the goal.",
            )

        # Submit member search
        if (
            "member id" in text
            and "search" in text
            and self.seen_search
        ):
            return ProposedAction(
                type="click",
                strategy="role",
                target="Search",
                reason="Submit the member lookup.",
            )

        # Member was not found
        if "member not found" in text:
            return ProposedAction(
                type="done",
                reason="The requested member is not found.",
            )

        # Application failure
        if "application error" in text:
            return ProposedAction(
                type="done",
                reason="The application reported an error.",
            )

        # Member details page
        if "member details" in text and not self.extracted:
            self.seen_details = True
            self.extracted = True

            return ProposedAction(
                type="extract",
                strategy="css",
                target="table tr:nth-child(2) td:nth-child(2)",
                output_name="savings_balance",
                reason="Read the current savings balance from the member details.",
            )

        # Prevent repeated extraction
        if self.extracted:
            return ProposedAction(
                type="done",
                reason="The requested savings balance has been extracted.",
            )

        return ProposedAction(
            type="done",
            reason="No safe next action is available.",
        )