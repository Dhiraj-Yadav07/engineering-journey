from pydantic import BaseModel


class PrincipalRequest(BaseModel):
    id: str
    type: str


class ResourceRequest(BaseModel):
    id: str
    type: str


class ActionRequest(BaseModel):
    name: str


class AccessRequestBody(BaseModel):
    principal: PrincipalRequest
    resource: ResourceRequest
    action: ActionRequest
    context: dict[str, str]


class AccessDecisionResponse(BaseModel):
    effect: str
    reason: str
    risk_score: int