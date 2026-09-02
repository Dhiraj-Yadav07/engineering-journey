import pytest

from authorization_engine.failure_modes import (
    PolicyUnavailableError,
    authorize_fail_closed,
    authorize_fail_open,
)


def policy_allows():
    return True


def policy_denies():
    return False


def policy_unavailable():
    raise PolicyUnavailableError("Policy store unavailable")

def test_fail_open_preserves_allow():
    assert authorize_fail_open(policy_allows) is True


def test_fail_open_preserves_deny():
    assert authorize_fail_open(policy_denies) is False


def test_fail_open_allows_when_policy_unavailable():
    assert authorize_fail_open(policy_unavailable) is True


def test_fail_closed_preserves_allow():
    assert authorize_fail_closed(policy_allows) is True


def test_fail_closed_preserves_deny():
    assert authorize_fail_closed(policy_denies) is False


def test_fail_closed_denies_when_policy_unavailable():
    assert authorize_fail_closed(policy_unavailable) is False