from .abac_models import ABACDecision, ABACRequest


class ABACEngine:
    """
    Simple Attribute-Based Access Control engine.

    v0.1 policy:

    A user may READ a resource when:
    1. The user's department matches the resource's department.
    2. The request comes from the corporate network.
    """

    def authorize(self, request: ABACRequest) -> ABACDecision:
        if request.action != "read":
            return ABACDecision(
                allowed=False,
                reason="action is not supported",
            )

        user_department = request.user.attributes.get("department")
        resource_department = request.resource.attributes.get("department")
        network = request.context.attributes.get("network")

        if user_department != resource_department:
            return ABACDecision(
                allowed=False,
                reason="user department does not match resource department",
            )

        if network != "corporate":
            return ABACDecision(
                allowed=False,
                reason="request is not from the corporate network",
            )

        return ABACDecision(
            allowed=True,
            reason="department matches and request is from corporate network",
        )