from iam_analyzer.models import Action
from iam_analyzer.risk import calculate_risk_score


def test_read_action_has_low_risk():
    action = Action(
        name="storage.objects.get",
    )

    score = calculate_risk_score(action)

    assert score < 30


def test_write_action_has_higher_risk_than_read():
    read_action = Action(
        name="storage.objects.get",
    )

    write_action = Action(
        name="storage.objects.create",
    )

    read_score = calculate_risk_score(read_action)
    write_score = calculate_risk_score(write_action)

    assert write_score > read_score


def test_delete_action_has_high_risk():
    action = Action(
        name="storage.objects.delete",
    )

    score = calculate_risk_score(action)

    assert score >= 60


def test_iam_action_has_high_risk():
    action = Action(
        name="iam.roles.update",
    )

    score = calculate_risk_score(action)

    assert score >= 60