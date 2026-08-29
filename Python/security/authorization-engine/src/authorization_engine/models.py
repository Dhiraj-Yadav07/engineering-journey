from dataclasses import dataclass
from enum import Enum


@dataclass(frozen=True)
class Permission:
    resource: str
    action: str

    def __post_init__(self) -> None:
        if not self.resource:
            raise ValueError("Permission resource cannot be empty")

        if not self.action:
            raise ValueError("Permission action cannot be empty")


@dataclass
class Role:
    name: str
    permissions: set[Permission]

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("Role name cannot be empty")


class Decision(Enum):
    ALLOW = "allow"
    DENY = "deny"


@dataclass(frozen=True)
class AuthorizationDecision:
    decision: Decision
    reason: str