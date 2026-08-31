from authorization_engine.abac_models import (
    AccessContext,
    ABACRequest,
    Resource,
    User,
)
from authorization_engine.abac_engine import ABACEngine


def make_request(
    user_attributes=None,
    resource_attributes=None,
    context_attributes=None,
    action="read",
):
    user = User(
        id="alice",
        attributes=user_attributes or {},
    )

    resource = Resource(
        id="report-123",
        attributes=resource_attributes or {},
    )

    context = AccessContext(
        attributes=context_attributes or {},
    )

    return ABACRequest(
        user=user,
        resource=resource,
        action=action,
        context=context,
    )


def test_matching_attributes_are_allowed():
    engine = ABACEngine()

    request = make_request(
        user_attributes={
            "department": "engineering",
        },
        resource_attributes={
            "department": "engineering",
        },
        context_attributes={
            "network": "corporate",
        },
    )

    decision = engine.authorize(request)

    assert decision.allowed is True


def test_department_mismatch_is_denied():
    engine = ABACEngine()

    request = make_request(
        user_attributes={
            "department": "engineering",
        },
        resource_attributes={
            "department": "finance",
        },
        context_attributes={
            "network": "corporate",
        },
    )

    decision = engine.authorize(request)

    assert decision.allowed is False


def test_non_corporate_network_is_denied():
    engine = ABACEngine()

    request = make_request(
        user_attributes={
            "department": "engineering",
        },
        resource_attributes={
            "department": "engineering",
        },
        context_attributes={
            "network": "public",
        },
    )

    decision = engine.authorize(request)

    assert decision.allowed is False


def test_unsupported_action_is_denied():
    engine = ABACEngine()

    request = make_request(
        user_attributes={
            "department": "engineering",
        },
        resource_attributes={
            "department": "engineering",
        },
        context_attributes={
            "network": "corporate",
        },
        action="delete",
    )

    decision = engine.authorize(request)

    assert decision.allowed is False


def test_missing_user_attribute_is_denied():
    engine = ABACEngine()

    request = make_request(
        user_attributes={},
        resource_attributes={
            "department": "engineering",
        },
        context_attributes={
            "network": "corporate",
        },
    )

    decision = engine.authorize(request)

    assert decision.allowed is False


def test_missing_resource_attribute_is_denied():
    engine = ABACEngine()

    request = make_request(
        user_attributes={
            "department": "engineering",
        },
        resource_attributes={},
        context_attributes={
            "network": "corporate",
        },
    )

    decision = engine.authorize(request)

    assert decision.allowed is False


def test_missing_context_attribute_is_denied():
    engine = ABACEngine()

    request = make_request(
        user_attributes={
            "department": "engineering",
        },
        resource_attributes={
            "department": "engineering",
        },
        context_attributes={},
    )

    decision = engine.authorize(request)

    assert decision.allowed is False