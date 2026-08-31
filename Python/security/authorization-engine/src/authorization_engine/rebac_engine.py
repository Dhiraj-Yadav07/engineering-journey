from authorization_engine.rebac_store import RelationshipStore


class ReBACEngine:
    RELATION_PERMISSIONS = {
        "owner": {"read", "write", "delete"},
        "editor": {"read", "write"},
        "viewer": {"read"},
    }

    def __init__(self, store: RelationshipStore):
        self.store = store

    def authorize(
        self,
        subject: str,
        action: str,
        resource: str,
    ) -> bool:
        # Direct relationship check
        for relation, allowed_actions in self.RELATION_PERMISSIONS.items():
            if self.store.exists(subject, relation, resource):
                return action in allowed_actions

        # Group relationship check
        for relation, allowed_actions in self.RELATION_PERMISSIONS.items():
            if action not in allowed_actions:
                continue

            if self.store.exists(
                "group:engineering",
                relation,
                resource,
            ) and self.store.is_member(
                subject,
                "group:engineering",
            ):
                return True

        return False