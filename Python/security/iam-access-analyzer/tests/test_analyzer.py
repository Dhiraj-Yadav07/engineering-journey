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
    )

    analyzer = AccessAnalyzer(
        policies=[allow_policy, deny_policy],
    )

    decision = analyzer.analyze(request)

    assert decision.effect == Effect.DENY
    assert decision.reason == "Explicit deny policy matched"