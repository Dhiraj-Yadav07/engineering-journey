from datetime import datetime


def policy_is_expired(
    expires_at: datetime | None,
    current_time: datetime,
) -> bool:
    if expires_at is None:
        return False

    return current_time >= expires_at