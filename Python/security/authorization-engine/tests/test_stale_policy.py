from authorization_engine.stale_policy import (
    SimplePolicy,
    authorize_with_policy,
    authorize_with_stale_policy_protection,
    is_policy_stale,
)


def test_current_policy_denies_user_after_policy_change():
    policy_v2 = SimplePolicy(
        version=2,
        allowed_users={"alice"},
    )

    assert authorize_with_policy(
        policy_v2,
        "bob",
    ) is False


def test_stale_policy_still_allows_user():
    policy_v1 = SimplePolicy(
        version=1,
        allowed_users={"alice", "bob"},
    )

    assert authorize_with_policy(
        policy_v1,
        "bob",
    ) is True


def test_stale_policy_produces_different_decision_from_current_policy():
    policy_v1 = SimplePolicy(
        version=1,
        allowed_users={"alice", "bob"},
    )

    policy_v2 = SimplePolicy(
        version=2,
        allowed_users={"alice"},
    )

    stale_decision = authorize_with_policy(
        policy_v1,
        "bob",
    )

    current_decision = authorize_with_policy(
        policy_v2,
        "bob",
    )

    assert stale_decision is True
    assert current_decision is False

def test_detects_stale_policy_version():
    policy_v1 = SimplePolicy(
        version=1,
        allowed_users={"alice", "bob"},
    )

    assert is_policy_stale(
        policy_v1,
        current_version=2,
    ) is True


def test_current_policy_is_not_stale():
    policy_v2 = SimplePolicy(
        version=2,
        allowed_users={"alice"},
    )

    assert is_policy_stale(
        policy_v2,
        current_version=2,
    ) is False


def test_stale_policy_can_be_detected_before_authorization():
    policy_v1 = SimplePolicy(
        version=1,
        allowed_users={"alice", "bob"},
    )

    assert is_policy_stale(
        policy_v1,
        current_version=2,
    ) is True

def test_stale_policy_is_denied_even_when_it_would_allow():
    policy_v1 = SimplePolicy(
        version=1,
        allowed_users={"alice", "bob"},
    )

    assert authorize_with_stale_policy_protection(
        policy_v1,
        "bob",
        current_version=2,
    ) is False


def test_current_policy_can_allow_user():
    policy_v2 = SimplePolicy(
        version=2,
        allowed_users={"alice"},
    )

    assert authorize_with_stale_policy_protection(
        policy_v2,
        "alice",
        current_version=2,
    ) is True


def test_current_policy_still_denies_user():
    policy_v2 = SimplePolicy(
        version=2,
        allowed_users={"alice"},
    )

    assert authorize_with_stale_policy_protection(
        policy_v2,
        "bob",
        current_version=2,
    ) is False