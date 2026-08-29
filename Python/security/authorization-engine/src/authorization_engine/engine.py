from .models import (
    AuthorizationDecision,
    Decision,
    Permission,
    Role,
)


class AuthorizationEngine:
    def __init__(self) -> None:
        self._roles: dict[str, Role] = {}
        self._subject_roles: dict[str, set[str]] = {}

    def add_role(self, role: Role) -> None:
        self._roles[role.name] = role

    def assign_role(self, subject: str, role_name: str) -> None:
        if role_name not in self._roles:
            raise ValueError(f"Role '{role_name}' does not exist")

        self._subject_roles.setdefault(subject, set()).add(role_name)

    def authorize(
        self,
        subject: str,
        resource: str,
        action: str,
    ) -> AuthorizationDecision:
        permission = Permission(resource, action)

        role_names = self._subject_roles.get(subject, set())

        for role_name in role_names:
            role = self._roles[role_name]

            if permission in role.permissions:
                return AuthorizationDecision(
                    decision=Decision.ALLOW,
                    reason=(
                        f"role '{role_name}' grants "
                        f"'{resource}:{action}'"
                    ),
                )

        return AuthorizationDecision(
            decision=Decision.DENY,
            reason=(
                f"no assigned role grants "
                f"'{resource}:{action}'"
            ),
        )