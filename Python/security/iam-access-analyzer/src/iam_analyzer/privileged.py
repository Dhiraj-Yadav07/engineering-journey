from iam_analyzer.models import Action


PRIVILEGED_ACTIONS = {
    "iam.roles.create",
    "iam.roles.update",
    "iam.roles.delete",
}


def is_privileged_action(action: Action) -> bool:
    return action.name in PRIVILEGED_ACTIONS