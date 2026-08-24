from datetime import datetime

from iam_analyzer.conditions import condition_matches
from iam_analyzer.expiration import policy_is_expired
from iam_analyzer.matching import action_matches
from iam_analyzer.models import (
    AccessDecision,
    AccessRequest,
    Effect,
    Policy,
)


class AccessAnalyzer:
    def __init__(
        self,
        policies: list[Policy],
        current_time: datetime | None = None,
    ):
        self.policies = policies
        self.current_time = (
            current_time
            if current_time is not None
            else datetime.now()
        )

    def analyze(self, request: AccessRequest) -> AccessDecision:
        matching_policies = []

        for policy in self.policies:
            if (
                policy.principal == request.principal
                and policy.resource == request.resource
                and action_matches(
                    policy.action.name,
                    request.action.name,
                )
            ):
                if policy_is_expired(
                    policy.expires_at,
                    self.current_time,
                ):
                    continue

                if policy.condition_key is not None:
                    if not condition_matches(
                        policy.condition_key,
                        policy.condition_value,
                        request.context,
                    ):
                        continue

                matching_policies.append(policy)

        for policy in matching_policies:
            if policy.effect == Effect.DENY:
                return AccessDecision(
                    effect=Effect.DENY,
                    reason="Explicit deny policy matched",
                )

        if matching_policies:
            return AccessDecision(
                effect=Effect.ALLOW,
                reason="Matching allow policy found",
            )

        return AccessDecision(
            effect=Effect.DENY,
            reason="No matching policy found",
        )