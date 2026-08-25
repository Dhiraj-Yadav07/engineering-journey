# IAM Access Analyzer — Policy Evaluator v0.2 + FastAPI API

A Python-based IAM policy evaluation engine with a FastAPI REST interface. The project models principals, resources, actions, policies, contextual conditions, wildcard actions, policy expiration, and explicit deny precedence, and exposes the authorization evaluator through a documented HTTP API.

This project is part of the Engineering Journey security and IAM portfolio.

---

## Objective

Build a simplified IAM policy evaluator capable of answering:

> "Is this principal allowed to perform this action on this resource under the current context and time?"

Example:

```text
Principal:
user:alice@example.com

Resource:
bucket:prod-data

Action:
storage.objects.get

Context:
environment=production

Result:
ALLOW
```

---

## v0.2 Capabilities

The evaluator supports:

- Principal matching
- Resource matching
- Exact action matching
- Wildcard action matching
- IAM-style contextual conditions
- Policy expiration
- Explicit DENY precedence
- Deterministic time-based testing
- Automated pytest coverage

---

## Architecture

```text
                    AccessRequest
                         |
                         v
                +------------------+
                |  AccessAnalyzer   |
                +------------------+
                         |
          +--------------+--------------+
          |              |              |
          v              v              v
   Principal/      Action Matching   Expiration
    Resource       Exact/Wildcard      Check
    Matching
          |              |              |
          +--------------+--------------+
                         |
                         v
                    Conditions
                         |
                         v
                Matching Policies
                         |
                  +------+------+
                  |             |
                  v             v
               DENY          ALLOW
                  |
                  +------+
                         |
                         v
                  Final Decision
```

---

## Project Structure

```text
iam-access-analyzer/
│
├── .gitignore
├── pyproject.toml
├── README.md
│
├── src/
│   └── iam_analyzer/
│       ├── analyzer.py          # Core policy evaluation engine
│       ├── api.py              # FastAPI application and REST endpoint
│       ├── api_models.py       # Pydantic request models
│       ├── conditions.py       # IAM condition evaluation
│       ├── expiration.py       # Policy expiration logic
│       ├── matching.py         # Exact/wildcard action matching
│       └── models.py            # Domain dataclasses and enums
│
└── tests/
    ├── test_analyzer.py        # Policy evaluator tests
    └── test_api.py             # FastAPI endpoint tests
```

`.venv/`, `__pycache__/`, and pytest cache files are excluded through `.gitignore`.

---

## Data Model

### Principal

Represents the identity requesting access.

Supported principal types:

```text
USER
SERVICE_ACCOUNT
GROUP
ROLE
```

Example:

```python
Principal(
    id="user:alice@example.com",
    type=PrincipalType.USER,
)
```

### Resource

Represents the protected resource.

Example:

```python
Resource(
    id="bucket:prod-data",
    type="storage_bucket",
)
```

### Action

Represents the operation being requested.

Example:

```python
Action(
    name="storage.objects.get",
)
```

### Policy

A policy connects a principal, resource, action, and authorization effect.

Example:

```python
Policy(
    principal=principal,
    resource=resource,
    action=action,
    effect=Effect.ALLOW,
)
```

A policy can additionally contain:

```text
condition_key
condition_value
expires_at
```

### AccessRequest

Represents an authorization request.

```python
AccessRequest(
    principal=principal,
    resource=resource,
    action=action,
    context={
        "environment": "production",
    },
)
```

### AccessDecision

Represents the evaluator result:

```text
ALLOW
DENY
```

along with a reason explaining the decision.

---

# Policy Evaluation

The evaluator processes policies in the following order:

```text
1. Principal match
       |
2. Resource match
       |
3. Action match
       |
4. Expiration check
       |
5. Condition evaluation
       |
6. Collect matching policies
       |
7. Explicit DENY evaluation
       |
8. ALLOW if a matching policy exists
       |
9. Otherwise DENY
```

---

# Wildcard Action Matching

Policies can use wildcard actions.

Example:

```text
storage.objects.*
```

matches:

```text
storage.objects.get
storage.objects.create
storage.objects.delete
storage.objects.update
```

Example policy:

```python
Policy(
    principal=principal,
    resource=resource,
    action=Action(name="storage.objects.*"),
    effect=Effect.ALLOW,
)
```

Request:

```python
Action(
    name="storage.objects.get",
)
```

Result:

```text
ALLOW
```

---

# IAM Conditions

Policies can require contextual attributes.

Example:

```python
Policy(
    principal=principal,
    resource=resource,
    action=Action(name="storage.objects.get"),
    effect=Effect.ALLOW,
    condition_key="environment",
    condition_value="production",
)
```

The request supplies:

```python
context={
    "environment": "production",
}
```

The condition matches and the policy applies.

If the request instead contains:

```python
context={
    "environment": "development",
}
```

the policy does not match.

Missing conditions also fail closed:

```text
Missing condition
       |
       v
Condition = False
       |
       v
Policy does not match
```

---

# Policy Expiration

Policies can have an expiration timestamp.

Example:

```python
Policy(
    principal=principal,
    resource=resource,
    action=action,
    effect=Effect.ALLOW,
    expires_at=datetime(2026, 8, 31, 23, 59, 59),
)
```

Before expiration:

```text
Current time < expiration
        |
        v
Policy is valid
```

At or after expiration:

```text
Current time >= expiration
        |
        v
Policy is expired
        |
        v
Policy is ignored
```

Expired policies cannot grant access.

---

# Explicit DENY Precedence

The evaluator implements the security principle:

> Explicit DENY overrides ALLOW.

Example:

```text
Policy 1:
storage.objects.* → ALLOW

Policy 2:
storage.objects.delete → DENY
```

Request:

```text
storage.objects.delete
```

Both policies match, but:

```text
Explicit DENY
      |
      v
Final result = DENY
```

This mirrors an important IAM authorization concept used in cloud security systems.

---

# Expired Policies

Expired policies are ignored during policy matching.

For example:

```text
ALLOW policy
expires: 2026-08-20

Current time:
2026-08-25
```

The policy no longer participates in the authorization decision.

This also means an expired DENY cannot override a currently valid ALLOW.

---

# Deterministic Time Testing

The evaluator accepts an optional `current_time`:

```python
AccessAnalyzer(
    policies=policies,
    current_time=datetime(2026, 8, 25, 12, 0, 0),
)
```

This makes expiration behavior deterministic and avoids tests depending on the real system clock.

When no `current_time` is supplied, the evaluator uses the current system time.

---

# Example Evaluation

Policy:

```text
Principal:
user:alice@example.com

Resource:
bucket:prod-data

Action:
storage.objects.*

Effect:
ALLOW

Condition:
environment == production

Expiration:
2026-08-31 23:59:59
```

Request:

```text
Principal:
user:alice@example.com

Resource:
bucket:prod-data

Action:
storage.objects.get

Context:
environment=production

Current time:
2026-08-25 12:00:00
```

Evaluation:

```text
Principal matches       ✓
Resource matches        ✓
Wildcard action matches ✓
Policy not expired      ✓
Condition matches       ✓
Explicit DENY           ✗
                         |
                         v
                       ALLOW
```

---

# Testing

The project uses `pytest` for both unit-level evaluator testing and API-level testing.

Run:

```powershell
pytest
```

Current test evidence:

```text
27 tests collected
27 passed
0 failed
```

The test suite covers:

```text
✓ Matching ALLOW policy
✓ No matching policy
✓ Explicit DENY
✓ Wildcard action
✓ Wildcard action mismatch
✓ Conditions
✓ Missing conditions
✓ Expiration
✓ Exact expiration boundary
✓ Expired policies
✓ Wildcard + condition
✓ Wildcard + expiration
✓ Explicit DENY + wildcard ALLOW
✓ Expired DENY + valid ALLOW
✓ FastAPI health endpoint
✓ FastAPI access-analysis endpoint
✓ API validation behavior
✓ API ALLOW / DENY behavior
```

The API tests use FastAPI's test client and exercise the endpoint without requiring a running Uvicorn server.

# Installation

Create the virtual environment:

```powershell
python -m venv .venv
```

Activate it:

```powershell
.\.venv\Scripts\Activate.ps1
```

Install the project:

```powershell
python -m pip install -e .
```

Install the development/runtime dependencies used by this build:

```powershell
python -m pip install pytest fastapi uvicorn
```

Verify FastAPI:

```powershell
python -c "import fastapi; print(fastapi.__version__)"
```

Run the evaluator/API test suite:

```powershell
pytest
```

---

# FastAPI REST API

The policy evaluator is exposed through a REST API implemented with FastAPI.

## Start the API

From the project root:

```powershell
python -m uvicorn iam_analyzer.api:app --reload
```

The development server starts on:

```text
http://127.0.0.1:8000
```

`--reload` enables automatic server reload when source files change. The terminal remains occupied by the running Uvicorn process; this is expected. Stop it with `Ctrl+C`.

## Health Check

Endpoint:

```http
GET /health
```

PowerShell:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
```

Expected response:

```json
{
  "status": "ok"
}
```

## Analyze Access

Endpoint:

```http
POST /analyze-access
Content-Type: application/json
```

Example request:

```json
{
  "principal": {
    "id": "user:alice@example.com",
    "type": "user"
  },
  "resource": {
    "id": "bucket:prod-data",
    "type": "storage_bucket"
  },
  "action": {
    "name": "storage.objects.get"
  },
  "context": {}
}
```

Example response:

```json
{
  "effect": "allow",
  "reason": "Matching allow policy found"
}
```

A non-matching principal/request is evaluated through the same policy engine and can return:

```json
{
  "effect": "deny",
  "reason": "No matching policy found"
}
```

## OpenAPI / Swagger Documentation

FastAPI automatically exposes the OpenAPI contract and interactive documentation.

Swagger UI:

```text
http://127.0.0.1:8000/docs
```

Raw OpenAPI specification:

```text
http://127.0.0.1:8000/openapi.json
```

The Swagger UI was validated manually during this build, including successful ALLOW and DENY access-analysis requests.

## API Request Validation

Pydantic models validate incoming JSON before it reaches the IAM evaluator.

The API request model contains:

```text
AccessRequestBody
├── principal
│   ├── id
│   └── type
├── resource
│   ├── id
│   └── type
├── action
│   └── name
└── context
```

Invalid or missing request fields are rejected by FastAPI with an HTTP `422` validation response.

---

# API Design Boundary

The API layer deliberately separates HTTP concerns from authorization logic:

```text
HTTP JSON
   |
   v
Pydantic models
   |
   v
Internal IAM dataclasses
   |
   v
AccessAnalyzer
   |
   v
AccessDecision
   |
   v
HTTP JSON response
```

This keeps the core evaluator independent of FastAPI and makes the policy engine easier to test and reuse.

The current API is a learning/portfolio interface rather than a production policy-management service. It does not yet provide a persistent policy store, authentication, authorization of API callers, or policy-management endpoints.

---

# Python Environment

Developed and tested with:

```text
Python 3.14.7
pytest 9.1.1
FastAPI 0.141.1
Uvicorn 0.52.4
Pydantic 2.13.4
```

# Security Design Principles Demonstrated

## 1. Default deny

If no applicable policy grants access:

```text
DENY
```

## 2. Explicit deny precedence

A matching DENY overrides matching ALLOW policies.

## 3. Fail closed

Missing or failed conditions do not grant access.

## 4. Time-bounded authorization

Policies can expire automatically.

## 5. Context-aware authorization

Authorization decisions can depend on request context.

## 6. Deterministic evaluation

The evaluator can receive a fixed evaluation timestamp, enabling reliable testing.

---

# Limitations

This is a learning and portfolio implementation rather than a production IAM engine.

It currently does not implement:

- Resource hierarchy
- Policy inheritance
- Groups and group membership resolution
- Role assumption
- Attribute-based principal matching
- Multiple condition operators
- IP/CIDR conditions
- Time-of-day conditions
- Policy versioning
- Policy documents such as JSON IAM policies
- Resource-based versus identity-based policies
- Organization-level policy constraints
- Permission boundaries
- Service control policies
- Credential/session policies

These are potential future extensions.

---

# Future Roadmap

The current objective is complete: the evaluator has been exposed through a FastAPI REST endpoint with generated OpenAPI documentation.

## v0.3 / API Enhancements

Potential next enhancements:

```text
JSON policy parser
Policy input through API
Policy collections / policy store
Multiple condition operators
CIDR/IP conditions
Resource wildcard matching
Multiple principals
Structured decision reasons
```

## v0.4 / Cloud IAM Modeling

Potential cloud IAM modeling:

```text
Identity policies
Resource policies
Role assumption
Groups and group membership
Permission boundaries
```

## v0.5 / Enterprise IAM Simulation

Potential enterprise capabilities:

```text
AWS IAM semantics
GCP IAM semantics
Policy inheritance
Organization constraints
Policy analysis/reporting
Access graph visualization
Authentication and API authorization
```

---

# Portfolio Outcome

This project demonstrates practical Python implementation of an IAM authorization engine and its exposure as a REST service.

It combines:

```text
Python
+
Object-oriented design
+
Dataclasses
+
Enums
+
Policy modeling
+
Authorization logic
+
Wildcard matching
+
Context-aware access control
+
Time-based authorization
+
Automated testing
+
FastAPI REST API
+
Pydantic request validation
+
Uvicorn application serving
+
OpenAPI / Swagger documentation
```

The project is intentionally designed as an incremental engineering exercise:

```text
v0.1
Basic IAM policy evaluator
        |
        v
v0.2
Wildcard matching
+
Conditions
+
Expiration
+
Explicit DENY precedence
+
23 evaluator tests
        |
        v
API Build
FastAPI REST endpoint
+
Pydantic request validation
+
OpenAPI / Swagger docs
+
API tests
+
27 total automated tests
        |
        v
Future
Enterprise IAM policy simulation
```

## Current Build Evidence

```text
Core policy evaluator
        ✓

Wildcard IAM action matching
        ✓

IAM-style conditions
        ✓

Policy expiration
        ✓

Explicit DENY precedence
        ✓

Deterministic time testing
        ✓

FastAPI REST endpoint
        ✓

Pydantic request validation
        ✓

Swagger UI / OpenAPI
        ✓

27 automated tests passing
        ✓
```
