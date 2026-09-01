import pytest

from authorization_engine.audit_store import AuditStore
from authorization_engine.policy_manager import PolicyManager
from authorization_engine.policy_store import VersionedPolicyStore


@pytest.fixture
def manager():
    return PolicyManager(
        policy_store=VersionedPolicyStore(),
        audit_store=AuditStore(),
    )


def test_create_first_policy_version(manager):
    policy = manager.create_version(
        "document-read",
        "alice can read report-123",
        "admin",
    )

    assert policy.version == 1
    assert policy.policy_id == "document-read"
    assert policy.rule == "alice can read report-123"
    assert policy.created_by == "admin"


def test_create_second_policy_version(manager):
    manager.create_version(
        "document-read",
        "alice can read report-123",
        "admin",
    )

    policy = manager.create_version(
        "document-read",
        "alice and bob can read report-123",
        "security-admin",
    )

    assert policy.version == 2
    assert policy.created_by == "security-admin"


def test_latest_version_is_returned(manager):
    manager.create_version(
        "document-read",
        "alice can read report-123",
        "admin",
    )

    manager.create_version(
        "document-read",
        "alice and bob can read report-123",
        "security-admin",
    )

    latest = manager.policy_store.get_latest("document-read")

    assert latest is not None
    assert latest.version == 2
    assert latest.rule == "alice and bob can read report-123"


def test_policy_creation_generates_audit_event(manager):
    manager.create_version(
        "document-read",
        "alice can read report-123",
        "admin",
    )

    events = manager.audit_store.list_policy_events(
        "document-read"
    )

    assert len(events) == 1
    assert events[0].policy_id == "document-read"
    assert events[0].version == 1
    assert events[0].action == "policy_created"
    assert events[0].actor == "admin"


def test_each_policy_version_has_audit_event(manager):
    manager.create_version(
        "document-read",
        "alice can read report-123",
        "admin",
    )

    manager.create_version(
        "document-read",
        "alice and bob can read report-123",
        "security-admin",
    )

    events = manager.audit_store.list_policy_events(
        "document-read"
    )

    assert len(events) == 2

    assert events[0].version == 1
    assert events[0].actor == "admin"

    assert events[1].version == 2
    assert events[1].actor == "security-admin"


def test_different_policies_have_independent_versions(manager):
    policy_a = manager.create_version(
        "document-read",
        "alice can read report-123",
        "admin",
    )

    policy_b = manager.create_version(
        "document-write",
        "bob can write report-123",
        "admin",
    )

    assert policy_a.version == 1
    assert policy_b.version == 1


def test_audit_timestamp_matches_policy_creation(manager):
    policy = manager.create_version(
        "document-read",
        "alice can read report-123",
        "admin",
    )

    events = manager.audit_store.list_policy_events(
        "document-read"
    )

    assert len(events) == 1
    assert events[0].timestamp == policy.created_at

def test_rollback_creates_new_version_from_historical_version():
    manager = PolicyManager(
        VersionedPolicyStore(),
        AuditStore(),
    )

    manager.create_version(
        "document-read",
        "alice can read report-123",
        "admin",
    )

    manager.create_version(
        "document-read",
        "alice and bob can read report-123",
        "security-admin",
    )

    rollback = manager.rollback(
        "document-read",
        1,
        "security-admin",
    )

    assert rollback.version == 3
    assert rollback.rule == "alice can read report-123"
    assert rollback.created_by == "security-admin"