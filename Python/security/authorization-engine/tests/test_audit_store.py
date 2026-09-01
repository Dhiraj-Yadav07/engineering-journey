from datetime import datetime, timezone

from authorization_engine.audit_models import AuditEvent
from authorization_engine.audit_store import AuditStore


def test_record_event():
    store = AuditStore()

    event = AuditEvent(
        policy_id="document-read",
        version=1,
        action="policy_created",
        actor="admin",
        timestamp=datetime.now(timezone.utc),
    )

    store.record(event)

    assert store.list_events() == [event]


def test_multiple_events_are_preserved():
    store = AuditStore()

    timestamp = datetime.now(timezone.utc)

    event_v1 = AuditEvent(
        policy_id="document-read",
        version=1,
        action="policy_created",
        actor="admin",
        timestamp=timestamp,
    )

    event_v2 = AuditEvent(
        policy_id="document-read",
        version=2,
        action="policy_updated",
        actor="security-admin",
        timestamp=timestamp,
    )

    store.record(event_v1)
    store.record(event_v2)

    assert store.list_events() == [event_v1, event_v2]


def test_list_policy_events_filters_by_policy():
    store = AuditStore()

    timestamp = datetime.now(timezone.utc)

    document_event = AuditEvent(
        policy_id="document-read",
        version=1,
        action="policy_created",
        actor="admin",
        timestamp=timestamp,
    )

    network_event = AuditEvent(
        policy_id="network-access",
        version=1,
        action="policy_created",
        actor="admin",
        timestamp=timestamp,
    )

    store.record(document_event)
    store.record(network_event)

    assert store.list_policy_events("document-read") == [document_event]


def test_unknown_policy_has_no_events():
    store = AuditStore()

    timestamp = datetime.now(timezone.utc)

    store.record(
        AuditEvent(
            policy_id="document-read",
            version=1,
            action="policy_created",
            actor="admin",
            timestamp=timestamp,
        )
    )

    assert store.list_policy_events("unknown-policy") == []


def test_audit_event_is_immutable():
    timestamp = datetime.now(timezone.utc)

    event = AuditEvent(
        policy_id="document-read",
        version=1,
        action="policy_created",
        actor="admin",
        timestamp=timestamp,
    )

    try:
        event.version = 2
        assert False, "AuditEvent should be immutable"
    except AttributeError:
        pass