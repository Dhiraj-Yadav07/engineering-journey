from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class AuditEvent:
    policy_id: str
    version: int
    action: str
    actor: str
    timestamp: datetime