import pytest

from authorization_engine.rebac_models import (
    GroupMembership,
    RelationshipTuple,
)
from authorization_engine.rebac_store import RelationshipStore
from authorization_engine.rebac_engine import ReBACEngine


@pytest.fixture
def engine():
    store = RelationshipStore()

    store.add(
        RelationshipTuple(
            "alice",
            "owner",
            "document:report-123",
        )
    )

    store.add(
        RelationshipTuple(
            "bob",
            "editor",
            "document:report-123",
        )
    )

    store.add(
        RelationshipTuple(
            "charlie",
            "viewer",
            "document:report-123",
        )
    )

    return ReBACEngine(store)


def test_owner_can_read(engine):
    assert engine.authorize(
        "alice",
        "read",
        "document:report-123",
    ) is True


def test_owner_can_write(engine):
    assert engine.authorize(
        "alice",
        "write",
        "document:report-123",
    ) is True


def test_owner_can_delete(engine):
    assert engine.authorize(
        "alice",
        "delete",
        "document:report-123",
    ) is True


def test_editor_can_read(engine):
    assert engine.authorize(
        "bob",
        "read",
        "document:report-123",
    ) is True


def test_editor_can_write(engine):
    assert engine.authorize(
        "bob",
        "write",
        "document:report-123",
    ) is True


def test_editor_cannot_delete(engine):
    assert engine.authorize(
        "bob",
        "delete",
        "document:report-123",
    ) is False


def test_viewer_can_read(engine):
    assert engine.authorize(
        "charlie",
        "read",
        "document:report-123",
    ) is True


def test_viewer_cannot_write(engine):
    assert engine.authorize(
        "charlie",
        "write",
        "document:report-123",
    ) is False


def test_viewer_cannot_delete(engine):
    assert engine.authorize(
        "charlie",
        "delete",
        "document:report-123",
    ) is False


def test_unknown_user_is_denied(engine):
    assert engine.authorize(
        "david",
        "read",
        "document:report-123",
    ) is False


def test_relationship_is_resource_specific(engine):
    assert engine.authorize(
        "alice",
        "read",
        "document:other-456",
    ) is False

def test_same_user_can_have_different_relationships_with_different_resources(engine):
    engine.store.add(
        RelationshipTuple(
            "alice",
            "viewer",
            "document:design-456",
        )
    )

    assert engine.authorize(
        "alice",
        "read",
        "document:design-456",
    ) is True

    assert engine.authorize(
        "alice",
        "write",
        "document:design-456",
    ) is False

    assert engine.authorize(
        "alice",
        "delete",
        "document:design-456",
    ) is False

def test_group_member_inherits_resource_access(engine):
    engine.store.add(
        RelationshipTuple(
            "group:engineering",
            "viewer",
            "document:report-123",
        )
    )

    engine.store.add_membership(
        GroupMembership(
            "david",
            "group:engineering",
        )
    )

    assert engine.authorize(
        "david",
        "read",
        "document:report-123",
    ) is True

    assert engine.authorize(
        "david",
        "write",
        "document:report-123",
    ) is False

    assert engine.authorize(
        "david",
        "delete",
        "document:report-123",
    ) is False