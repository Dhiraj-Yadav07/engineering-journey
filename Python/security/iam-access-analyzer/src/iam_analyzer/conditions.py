def condition_matches(
    condition_key: str,
    expected_value: str,
    context: dict[str, str],
) -> bool:
    actual_value = context.get(condition_key)

    if actual_value is None:
        return False

    return actual_value == expected_value