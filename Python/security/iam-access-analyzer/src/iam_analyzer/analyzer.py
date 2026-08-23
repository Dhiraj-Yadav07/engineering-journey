from iam_analyzer.models import (
    AccessDecision,
    AccessRequest,
    Effect,
    Policy,
)


class AccessAnalyzer:
    def __init__(self, policies: list[Policy]):
        self.policies = policies

    def analyze(self, request: AccessRequest) -> AccessDecision:
        matching_policies = []

        for policy in self.policies:
            if (
                policy.principal == request.principal
                and policy.resource == request.resource
                and policy.action == request.action
            ):
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