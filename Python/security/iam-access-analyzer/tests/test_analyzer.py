from iam_analyzer.analyzer import AccessAnalyzer
from iam_analyzer.models import (
    AccessRequest,
    Action,
    Effect,
    Policy,
    Principal,
    PrincipalType,
    Resource,
)

from iam_analyzer.conditions import condition_matches
from iam_analyzer.matching import action_matches
from datetime import datetime
from iam_analyzer.expiration import policy_is_expired


def test_allow_when_matching_policy_exists():
    principal = Principal(
        id="user:alice@example.com",
        type=PrincipalType.USER,
    )

    resource = Resource(
        id="bucket:prod-data",
        type="storage_bucket",
    )

    action = Action(
        name="storage.objects.get",
    )

    policy = Policy(
        principal=principal,
        resource=resource,
        action=action,
        effect=Effect.ALLOW,
    )

    request = AccessRequest(
        principal=principal,
        resource=resource,
        action=action,
        context={},
    )

    analyzer = AccessAnalyzer(
        policies=[policy],
    )

    decision = analyzer.analyze(request)

    assert decision.effect == Effect.ALLOW


def test_deny_when_no_policy_matches():
    principal = Principal(
        id="user:bob@example.com",
        type=PrincipalType.USER,
    )

    resource = Resource(
        id="bucket:prod-data",
        type="storage_bucket",
    )

    action = Action(
        name="storage.objects.get",
    )

    alice = Principal(
        id="user:alice@example.com",
        type=PrincipalType.USER,
    )

    policy = Policy(
        principal=alice,
        resource=resource,
        action=action,
        effect=Effect.ALLOW,
    )

    request = AccessRequest(
        principal=principal,
        resource=resource,
        action=action,
        context={},
    )

    analyzer = AccessAnalyzer(
        policies=[policy],
    )

    decision = analyzer.analyze(request)

    assert decision.effect == Effect.DENY
    assert decision.reason == "No matching policy found"


def test_explicit_deny_overrides_allow():
    principal = Principal(
        id="user:alice@example.com",
        type=PrincipalType.USER,
    )

    resource = Resource(
        id="bucket:prod-data",
        type="storage_bucket",
    )

    action = Action(
        name="storage.objects.get",
    )

    allow_policy = Policy(
        principal=principal,
        resource=resource,
        action=action,
        effect=Effect.ALLOW,
    )

    deny_policy = Policy(
        principal=principal,
        resource=resource,
        action=action,
        effect=Effect.DENY,
    )

    request = AccessRequest(
        principal=principal,
        resource=resource,
        action=action,
        context={},
    )

    analyzer = AccessAnalyzer(
        policies=[allow_policy, deny_policy],
    )

    decision = analyzer.analyze(request)

    assert decision.effect == Effect.DENY
    assert decision.reason == "Explicit deny policy matched"


def test_exact_action_match():
    assert action_matches(
        "storage.objects.get",
        "storage.objects.get",
    )


def test_wildcard_action_match():
    assert action_matches(
        "storage.objects.*",
        "storage.objects.get",
    )


def test_wildcard_action_does_not_match_different_service():
    assert not action_matches(
        "storage.objects.*",
        "compute.instances.start",
    )


def test_full_wildcard_matches_any_action():
    assert action_matches(
        "*",
        "compute.instances.start",
    )

def test_analyzer_allows_wildcard_action():
    principal = Principal(
        id="user:alice@example.com",
        type=PrincipalType.USER,
    )

    resource = Resource(
        id="bucket:prod-data",
        type="storage_bucket",
    )

    policy_action = Action(
        name="storage.objects.*",
    )

    requested_action = Action(
        name="storage.objects.get",
    )

    policy = Policy(
        principal=principal,
        resource=resource,
        action=policy_action,
        effect=Effect.ALLOW,
    )

    request = AccessRequest(
        principal=principal,
        resource=resource,
        action=requested_action,
        context={},
    )

    analyzer = AccessAnalyzer(
        policies=[policy],
    )

    decision = analyzer.analyze(request)

    assert decision.effect == Effect.ALLOW


def test_condition_matches_when_context_matches():
    assert condition_matches(
        "environment",
        "production",
        {
            "environment": "production",
        },
    )


def test_condition_does_not_match_when_context_differs():
    assert not condition_matches(
        "environment",
        "production",
        {
            "environment": "development",
        },
    )


def test_condition_does_not_match_when_context_key_missing():
    assert not condition_matches(
        "environment",
        "production",
        {},
    )

def test_analyzer_allows_when_condition_matches():
    principal = Principal(
        id="user:alice@example.com",
        type=PrincipalType.USER,
    )

    resource = Resource(
        id="bucket:prod-data",
        type="storage_bucket",
    )

    action = Action(
        name="storage.objects.get",
    )

    policy = Policy(
        principal=principal,
        resource=resource,
        action=action,
        effect=Effect.ALLOW,
        condition_key="environment",
        condition_value="production",
    )

    request = AccessRequest(
        principal=principal,
        resource=resource,
        action=action,
        context={
            "environment": "production",
        },
    )

    analyzer = AccessAnalyzer(
        policies=[policy],
    )

    decision = analyzer.analyze(request)

    assert decision.effect == Effect.ALLOW

def test_analyzer_denies_when_condition_does_not_match():
    principal = Principal(
        id="user:alice@example.com",
        type=PrincipalType.USER,
    )

    resource = Resource(
        id="bucket:prod-data",
        type="storage_bucket",
    )

    action = Action(
        name="storage.objects.get",
    )

    policy = Policy(
        principal=principal,
        resource=resource,
        action=action,
        effect=Effect.ALLOW,
        condition_key="environment",
        condition_value="production",
    )

    request = AccessRequest(
        principal=principal,
        resource=resource,
        action=action,
        context={
            "environment": "development",
        },
    )

    analyzer = AccessAnalyzer(
        policies=[policy],
    )

    decision = analyzer.analyze(request)

    assert decision.effect == Effect.DENY
    assert decision.reason == "No matching policy found"

def test_policy_is_not_expired_before_expiration():
    expires_at = datetime(2026, 8, 31, 23, 59, 59)
    current_time = datetime(2026, 8, 25, 12, 0, 0)

    assert not policy_is_expired(
        expires_at,
        current_time,
    )

def test_policy_is_expired_after_expiration():
    expires_at = datetime(2026, 8, 31, 23, 59, 59)
    current_time = datetime(2026, 9, 1, 12, 0, 0)

    assert policy_is_expired(
        expires_at,
        current_time,
    )

def test_policy_is_expired_at_exact_expiration_time():
    expires_at = datetime(2026, 8, 31, 23, 59, 59)

    assert policy_is_expired(
        expires_at,
        expires_at,
    )

def test_analyzer_denies_when_policy_is_expired():
    principal = Principal(
        id="user:alice@example.com",
        type=PrincipalType.USER,
    )

    resource = Resource(
        id="bucket:prod-data",
        type="storage_bucket",
    )

    action = Action(
        name="storage.objects.get",
    )

    policy = Policy(
        principal=principal,
        resource=resource,
        action=action,
        effect=Effect.ALLOW,
        expires_at=datetime(2026, 8, 31, 23, 59, 59),
    )

    request = AccessRequest(
        principal=principal,
        resource=resource,
        action=action,
        context={},
    )

    analyzer = AccessAnalyzer(
        policies=[policy],
        current_time=datetime(2026, 9, 1, 12, 0, 0),
    )

    decision = analyzer.analyze(request)

    assert decision.effect == Effect.DENY
    assert decision.reason == "No matching policy found"

def test_analyzer_allows_when_policy_is_not_expired():
    principal = Principal(
        id="user:alice@example.com",
        type=PrincipalType.USER,
    )

    resource = Resource(
        id="bucket:prod-data",
        type="storage_bucket",
    )

    action = Action(
        name="storage.objects.get",
    )

    policy = Policy(
        principal=principal,
        resource=resource,
        action=action,
        effect=Effect.ALLOW,
        expires_at=datetime(2026, 8, 31, 23, 59, 59),
    )

    request = AccessRequest(
        principal=principal,
        resource=resource,
        action=action,
        context={},
    )

    analyzer = AccessAnalyzer(
        policies=[policy],
        current_time=datetime(2026, 8, 25, 12, 0, 0),
    )

    decision = analyzer.analyze(request)

    assert decision.effect == Effect.ALLOW

def test_wildcard_action_with_matching_condition_allows():
    principal = Principal(
        id="user:alice@example.com",
        type=PrincipalType.USER,
    )

    resource = Resource(
        id="bucket:prod-data",
        type="storage_bucket",
    )

    policy = Policy(
        principal=principal,
        resource=resource,
        action=Action(name="storage.objects.*"),
        effect=Effect.ALLOW,
        condition_key="environment",
        condition_value="production",
    )

    request = AccessRequest(
        principal=principal,
        resource=resource,
        action=Action(name="storage.objects.get"),
        context={
            "environment": "production",
        },
    )

    analyzer = AccessAnalyzer(
        policies=[policy],
        current_time=datetime(2026, 8, 25, 12, 0, 0),
    )

    decision = analyzer.analyze(request)

    assert decision.effect == Effect.ALLOW

def test_wildcard_action_with_failed_condition_denies():
    principal = Principal(
        id="user:alice@example.com",
        type=PrincipalType.USER,
    )

    resource = Resource(
        id="bucket:prod-data",
        type="storage_bucket",
    )

    policy = Policy(
        principal=principal,
        resource=resource,
        action=Action(name="storage.objects.*"),
        effect=Effect.ALLOW,
        condition_key="environment",
        condition_value="production",
    )

    request = AccessRequest(
        principal=principal,
        resource=resource,
        action=Action(name="storage.objects.get"),
        context={
            "environment": "development",
        },
    )

    analyzer = AccessAnalyzer(
        policies=[policy],
        current_time=datetime(2026, 8, 25, 12, 0, 0),
    )

    decision = analyzer.analyze(request)

    assert decision.effect == Effect.DENY

def test_wildcard_action_with_expired_policy_denies():
    principal = Principal(
        id="user:alice@example.com",
        type=PrincipalType.USER,
    )

    resource = Resource(
        id="bucket:prod-data",
        type="storage_bucket",
    )

    policy = Policy(
        principal=principal,
        resource=resource,
        action=Action(name="storage.objects.*"),
        effect=Effect.ALLOW,
        expires_at=datetime(2026, 8, 31, 23, 59, 59),
    )

    request = AccessRequest(
        principal=principal,
        resource=resource,
        action=Action(name="storage.objects.get"),
        context={},
    )

    analyzer = AccessAnalyzer(
        policies=[policy],
        current_time=datetime(2026, 9, 1, 12, 0, 0),
    )

    decision = analyzer.analyze(request)

    assert decision.effect == Effect.DENY

def test_explicit_deny_overrides_wildcard_allow():
    principal = Principal(
        id="user:alice@example.com",
        type=PrincipalType.USER,
    )

    resource = Resource(
        id="bucket:prod-data",
        type="storage_bucket",
    )

    allow_policy = Policy(
        principal=principal,
        resource=resource,
        action=Action(name="storage.objects.*"),
        effect=Effect.ALLOW,
    )

    deny_policy = Policy(
        principal=principal,
        resource=resource,
        action=Action(name="storage.objects.delete"),
        effect=Effect.DENY,
    )

    request = AccessRequest(
        principal=principal,
        resource=resource,
        action=Action(name="storage.objects.delete"),
        context={},
    )

    analyzer = AccessAnalyzer(
        policies=[
            allow_policy,
            deny_policy,
        ],
    )

    decision = analyzer.analyze(request)

    assert decision.effect == Effect.DENY
    assert decision.reason == "Explicit deny policy matched"

def test_expired_deny_does_not_override_valid_allow():
    principal = Principal(
        id="user:alice@example.com",
        type=PrincipalType.USER,
    )

    resource = Resource(
        id="bucket:prod-data",
        type="storage_bucket",
    )

    allow_policy = Policy(
        principal=principal,
        resource=resource,
        action=Action(name="storage.objects.get"),
        effect=Effect.ALLOW,
        expires_at=datetime(2026, 9, 30, 23, 59, 59),
    )

    expired_deny_policy = Policy(
        principal=principal,
        resource=resource,
        action=Action(name="storage.objects.get"),
        effect=Effect.DENY,
        expires_at=datetime(2026, 8, 20, 23, 59, 59),
    )

    request = AccessRequest(
        principal=principal,
        resource=resource,
        action=Action(name="storage.objects.get"),
        context={},
    )

    analyzer = AccessAnalyzer(
        policies=[
            allow_policy,
            expired_deny_policy,
        ],
        current_time=datetime(2026, 8, 25, 12, 0, 0),
    )

    decision = analyzer.analyze(request)

    assert decision.effect == Effect.ALLOW