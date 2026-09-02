class PolicyUnavailableError(Exception):
    """Raised when the policy source cannot be reached."""


def authorize_fail_open(policy_check) -> bool:
    try:
        return policy_check()
    except PolicyUnavailableError:
        return True


def authorize_fail_closed(policy_check) -> bool:
    try:
        return policy_check()
    except PolicyUnavailableError:
        return False