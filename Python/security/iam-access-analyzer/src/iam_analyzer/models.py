from dataclasses import dataclass
from enum import Enum


class PrincipalType(Enum):
    USER = "user"
    SERVICE_ACCOUNT = "service_account"
    GROUP = "group"
    ROLE = "role"


@dataclass(frozen=True)
class Principal:
    id: str
    type: PrincipalType


@dataclass(frozen=True)
class Resource:
    id: str
    type: str


@dataclass(frozen=True)
class Action:
    name: str


class Effect(Enum):
    ALLOW = "allow"
    DENY = "deny"


@dataclass(frozen=True)
class Policy:
    principal: Principal
    resource: Resource
    action: Action
    effect: Effect


@dataclass(frozen=True)
class AccessRequest:
    principal: Principal
    resource: Resource
    action: Action


@dataclass(frozen=True)
class AccessDecision:
    effect: Effect
    reason: str