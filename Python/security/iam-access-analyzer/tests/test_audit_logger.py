from datetime import datetime

from iam_analyzer.audit import AuditEvent
from iam_analyzer.audit_logger import AuditLogger


def test_audit_logger_records_events():
    logger = AuditLogger()

    event = AuditEvent(
        timestamp=datetime(2026, 8, 25, 12, 0, 0),
        principal="user:alice@example.com",
        resource="bucket:prod-data",
        action="storage.objects.get",
        effect="allow",
        reason="Matching allow policy found",
    )

    logger.record(event)

    assert logger.events == [event]