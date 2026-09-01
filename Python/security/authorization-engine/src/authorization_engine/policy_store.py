from authorization_engine.policy_models import PolicyVersion


class VersionedPolicyStore:
    def __init__(self):
        self._policies: dict[str, list[PolicyVersion]] = {}

    def add_version(self, policy: PolicyVersion) -> None:
        versions = self._policies.setdefault(policy.policy_id, [])

        if versions:
            latest_version = versions[-1].version

            if policy.version != latest_version + 1:
                raise ValueError(
                    "Policy versions must be sequential"
                )
        elif policy.version != 1:
            raise ValueError(
                "The first policy version must be 1"
            )

        versions.append(policy)

    def get_version(
        self,
        policy_id: str,
        version: int,
    ) -> PolicyVersion:
        versions = self._policies.get(policy_id, [])

        for policy in versions:
            if policy.version == version:
                return policy

        raise KeyError(
            f"Policy '{policy_id}' version {version} not found"
        )

    def get_latest(
        self,
        policy_id: str,
    ) -> PolicyVersion:
        versions = self._policies.get(policy_id, [])

        if not versions:
            raise KeyError(
                f"Policy '{policy_id}' not found"
            )

        return versions[-1]

    def list_versions(
        self,
        policy_id: str,
    ) -> list[PolicyVersion]:
        return list(
            self._policies.get(policy_id, [])
        )