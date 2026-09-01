from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class PolicyVersion:
    policy_id: str
    version: int
    rule: str
    created_at: datetime
    created_by: str