def action_matches(policy_action: str, requested_action: str) -> bool:
    if policy_action == "*":
        return True

    if policy_action.endswith("*"):
        prefix = policy_action[:-1]
        return requested_action.startswith(prefix)

    return policy_action == requested_action