from authorization_engine.rebac_models import (
    GroupMembership,
    RelationshipTuple,
)


class RelationshipStore:
    def __init__(self):
        self._tuples: set[RelationshipTuple] = set()
        self._memberships: set[GroupMembership] = set()

    def add(self, relationship: RelationshipTuple) -> None:
        self._tuples.add(relationship)

    def remove(self, relationship: RelationshipTuple) -> None:
        self._tuples.discard(relationship)

    def exists(
        self,
        subject: str,
        relation: str,
        resource: str,
    ) -> bool:
        relationship = RelationshipTuple(
            subject=subject,
            relation=relation,
            resource=resource,
        )

        return relationship in self._tuples

    def add_membership(self, membership: GroupMembership) -> None:
        self._memberships.add(membership)

    def is_member(
        self,
        subject: str,
        group: str,
    ) -> bool:
        membership = GroupMembership(
            subject=subject,
            group=group,
        )

        return membership in self._memberships