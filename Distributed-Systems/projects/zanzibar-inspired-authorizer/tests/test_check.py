from zanzibar_authz.evaluator import CheckEngine
from zanzibar_authz.expressions import (
    Direct,
    Exclusion,
    Intersection,
    TupleToUserset,
    Union,
)
from zanzibar_authz.models import ConsistencyToken, TupleRecord
from zanzibar_authz.namespace import Namespace, RelationRule
from zanzibar_authz.store import TupleStore


def document_namespace() -> Namespace:
    return Namespace(
        name="document",
        relations={
            "owner": RelationRule(
                "owner",
                expression=Direct("owner"),
            ),
            "editor": RelationRule(
                "editor",
                expression=Direct("editor"),
            ),
            "direct_viewer": RelationRule(
                "direct_viewer",
                expression=Direct("direct_viewer"),
            ),
            "parent_viewer": RelationRule(
                "parent_viewer",
                expression=TupleToUserset(
                    tupleset_relation="parent",
                    computed_userset_relation="viewer",
                ),
            ),
            "viewer": RelationRule(
                "viewer",
                expression=Union(
                    (
                        Direct("direct_viewer"),
                        Direct("editor"),
                        Direct("owner"),
                        TupleToUserset(
                            tupleset_relation="parent",
                            computed_userset_relation="viewer",
                        ),
                    )
                ),
            ),
        },
    )


def group_namespace() -> Namespace:
    return Namespace(
        name="group",
        relations={
            "member": RelationRule("member"),
        },
    )


def build_engine(store: TupleStore) -> CheckEngine:
    namespaces = {
        "document": document_namespace(),
        "group": group_namespace(),
    }

    return CheckEngine(
        store=store,
        namespaces=namespaces,
    )


def test_direct_viewer_access() -> None:
    store = TupleStore()

    store.add(
        TupleRecord(
            object_type="document",
            object_id="design",
            relation="direct_viewer",
            subject_type="user",
            subject_id="alice",
        )
    )

    engine = build_engine(store)

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
            relation="direct_viewer",
            subject_type="user",
            subject_id="alice",
        )
    )

    engine = build_engine(store)

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

    # Engineering members are direct viewers of the document.
    store.add(
        TupleRecord(
            object_type="document",
            object_id="design",
            relation="direct_viewer",
            subject_type="group",
            subject_id="engineering",
            subject_relation="member",
        )
    )

    engine = build_engine(store)

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
            relation="direct_viewer",
            subject_type="group",
            subject_id="engineering",
            subject_relation="member",
        )
    )

    engine = build_engine(store)

    assert not engine.check(
        subject_type="user",
        subject_id="bob",
        object_type="document",
        object_id="design",
        relation="viewer",
    )


def test_namespace_defines_viewer_rule() -> None:
    namespace = document_namespace()

    viewer_rule = namespace.get_relation("viewer")

    assert isinstance(viewer_rule.expression, Union)

def test_intersection_requires_all_relations() -> None:
    store = TupleStore()

    store.add(
        TupleRecord(
            object_type="document",
            object_id="finance-report",
            relation="employee",
            subject_type="user",
            subject_id="alice",
        )
    )

    store.add(
        TupleRecord(
            object_type="document",
            object_id="finance-report",
            relation="finance_member",
            subject_type="user",
            subject_id="alice",
        )
    )

    namespace = Namespace(
        name="document",
        relations={
            "employee": RelationRule(
                "employee",
                expression=Direct("employee"),
            ),
            "finance_member": RelationRule(
                "finance_member",
                expression=Direct("finance_member"),
            ),
            "allowed": RelationRule(
                "allowed",
                expression=Intersection(
                    (
                        Direct("employee"),
                        Direct("finance_member"),
                    )
                ),
            ),
        },
    )

    engine = CheckEngine(
        store=store,
        namespaces={"document": namespace},
    )

    assert engine.check(
        subject_type="user",
        subject_id="alice",
        object_type="document",
        object_id="finance-report",
        relation="allowed",
    )


def test_intersection_denies_when_one_relation_is_missing() -> None:
    store = TupleStore()

    store.add(
        TupleRecord(
            object_type="document",
            object_id="finance-report",
            relation="employee",
            subject_type="user",
            subject_id="bob",
        )
    )

    namespace = Namespace(
        name="document",
        relations={
            "employee": RelationRule(
                "employee",
                expression=Direct("employee"),
            ),
            "finance_member": RelationRule(
                "finance_member",
                expression=Direct("finance_member"),
            ),
            "allowed": RelationRule(
                "allowed",
                expression=Intersection(
                    (
                        Direct("employee"),
                        Direct("finance_member"),
                    )
                ),
            ),
        },
    )

    engine = CheckEngine(
        store=store,
        namespaces={"document": namespace},
    )

    assert not engine.check(
        subject_type="user",
        subject_id="bob",
        object_type="document",
        object_id="finance-report",
        relation="allowed",
    )


def test_exclusion_removes_suspended_users() -> None:
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

    namespace = Namespace(
        name="document",
        relations={
            "viewer": RelationRule(
                "viewer",
                expression=Direct("viewer"),
            ),
            "suspended": RelationRule(
                "suspended",
                expression=Direct("suspended"),
            ),
            "allowed": RelationRule(
                "allowed",
                expression=Exclusion(
                    base=Direct("viewer"),
                    excluded=Direct("suspended"),
                ),
            ),
        },
    )

    engine = CheckEngine(
        store=store,
        namespaces={"document": namespace},
    )

    assert engine.check(
        subject_type="user",
        subject_id="alice",
        object_type="document",
        object_id="design",
        relation="allowed",
    )


def test_exclusion_denies_suspended_user() -> None:
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

    store.add(
        TupleRecord(
            object_type="document",
            object_id="design",
            relation="suspended",
            subject_type="user",
            subject_id="alice",
        )
    )

    namespace = Namespace(
        name="document",
        relations={
            "viewer": RelationRule(
                "viewer",
                expression=Direct("viewer"),
            ),
            "suspended": RelationRule(
                "suspended",
                expression=Direct("suspended"),
            ),
            "allowed": RelationRule(
                "allowed",
                expression=Exclusion(
                    base=Direct("viewer"),
                    excluded=Direct("suspended"),
                ),
            ),
        },
    )

    engine = CheckEngine(
        store=store,
        namespaces={"document": namespace},
    )

    assert not engine.check(
        subject_type="user",
        subject_id="alice",
        object_type="document",
        object_id="design",
        relation="allowed",
    )

def test_folder_viewer_access_is_inherited_by_document() -> None:
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

    # Engineering members can view the folder.
    store.add(
        TupleRecord(
            object_type="folder",
            object_id="engineering-docs",
            relation="viewer",
            subject_type="group",
            subject_id="engineering",
            subject_relation="member",
        )
    )

    # The document belongs to the folder.
    store.add(
        TupleRecord(
            object_type="document",
            object_id="design",
            relation="parent",
            subject_type="folder",
            subject_id="engineering-docs",
        )
    )

    engine = CheckEngine(
        store=store,
        namespaces={
            "document": document_namespace(),
            "group": group_namespace(),
            "folder": Namespace(
                name="folder",
                relations={
                    "viewer": RelationRule(
                        "viewer",
                        expression=Direct("viewer"),
                    ),
                },
            ),
        },
    )

    assert engine.check(
        subject_type="user",
        subject_id="alice",
        object_type="document",
        object_id="design",
        relation="viewer",
    )

def test_tuple_store_filters_by_snapshot_version() -> None:
    store = TupleStore()

    store.add(
        TupleRecord(
            object_type="document",
            object_id="design",
            relation="viewer",
            subject_type="user",
            subject_id="bob",
            valid_from=100,
            valid_to=105,
        )
    )

    assert len(
        store.find(
            object_type="document",
            object_id="design",
            relation="viewer",
            snapshot_version=100,
        )
    ) == 1

    assert len(
        store.find(
            object_type="document",
            object_id="design",
            relation="viewer",
            snapshot_version=104,
        )
    ) == 1

    assert len(
        store.find(
            object_type="document",
            object_id="design",
            relation="viewer",
            snapshot_version=105,
        )
    ) == 0

def test_check_uses_requested_snapshot_version() -> None:
    store = TupleStore()

    # Bob is a viewer starting at version 100.
    store.add(
        TupleRecord(
            object_type="document",
            object_id="design",
            relation="viewer",
            subject_type="user",
            subject_id="bob",
            valid_from=100,
            valid_to=105,
        )
    )

    namespace = Namespace(
        name="document",
        relations={
            "viewer": RelationRule(
                "viewer",
                expression=Direct("viewer"),
            ),
        },
    )

    engine = CheckEngine(
        store=store,
        namespaces={"document": namespace},
    )

    # At version 100, Bob should still have access.
    assert engine.check(
        subject_type="user",
        subject_id="bob",
        object_type="document",
        object_id="design",
        relation="viewer",
        consistency_token=ConsistencyToken(snapshot_version=100),
    )

    # At version 104, Bob still has access.
    assert engine.check(
        subject_type="user",
        subject_id="bob",
        object_type="document",
        object_id="design",
        relation="viewer",
        consistency_token=ConsistencyToken(snapshot_version=104),
    )

    # At version 105, Bob has been removed.
    assert not engine.check(
        subject_type="user",
        subject_id="bob",
        object_type="document",
        object_id="design",
        relation="viewer",
        consistency_token=ConsistencyToken(snapshot_version=105),
    )

def test_consistency_token_contains_snapshot_version() -> None:
    token = ConsistencyToken(snapshot_version=105)

    assert token.snapshot_version == 105