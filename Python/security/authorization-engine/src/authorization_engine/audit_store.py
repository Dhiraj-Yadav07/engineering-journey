from authorization_engine.audit_models import AuditEvent


class AuditStore:
    def __init__(self):
        self._events: list[AuditEvent] = []

    def record(self, event: AuditEvent) -> None:
        self._events.append(event)

    def list_events(self) -> list[AuditEvent]:
        return list(self._events)

    def list_policy_events(self, policy_id: str) -> list[AuditEvent]:
        return [
            event
            for event in self._events
            if event.policy_id == policy_id
        ]