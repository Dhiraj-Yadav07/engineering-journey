import pytest
from datetime import datetime, timezone

from authorization_engine.policy_models import PolicyVersion
from authorization_engine.policy_store import VersionedPolicyStore


@pytest.fixture
def store():
    return VersionedPolicyStore()


@pytest.fixture
def timestamp():
    return datetime.now(timezone.utc)


def test_first_policy_version_must_be_one(store, timestamp):
    policy = PolicyVersion(
        "document-read",
        1,
        "alice can read report-123",
        timestamp,
        "admin",
    )

    store.add_version(policy)

    assert store.get_version("document-read", 1) == policy


def test_policy_versions_are_sequential(store, timestamp):
    v1 = PolicyVersion(
        "document-read",
        1,
        "alice can read report-123",
        timestamp,
        "admin",
    )

    v2 = PolicyVersion(
        "document-read",
        2,
        "alice and bob can read report-123",
        timestamp,
        "admin",
    )

    store.add_version(v1)
    store.add_version(v2)

    assert store.get_version("document-read", 1) == v1
    assert store.get_version("document-read", 2) == v2


def test_latest_returns_highest_version(store, timestamp):
    v1 = PolicyVersion(
        "document-read",
        1,
        "alice can read report-123",
        timestamp,
        "admin",
    )

    v2 = PolicyVersion(
        "document-read",
        2,
        "alice and bob can read report-123",
        timestamp,
        "admin",
    )

    store.add_version(v1)
    store.add_version(v2)

    assert store.get_latest("document-read") == v2


def test_historical_version_is_preserved(store, timestamp):
    v1 = PolicyVersion(
        "document-read",
        1,
        "alice can read report-123",
        timestamp,
        "admin",
    )

    v2 = PolicyVersion(
        "document-read",
        2,
        "alice and bob can read report-123",
        timestamp,
        "admin",
    )

    store.add_version(v1)
    store.add_version(v2)

    historical = store.get_version("document-read", 1)

    assert historical.rule == "alice can read report-123"
    assert historical.version == 1


def test_list_versions_returns_policy_history(store, timestamp):
    v1 = PolicyVersion(
        "document-read",
        1,
        "alice can read report-123",
        timestamp,
        "admin",
    )

    v2 = PolicyVersion(
        "document-read",
        2,
        "alice and bob can read report-123",
        timestamp,
        "admin",
    )

    store.add_version(v1)
    store.add_version(v2)

    versions = store.list_versions("document-read")

    assert versions == [v1, v2]


def test_version_gap_is_rejected(store, timestamp):
    v1 = PolicyVersion(
        "document-read",
        1,
        "alice can read report-123",
        timestamp,
        "admin",
    )

    v3 = PolicyVersion(
        "document-read",
        3,
        "alice and bob can read report-123",
        timestamp,
        "admin",
    )

    store.add_version(v1)

    with pytest.raises(ValueError, match="sequential"):
        store.add_version(v3)


def test_first_version_cannot_start_at_two(store, timestamp):
    policy = PolicyVersion(
        "document-read",
        2,
        "alice can read report-123",
        timestamp,
        "admin",
    )

    with pytest.raises(
        ValueError,
        match="first policy version must be 1",
    ):
        store.add_version(policy)


def test_missing_version_raises_key_error(store):
    with pytest.raises(KeyError):
        store.get_version("document-read", 1)


def test_missing_policy_has_no_versions(store):
    assert store.list_versions("nonexistent-policy") == []


def test_missing_policy_latest_raises_key_error(store):
    with pytest.raises(KeyError):
        store.get_latest("nonexistent-policy")

def test_historical_policy_version_remains_available():
    from authorization_engine.policy_models import PolicyVersion
    from authorization_engine.policy_store import VersionedPolicyStore
    from datetime import datetime, timezone

    store = VersionedPolicyStore()
    now = datetime.now(timezone.utc)

    store.add_version(
        PolicyVersion(
            "document-read",
            1,
            "alice can read report-123",
            now,
            "admin",
        )
    )

    store.add_version(
        PolicyVersion(
            "document-read",
            2,
            "alice and bob can read report-123",
            now,
            "security-admin",
        )
    )

    version_one = store.get_version(
        "document-read",
        1,
    )

    version_two = store.get_version(
        "document-read",
        2,
    )

    assert version_one is not None
    assert version_two is not None

    assert version_one.version == 1
    assert version_one.rule == "alice can read report-123"

    assert version_two.version == 2
    assert version_two.rule == "alice and bob can read report-123"