from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class AuditEvent:
    timestamp: datetime
    principal: str
    resource: str
    action: str
    effect: str
    reason: str