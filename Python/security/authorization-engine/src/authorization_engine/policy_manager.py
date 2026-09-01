from datetime import datetime, timezone

from authorization_engine.audit_models import AuditEvent
from authorization_engine.audit_store import AuditStore
from authorization_engine.policy_models import PolicyVersion
from authorization_engine.policy_store import VersionedPolicyStore


class PolicyManager:
    def __init__(
        self,
        policy_store: VersionedPolicyStore,
        audit_store: AuditStore,
    ):
        self.policy_store = policy_store
        self.audit_store = audit_store

    def create_version(
        self,
        policy_id: str,
        rule: str,
        actor: str,
    ) -> PolicyVersion:
        versions = self.policy_store.list_versions(policy_id)

        next_version = len(versions) + 1
        timestamp = datetime.now(timezone.utc)

        policy = PolicyVersion(
            policy_id=policy_id,
            version=next_version,
            rule=rule,
            created_at=timestamp,
            created_by=actor,
        )

        self.policy_store.add_version(policy)

        self.audit_store.record(
            AuditEvent(
                policy_id=policy_id,
                version=next_version,
                action="policy_created",
                actor=actor,
                timestamp=timestamp,
            )
        )

        return policy

    def rollback(
        self,
        policy_id: str,
        target_version: int,
        actor: str,
    ) -> PolicyVersion:
        target = self.policy_store.get_version(
            policy_id,
            target_version,
        )

        if target is None:
            raise ValueError(
                f"Policy version {target_version} does not exist"
            )

        return self.create_version(
            policy_id,
            target.rule,
            actor,
        )