from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class User:
    id: str
    attributes: dict[str, Any]


@dataclass(frozen=True)
class Resource:
    id: str
    attributes: dict[str, Any]


@dataclass(frozen=True)
class AccessContext:
    attributes: dict[str, Any]


@dataclass(frozen=True)
class ABACRequest:
    user: User
    resource: Resource
    action: str
    context: AccessContext


@dataclass(frozen=True)
class ABACDecision:
    allowed: bool
    reason: str