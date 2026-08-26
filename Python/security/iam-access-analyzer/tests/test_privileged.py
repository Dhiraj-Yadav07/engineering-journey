from iam_analyzer.models import Action
from iam_analyzer.privileged import is_privileged_action


def test_iam_role_update_is_privileged():
    action = Action(
        name="iam.roles.update",
    )

    assert is_privileged_action(action) is True


def test_iam_role_create_is_privileged():
    action = Action(
        name="iam.roles.create",
    )

    assert is_privileged_action(action) is True


def test_iam_role_delete_is_privileged():
    action = Action(
        name="iam.roles.delete",
    )

    assert is_privileged_action(action) is True


def test_storage_read_is_not_privileged():
    action = Action(
        name="storage.objects.get",
    )

    assert is_privileged_action(action) is False