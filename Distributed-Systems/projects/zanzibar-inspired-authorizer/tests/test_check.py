from zanzibar_authz.evaluator import CheckEngine
from zanzibar_authz.models import TupleRecord
from zanzibar_authz.store import TupleStore


def test_direct_viewer_access() -> None:
    store = TupleStore()

    store.add(
        TupleRecord(
            object_type="document",
            object_id="design",
            relation="viewer",
            subject_type="user",
            subject_id="alice",
        )
    )

    engine = CheckEngine(store)

    assert engine.check(
        subject_type="user",
        subject_id="alice",
        object_type="document",
        object_id="design",
        relation="viewer",
    )


def test_unknown_user_is_denied() -> None:
    store = TupleStore()

    store.add(
        TupleRecord(
            object_type="document",
            object_id="design",
            relation="viewer",
            subject_type="user",
            subject_id="alice",
        )
    )

    engine = CheckEngine(store)

    assert not engine.check(
        subject_type="user",
        subject_id="bob",
        object_type="document",
        object_id="design",
        relation="viewer",
    )


def test_group_membership_grants_access() -> None:
    store = TupleStore()

    # Alice is a member of Engineering.
    store.add(
        TupleRecord(
            object_type="group",
            object_id="engineering",
            relation="member",
            subject_type="user",
            subject_id="alice",
        )
    )

    # Engineering members can view the document.
    store.add(
        TupleRecord(
            object_type="document",
            object_id="design",
            relation="viewer",
            subject_type="group",
            subject_id="engineering",
            subject_relation="member",
        )
    )

    engine = CheckEngine(store)

    assert engine.check(
        subject_type="user",
        subject_id="alice",
        object_type="document",
        object_id="design",
        relation="viewer",
    )


def test_non_member_is_denied() -> None:
    store = TupleStore()

    store.add(
        TupleRecord(
            object_type="group",
            object_id="engineering",
            relation="member",
            subject_type="user",
            subject_id="alice",
        )
    )

    store.add(
        TupleRecord(
            object_type="document",
            object_id="design",
            relation="viewer",
            subject_type="group",
            subject_id="engineering",
            subject_relation="member",
        )
    )

    engine = CheckEngine(store)

    assert not engine.check(
        subject_type="user",
        subject_id="bob",
        object_type="document",
        object_id="design",
        relation="viewer",
    )