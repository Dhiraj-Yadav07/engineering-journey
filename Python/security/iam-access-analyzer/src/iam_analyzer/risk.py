from iam_analyzer.models import Action


def calculate_risk_score(action: Action) -> int:
    if action.name.endswith(".get"):
        return 10

    if action.name.endswith(".create"):
        return 40

    if action.name.endswith(".delete"):
        return 70

    if action.name.startswith("iam."):
        return 70

    return 20