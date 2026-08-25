from datetime import datetime

from iam_analyzer.audit import AuditEvent


def test_audit_event_contains_authorization_details():
    timestamp = datetime(2026, 8, 25, 12, 0, 0)

    event = AuditEvent(
        timestamp=timestamp,
        principal="user:alice@example.com",
        resource="bucket:prod-data",
        action="storage.objects.get",
        effect="allow",
        reason="Matching allow policy found",
    )

    assert event.timestamp == timestamp
    assert event.principal == "user:alice@example.com"
    assert event.resource == "bucket:prod-data"
    assert event.action == "storage.objects.get"
    assert event.effect == "allow"
    assert event.reason == "Matching allow policy found"