from dataclasses import dataclass


@dataclass(frozen=True)
class SimplePolicy:
    version: int
    allowed_users: set[str]


def authorize_with_policy(
    policy: SimplePolicy,
    user: str,
) -> bool:
    return user in policy.allowed_users


def is_policy_stale(
    cached_policy: SimplePolicy,
    current_version: int,
) -> bool:
    return cached_policy.version < current_version

def authorize_with_stale_policy_protection(
    policy: SimplePolicy,
    user: str,
    current_version: int,
) -> bool:
    if is_policy_stale(policy, current_version):
        return False

    return authorize_with_policy(policy, user)