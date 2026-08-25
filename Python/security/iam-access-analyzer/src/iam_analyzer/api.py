from fastapi import FastAPI

from iam_analyzer.analyzer import AccessAnalyzer
from iam_analyzer.api_models import (
    AccessDecisionResponse,
    AccessRequestBody,
)
from iam_analyzer.models import (
    AccessRequest,
    Action,
    Effect,
    Policy,
    Principal,
    PrincipalType,
    Resource,
)


app = FastAPI(
    title="IAM Access Analyzer API",
    description=(
        "REST API for evaluating IAM access requests "
        "against configured authorization policies."
    ),
    version="0.3.0",
)


@app.get(
    "/health",
    summary="Check API health",
    description="Returns the health status of the IAM Access Analyzer API.",
)
def health_check():
    return {"status": "ok"}


@app.post(
    "/analyze-access",
    summary="Evaluate IAM access",
    description=(
        "Evaluates whether a principal is allowed to perform "
        "an action against a resource."
    ),
    response_model=AccessDecisionResponse,
)
def analyze_access(request: AccessRequestBody):

    principal = Principal(
        id=request.principal.id,
        type=PrincipalType(request.principal.type),
    )

    resource = Resource(
        id=request.resource.id,
        type=request.resource.type,
    )

    action = Action(
        name=request.action.name,
    )

    access_request = AccessRequest(
        principal=principal,
        resource=resource,
        action=action,
        context=request.context,
    )

    policy = Policy(
        principal=Principal(
            id="user:alice@example.com",
            type=PrincipalType.USER,
        ),
        resource=resource,
        action=action,
        effect=Effect.ALLOW,
    )

    analyzer = AccessAnalyzer(
        policies=[policy],
    )

    decision = analyzer.analyze(access_request)

    return {
        "effect": decision.effect.value,
        "reason": decision.reason,
    }