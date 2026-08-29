import pytest

from authorization_engine.engine import AuthorizationEngine
from authorization_engine.models import Decision, Permission, Role


def test_allows_action_granted_by_role():
    engine = AuthorizationEngine()

    developer = Role(
        name="developer",
        permissions={
            Permission("reports", "read"),
            Permission("reports", "write"),
        },
    )

    engine.add_role(developer)
    engine.assign_role("alice", "developer")

    decision = engine.authorize("alice", "reports", "read")

    assert decision.decision is Decision.ALLOW
    assert decision.reason == "role 'developer' grants 'reports:read'"


def test_denies_action_not_granted_by_role():
    engine = AuthorizationEngine()

    developer = Role(
        name="developer",
        permissions={
            Permission("reports", "read"),
            Permission("reports", "write"),
        },
    )

    engine.add_role(developer)
    engine.assign_role("alice", "developer")

    decision = engine.authorize("alice", "reports", "delete")

    assert decision.decision is Decision.DENY
    assert decision.reason == "no assigned role grants 'reports:delete'"


def test_denies_unknown_subject():
    engine = AuthorizationEngine()

    developer = Role(
        name="developer",
        permissions={
            Permission("reports", "read"),
        },
    )

    engine.add_role(developer)

    decision = engine.authorize(
        "unknown-user",
        "reports",
        "read",
    )

    assert decision.decision is Decision.DENY


def test_subject_can_have_multiple_roles():
    engine = AuthorizationEngine()

    developer = Role(
        name="developer",
        permissions={
            Permission("reports", "read"),
            Permission("reports", "write"),
        },
    )

    auditor = Role(
        name="auditor",
        permissions={
            Permission("audit", "read"),
        },
    )

    engine.add_role(developer)
    engine.add_role(auditor)

    engine.assign_role("alice", "developer")
    engine.assign_role("alice", "auditor")

    reports_decision = engine.authorize(
        "alice",
        "reports",
        "write",
    )

    audit_decision = engine.authorize(
        "alice",
        "audit",
        "read",
    )

    assert reports_decision.decision is Decision.ALLOW
    assert audit_decision.decision is Decision.ALLOW


def test_assigning_unknown_role_fails():
    engine = AuthorizationEngine()

    with pytest.raises(ValueError):
        engine.assign_role("alice", "nonexistent-role")

def test_permissions_are_isolated_between_roles():
    engine = AuthorizationEngine()

    developer = Role(
        name="developer",
        permissions={
            Permission("reports", "read"),
            Permission("reports", "write"),
        },
    )

    auditor = Role(
        name="auditor",
        permissions={
            Permission("audit", "read"),
        },
    )

    engine.add_role(developer)
    engine.add_role(auditor)

    engine.assign_role("alice", "developer")
    engine.assign_role("alice", "auditor")

    assert (
        engine.authorize("alice", "reports", "read").decision
        is Decision.ALLOW
    )

    assert (
        engine.authorize("alice", "audit", "read").decision
        is Decision.ALLOW
    )

    assert (
        engine.authorize("alice", "audit", "write").decision
        is Decision.DENY
    )

    assert (
        engine.authorize("alice", "reports", "delete").decision
        is Decision.DENY
    )

def test_permission_requires_resource():
    with pytest.raises(ValueError):
        Permission("", "read")


def test_permission_requires_action():
    with pytest.raises(ValueError):
        Permission("reports", "")


def test_role_requires_name():
    with pytest.raises(ValueError):
        Role("", {Permission("reports", "read")})