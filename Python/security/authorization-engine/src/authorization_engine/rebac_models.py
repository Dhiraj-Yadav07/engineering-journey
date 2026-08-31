from dataclasses import dataclass


@dataclass(frozen=True)
class RelationshipTuple:
    subject: str
    relation: str
    resource: str


@dataclass(frozen=True)
class GroupMembership:
    subject: str
    group: str