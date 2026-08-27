# IAM Access Analyzer — Security Analyzer v0.3 + FastAPI API

A Python-based IAM authorization and security analysis engine with a FastAPI REST interface. The project models principals, resources, actions, policies, contextual conditions, wildcard actions, policy expiration, explicit deny precedence, audit logging, risk scoring, and privileged access detection.

The analyzer exposes authorization decisions through a documented HTTP API and enriches those decisions with security-oriented metadata.

This project is part of the Engineering Journey security and IAM portfolio.

---

## Objective

Build a simplified IAM policy evaluator capable of answering:

> "Is this principal allowed to perform this action on this resource under the current context and time?"

The v0.3 security build extends that authorization decision with:

- Audit event recording
- Action-based risk scoring
- Privileged access detection
- Security metadata returned through the REST API
- Automated regression coverage for all previous capabilities

Example:

```text
Principal:
user:alice@example.com

Resource:
bucket:prod-data

Action:
storage.objects.delete

Context:
environment=production

Result:
ALLOW

Risk score:
70

Privileged:
false
```

---

# v0.3 Security Capabilities

The analyzer currently supports:

### Authorization
- Principal matching
- Resource matching
- Exact action matching
- Wildcard action matching
- IAM-style contextual conditions
- Policy expiration
- Explicit DENY precedence
- Default deny behavior
- Deterministic time-based testing

### Security Analysis
- Audit event generation
- In-memory audit logging
- Action-based risk scoring
- Privileged access detection
- Security metadata attached to access decisions
- Risk score exposed through the API
- Privileged flag exposed through the API

### API
- FastAPI REST endpoint
- Pydantic request/response validation
- OpenAPI schema
- Swagger UI
- Health endpoint
- Access-analysis endpoint

### Testing
- Unit tests for authorization logic
- Unit tests for audit models
- Unit tests for audit logging
- Unit tests for risk scoring
- Unit tests for privileged access detection
- API tests
- Full regression suite

Current build evidence:

```text
41 tests collected
41 passed
0 failed
```

---

# Architecture

Two architecture diagrams are maintained with this project:

```text
docs/
└── architecture/
    ├── iam-access-analyzer-hld.png
    └── iam-access-analyzer-lld.png
```

The diagrams are intended to document the application independently from the README.

## High-Level Architecture

The HLD shows the major application boundaries:

```text
                    Client
                      |
                      v
              +---------------+
              |   FastAPI     |
              | REST API      |
              +---------------+
                      |
                      v
              +---------------+
              | AccessAnalyzer|
              +---------------+
                      |
       +--------------+--------------+
       |              |              |
       v              v              v
 Authorization    Risk Analysis   Privileged
 Evaluation       / Scoring       Detection
       |              |              |
       +--------------+--------------+
                      |
                      v
                AccessDecision
                      |
          +-----------+-----------+
          |           |           |
          v           v           v
       Effect      Risk Score   Privileged
       /Reason                   Flag
                      |
                      v
                Audit Logger
```

The application deliberately separates the HTTP interface from the authorization/security analysis domain.

---

# Low-Level Architecture

The LLD represents the Python module-level design:

```text
FastAPI
   |
   v
api.py
   |
   +----> api_models.py
   |
   v
AccessAnalyzer
   |
   +----> matching.py
   +----> conditions.py
   +----> expiration.py
   +----> risk.py
   +----> privileged.py
   +----> audit.py
   +----> audit_logger.py
   |
   v
models.py
   |
   +----> AccessRequest
   +----> AccessDecision
   +----> Principal
   +----> Resource
   +----> Action
   +----> Policy
```

The core analyzer remains independent of FastAPI.

---

# Project Structure

```text
iam-access-analyzer/
│
├── .gitignore
├── Dockerfile
├── pyproject.toml
├── README.md
│
├── docs/
│   └── architecture/
│       ├── iam-access-analyzer-hld.png
│       └── iam-access-analyzer-lld.png
│
├── src/
│   └── iam_analyzer/
│       ├── __init__.py
│       ├── analyzer.py          # Core authorization/security evaluation
│       ├── api.py              # FastAPI application and REST endpoint
│       ├── api_models.py       # Pydantic request/response models
│       ├── audit.py             # Audit event domain model
│       ├── audit_logger.py      # In-memory audit event logger
│       ├── conditions.py        # IAM condition evaluation
│       ├── expiration.py       # Policy expiration logic
│       ├── matching.py         # Exact/wildcard action matching
│       ├── models.py            # Domain dataclasses and enums
│       ├── privileged.py        # Privileged action detection
│       └── risk.py              # Action risk scoring
│
└── tests/
    ├── test_analyzer.py         # Authorization/security analyzer tests
    ├── test_api.py              # FastAPI endpoint tests
    ├── test_audit.py             # AuditEvent tests
    ├── test_audit_logger.py      # AuditLogger tests
    ├── test_privileged.py        # Privileged detection tests
    └── test_risk.py              # Risk scoring tests
```

`.venv/`, `__pycache__/`, and pytest cache files are excluded through `.gitignore`.

---

# Data Model

## Principal

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

## Resource

Represents the protected resource.

Example:

```python
Resource(
    id="bucket:prod-data",
    type="storage_bucket",
)
```

## Action

Represents the operation being requested.

Example:

```python
Action(
    name="storage.objects.get",
)
```

## Policy

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

## AccessRequest

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

## AccessDecision

Represents the evaluator result:

```text
ALLOW
DENY
```

along with:

```text
reason
risk_score
privileged
```

The decision therefore combines the authorization outcome with security-analysis metadata.

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
       |
10. Calculate risk score
       |
11. Detect privileged access
       |
12. Record audit event
       |
13. Return AccessDecision
```

The security enrichment is performed as part of the analyzer's final decision path so that the API and future consumers receive consistent metadata.

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

Missing conditions fail closed:

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

An expired DENY also cannot override a currently valid ALLOW.

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

# Audit Logging

v0.3 introduces an explicit audit model and audit logger.

## AuditEvent

Each authorization decision can produce an audit event containing:

```text
timestamp
principal
resource
action
effect
reason
```

Conceptually:

```python
AuditEvent(
    timestamp=...,
    principal="user:alice@example.com",
    resource="bucket:prod-data",
    action="storage.objects.delete",
    effect="allow",
    reason="Matching allow policy found",
)
```

## AuditLogger

The current implementation provides an in-memory logger:

```python
logger = AuditLogger()

logger.record(event)
```

Events are retained in:

```python
logger.events
```

This provides a deterministic and testable foundation for future persistence or integration with an enterprise logging platform.

### Important design boundary

The current logger is intentionally lightweight. It is not a production SIEM, durable event store, or centralized audit backend.

Potential future integrations include:

```text
Cloud Logging
CloudWatch
Splunk
Elastic
OpenSearch
Kafka
Database / event store
```

---

# Risk Scoring

v0.3 introduces action-based risk scoring.

The current scoring model is intentionally simple and deterministic.

| Action category | Example | Score |
|---|---|---:|
| Read | `storage.objects.get` | 10 |
| Create | `storage.objects.create` | 40 |
| Delete | `storage.objects.delete` | 70 |
| IAM operation | `iam.roles.update` | 70 |
| Other | unmatched action | 20 |

The scoring function is implemented in:

```text
src/iam_analyzer/risk.py
```

Example:

```python
action = Action(
    name="storage.objects.delete",
)

score = calculate_risk_score(action)

assert score == 70
```

The current model is intentionally a baseline rather than a formal enterprise risk engine.

Future scoring can incorporate additional dimensions such as:

```text
Resource sensitivity
Environment
Principal type
Production vs development
Data classification
Privilege level
Action frequency
Policy age
Access path
Anomaly indicators
```

---

# Privileged Access Detection

v0.3 introduces privileged access detection.

The detection logic is implemented in:

```text
src/iam_analyzer/privileged.py
```

The analyzer evaluates the requested action and determines whether it represents privileged access.

Example concept:

```python
is_privileged_action(
    Action(name="iam.roles.update")
)
```

returns:

```text
True
```

A normal read operation such as:

```text
storage.objects.get
```

is not considered privileged by the current baseline rules.

The objective is to distinguish ordinary resource access from operations that can materially change IAM configuration or security posture.

This is a deliberately small policy engine at v0.3 and can be expanded later with a richer privileged-action taxonomy.

---

# Security Decision Model

A v0.3 decision can be represented conceptually as:

```text
                    AccessRequest
                         |
                         v
                +------------------+
                | AccessAnalyzer    |
                +------------------+
                         |
        +----------------+----------------+
        |                |                |
        v                v                v
 Authorization      Risk Scoring    Privileged Detection
        |                |                |
        +----------------+----------------+
                         |
                         v
                  AccessDecision
                         |
       +-----------------+-----------------+
       |                 |                 |
       v                 v                 v
    Effect           Risk Score       Privileged
       |                 |                 |
       +-----------------+-----------------+
                         |
                         v
                    AuditEvent
                         |
                         v
                    AuditLogger
```

This design keeps authorization, security classification, and audit recording logically distinct while allowing the analyzer to return a single coherent security decision.

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
storage.objects.delete

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

Risk score:
70

Privileged:
false

Audit event:
recorded
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

`--reload` enables automatic server reload when source files change.

Stop it with:

```text
Ctrl+C
```

---

# Health Check

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

---

# Analyze Access

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
    "name": "storage.objects.delete"
  },
  "context": {}
}
```

Example v0.3 response:

```json
{
  "effect": "allow",
  "reason": "Matching allow policy found",
  "risk_score": 70,
  "privileged": false
}
```

A non-matching principal can return:

```json
{
  "effect": "deny",
  "reason": "No matching policy found",
  "risk_score": 10,
  "privileged": false
}
```

The API response therefore exposes both authorization and security-analysis information.

---

# OpenAPI / Swagger Documentation

FastAPI automatically exposes the OpenAPI contract and interactive documentation.

Swagger UI:

```text
http://127.0.0.1:8000/docs
```

Raw OpenAPI specification:

```text
http://127.0.0.1:8000/openapi.json
```

The Swagger UI can be used to submit access-analysis requests and inspect the returned authorization/security metadata.

---

# API Request Validation

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

The response model contains:

```text
AccessDecisionResponse
├── effect
├── reason
├── risk_score
└── privileged
```

Invalid or missing request fields are rejected by FastAPI with an HTTP `422` validation response.

---

# API Design Boundary

The API layer deliberately separates HTTP concerns from authorization/security logic:

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
   +----> Authorization
   |
   +----> Risk scoring
   |
   +----> Privileged detection
   |
   +----> Audit logging
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

# Testing

The project uses `pytest` for unit-level evaluator testing and API-level testing.

Run the complete suite:

```powershell
pytest
```

Current v0.3 test evidence:

```text
35+ tests
0 failed
```

The final v0.3 build includes:

```text
✓ Core analyzer tests
✓ Wildcard action tests
✓ IAM condition tests
✓ Policy expiration tests
✓ Explicit DENY tests
✓ Audit event tests
✓ Audit logger tests
✓ Risk scoring tests
✓ Privileged access detection tests
✓ FastAPI endpoint tests
```

At the completed privileged-access stage, the full regression suite produced:

```text
41 passed
1 warning
0 failed
```

The warning is a dependency deprecation warning originating from the installed FastAPI/Starlette test-client stack and does not represent a failing application test.

---

# Test Coverage by Capability

## Authorization

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
```

## Security

```text
✓ AuditEvent creation
✓ AuditLogger recording
✓ Analyzer audit event generation
✓ Read action risk scoring
✓ Write action risk scoring
✓ Delete action risk scoring
✓ IAM action risk scoring
✓ Privileged action detection
✓ Non-privileged action detection
✓ Analyzer privileged flag
```

## API

```text
✓ FastAPI health endpoint
✓ FastAPI access-analysis endpoint
✓ API validation behavior
✓ API ALLOW / DENY behavior
✓ API risk score response
✓ API privileged flag response
```

The API tests use FastAPI's test client and exercise the endpoint without requiring a running Uvicorn server.

---

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

Install the development/runtime dependencies:

```powershell
python -m pip install pytest fastapi uvicorn
```

Verify FastAPI:

```powershell
python -c "import fastapi; print(fastapi.__version__)"
```

Run the full test suite:

```powershell
pytest
```

---

# Python Environment

The v0.3 development environment used for the build included:

```text
Python 3.14.7
pytest 9.1.1
FastAPI
Uvicorn
Pydantic
```

Exact installed versions can be verified from the active virtual environment.

---

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

## 7. Security observability

Authorization decisions can generate structured audit events.

## 8. Risk-aware authorization analysis

Actions receive a deterministic baseline risk score.

## 9. Privileged access identification

Security-sensitive operations can be identified separately from ordinary access.

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
- Persistent audit storage
- Centralized SIEM integration
- Dynamic risk scoring based on resource sensitivity
- Machine-learning/anomaly-based risk detection
- Comprehensive privileged-action taxonomy
- API authentication
- API authorization
- Persistent policy management

These are potential future extensions.

---

# Docker Containerization

v0.3 is containerized with Docker so the analyzer can be run as a self-contained Linux container without relying on the host Python environment.

The container packages:

```text
Python runtime
+
IAM Access Analyzer package
+
FastAPI
+
Uvicorn
```

The container exposes the FastAPI application on port `8000`.

## Docker Prerequisites

The local Docker workflow was validated on Windows using Docker Desktop with the Linux container backend.

Verify Docker is available:

```powershell
docker --version
docker info
docker compose version
```

The validated environment reported:

```text
Docker version 29.7.2
Docker Compose version v5.4.0
Docker Desktop Linux backend
WSL 2
```

Docker Desktop is responsible for providing the Linux container runtime. The application itself does not require a separate Python installation inside the container.

## Dockerfile

The build uses a lightweight Python base image:

```dockerfile
FROM python:3.14-slim

WORKDIR /app

COPY pyproject.toml .
COPY src ./src

RUN pip install --no-cache-dir .

EXPOSE 8000

CMD ["uvicorn", "iam_analyzer.api:app", "--host", "0.0.0.0", "--port", "8000"]
```

The important containerization decisions are:

- `python:3.14-slim` provides a smaller Python runtime image.
- `/app` is used as the container working directory.
- `pyproject.toml` and `src/` are copied into the image.
- `pip install --no-cache-dir .` installs the project and its declared runtime dependencies.
- `EXPOSE 8000` documents the application port.
- Uvicorn binds to `0.0.0.0` so the service is reachable through the published Docker port.

## Build the Docker Image

From the project root:

```powershell
docker build -t iam-access-analyzer:0.3.0 .
```

The successful build produced:

```text
iam-access-analyzer:0.3.0
```

Verify the image:

```powershell
docker images
```

Expected image entry:

```text
iam-access-analyzer:0.3.0
```

The validated local build reported approximately:

```text
Disk usage:    219 MB
Content size:   53.6 MB
```

These values are local Docker Desktop measurements and can vary between environments.

## Run the Container

Start the analyzer with:

```powershell
docker run --name iam-access-analyzer -p 8000:8000 iam-access-analyzer:0.3.0
```

The container starts Uvicorn and listens on:

```text
http://0.0.0.0:8000
```

The host can access the service through:

```text
http://localhost:8000
```

The terminal remains attached to the container logs while the process is running. This is expected behavior for `docker run` without detached mode.

## Verify Container Status

In another PowerShell terminal:

```powershell
docker ps
```

Expected state:

```text
STATUS: Up
PORTS: 0.0.0.0:8000->8000/tcp
```

Inspect the container state directly:

```powershell
docker inspect iam-access-analyzer --format "{{.State.Status}}"
```

Expected:

```text
running
```

## Docker Health Check

Validate the API through the published host port:

```powershell
Invoke-RestMethod http://localhost:8000/health
```

Expected response:

```text
status
------
ok
```

This confirms that traffic can travel from the Windows host through Docker's published port to the FastAPI application inside the container.

## Analyze Access from the Container

The same REST API can be exercised against the containerized service.

Example PowerShell request:

```powershell
$body = @{
    principal = @{
        id = "user:alice@example.com"
        type = "user"
    }
    resource = @{
        id = "bucket:prod-data"
        type = "storage_bucket"
    }
    action = @{
        name = "storage.objects.delete"
    }
    context = @{}
} | ConvertTo-Json -Depth 5

Invoke-RestMethod `
    -Uri http://localhost:8000/analyze-access `
    -Method Post `
    -ContentType "application/json" `
    -Body $body
```

Validated response:

```text
 effect reason                      risk_score privileged
 ------ ------                      ---------- ----------
 allow  Matching allow policy found         70      False
```

This demonstrates that the containerized service preserves the v0.3 authorization and security-analysis behavior.

## Privileged Access Detection in the Container

A privileged IAM action can also be tested through the containerized API.

Example:

```powershell
$body = @{
    principal = @{
        id = "user:alice@example.com"
        type = "user"
    }
    resource = @{
        id = "project:prod"
        type = "project"
    }
    action = @{
        name = "iam.roles.update"
    }
    context = @{}
} | ConvertTo-Json -Depth 5

Invoke-RestMethod `
    -Uri http://localhost:8000/analyze-access `
    -Method Post `
    -ContentType "application/json" `
    -Body $body
```

Validated response:

```text
 effect reason                      risk_score privileged
 ------ ------                      ---------- ----------
 allow  Matching allow policy found         70       True
```

The current privileged-action baseline specifically recognizes IAM-oriented privileged actions such as `iam.roles.update`. Ordinary resource operations such as `storage.objects.delete` can have a high risk score without being classified as privileged by the current privileged-action taxonomy.

## Docker Logs

Inspect application logs with:

```powershell
docker logs iam-access-analyzer
```

Validated logs included:

```text
Uvicorn running on http://0.0.0.0:8000
GET /health HTTP/1.1 200 OK
POST /analyze-access HTTP/1.1 200 OK
GET /docs HTTP/1.1 200 OK
GET /openapi.json HTTP/1.1 200 OK
```

The logs demonstrate successful application startup and successful HTTP requests through the container.

## Container Lifecycle

Stop the running container:

```powershell
docker stop iam-access-analyzer
```

Confirm that no containers are running:

```powershell
docker ps
```

The stopped container remains available:

```powershell
docker ps -a
```

A successful stop exits with code `0`.

Restart the existing container:

```powershell
docker start iam-access-analyzer
```

Verify it is running:

```powershell
docker ps
```

Re-test the API:

```powershell
Invoke-RestMethod http://localhost:8000/health
```

Expected:

```text
status
------
ok
```

This validates that the same container can be stopped and restarted without rebuilding the image.

## Docker Image Inspection

Verify the image tag:

```powershell
docker image inspect iam-access-analyzer:0.3.0 --format "{{.RepoTags}}"
```

Validated result:

```text
[iam-access-analyzer:0.3.0]
```

Verify the container working directory:

```powershell
docker inspect iam-access-analyzer --format "{{.Config.WorkingDir}}"
```

Validated result:

```text
/app
```

Verify the exposed application port:

```powershell
docker inspect iam-access-analyzer --format "{{.Config.ExposedPorts}}"
```

Validated result:

```text
map[8000/tcp:{}]
```

These inspection commands provide direct evidence of the image/container configuration rather than relying only on the application response.

## Docker Validation Summary

The v0.3 containerization build was validated end-to-end:

```text
Docker installed and available
        ✓

Docker image built successfully
        ✓

Image tagged iam-access-analyzer:0.3.0
        ✓

Container started successfully
        ✓

Port 8000 published to host
        ✓

/health returned status=ok
        ✓

/analyze-access returned authorization decision
        ✓

Risk score returned through containerized API
        ✓

Privileged access detection returned True for iam.roles.update
        ✓

Container logs recorded successful requests
        ✓

Container stopped with exit code 0
        ✓

Container restarted successfully
        ✓

Container configuration inspected
        ✓
```

The Docker image is therefore not only buildable but also operationally validated through the real HTTP interface.

---

# Future Roadmap

The project is intentionally developed as an incremental security-engineering exercise.

## v0.1 — Basic IAM Evaluator

```text
Basic IAM policy evaluator
        |
        v
Principal/resource/action modeling
        |
        v
ALLOW / DENY decisions
```

## v0.2 — Context-Aware Authorization + API

```text
Wildcard matching
        +
IAM-style conditions
        +
Policy expiration
        +
Explicit DENY precedence
        +
Deterministic testing
        |
        v
FastAPI REST endpoint
        +
Pydantic validation
        +
OpenAPI / Swagger documentation
```

## v0.3 — Security Analyzer

```text
Authorization
        +
Audit logging
        +
Risk scoring
        +
Privileged access detection
        |
        v
Security-aware AccessDecision
```

Completed v0.3 evidence:

```text
41 automated tests passing
Audit event model
Audit logger
Risk scoring engine
Privileged access detector
API security metadata
HLD + LLD architecture diagrams
```

## Future Security Enhancements

Potential next steps:

```text
Risk scoring based on resource sensitivity
Risk scoring based on principal type
Risk thresholds / severity levels
High-risk access alerts
Structured audit event persistence
JSON audit output
SIEM integration
Policy change auditing
Privileged access reporting
Access review reports
```

## Future IAM Modeling

Potential cloud IAM modeling:

```text
Identity policies
Resource policies
Role assumption
Groups and group membership
Permission boundaries
Service control policies
Organization policies
```

## Future Enterprise IAM Simulation

Potential enterprise capabilities:

```text
AWS IAM semantics
GCP IAM semantics
Policy inheritance
Organization constraints
Policy analysis/reporting
Access graph visualization
Authentication
API authorization
Policy-as-code workflows
```

---

# Portfolio Outcome

This project demonstrates practical Python implementation of an IAM authorization engine, security analyzer, and REST service.

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
Audit logging
+
Risk scoring
+
Privileged access detection
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
+
Security-oriented architecture
+
Docker containerization
```

The project demonstrates an incremental engineering progression:

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
        |
        v
API Build
FastAPI REST endpoint
+
Pydantic validation
+
OpenAPI / Swagger
        |
        v
v0.3
Security Analyzer
+
Audit logging
+
Risk scoring
+
Privileged access detection
+
Security-aware API responses
+
41 automated tests
        |
        v
Future
Enterprise IAM security analysis
```

---

# Current Build Evidence

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

Audit event model
        ✓

Audit logger
        ✓

Risk scoring
        ✓

Privileged access detection
        ✓

Security metadata in API response
        ✓

HLD architecture diagram
        ✓

LLD architecture diagram
        ✓

Docker image iam-access-analyzer:0.3.0
        ✓

Container runtime validation
        ✓

41 automated tests passing
        ✓
```

---

# Version

```text
IAM Access Analyzer
Version: 0.3.0
Status: Security Analyzer + Docker containerization build complete
```

The v0.3 objective is complete:

> Extend the IAM policy evaluator into a security analyzer by adding audit logging, risk scoring, and privileged access detection while preserving the existing authorization behavior and API functionality.

---

# Threat Model

v0.3 includes a lightweight threat model for the IAM Access Analyzer service. The objective is to identify realistic abuse cases around authorization decisions, security metadata, audit events, and the containerized API.

The threat model is intentionally scoped to the current portfolio implementation. It identifies the security boundaries and failure modes that would matter when evolving the analyzer toward an enterprise IAM security-analysis service.

## Threat Model Scope

```text
Client
  |
  | HTTP / JSON
  v
FastAPI API
  |
  | validated request
  v
AccessAnalyzer
  |
  +----> Policy matching
  +----> Conditions
  +----> Expiration
  +----> DENY precedence
  +----> Risk scoring
  +----> Privileged detection
  +----> Audit logging
  |
  v
AccessDecision
  |
  +----> Effect
  +----> Reason
  +----> Risk score
  +----> Privileged flag
```

The current Docker deployment adds an additional boundary:

```text
Windows Host
     |
     | localhost:8000
     v
Docker published port
     |
     v
Linux container
     |
     v
Uvicorn / FastAPI
     |
     v
IAM Access Analyzer
```

## Assets

The primary assets considered by the threat model are:

| Asset | Security Importance |
|---|---|
| Authorization decision | Determines whether requested access is allowed |
| IAM policy data | Defines authorization behavior |
| Principal identity | Determines who is requesting access |
| Resource identity | Determines what is being accessed |
| Request context | Can influence conditional authorization |
| Risk score | Security classification of an access request |
| Privileged flag | Identifies potentially security-sensitive operations |
| Audit events | Security observability and investigation evidence |
| API availability | Required for clients to obtain decisions |
| Container image | Runtime artifact containing the analyzer |
| Application configuration/code | Determines authorization semantics |

## Trust Boundaries

### Trust Boundary 1 — External Client to API

The HTTP client is outside the application trust boundary.

```text
UNTRUSTED / EXTERNAL
        |
        | HTTP JSON
        v
+-------------------+
| FastAPI API       |
| Pydantic boundary |
+-------------------+
```

Primary concern:

> Do not allow malformed or unexpected request data to directly enter the authorization engine.

The current implementation addresses this with Pydantic request validation.

### Trust Boundary 2 — API to Authorization Engine

The API converts validated request models into internal IAM domain objects.

```text
Pydantic models
       |
       v
Internal IAM models
       |
       v
AccessAnalyzer
```

This separation reduces coupling between transport-level input and authorization logic.

### Trust Boundary 3 — Host to Container

Docker provides process and filesystem isolation from the host application environment.

```text
Host
  |
  | published TCP port
  v
Container
  |
  v
FastAPI / Uvicorn
```

The current deployment is intended for local development and demonstration, not an internet-facing production deployment.

## STRIDE-Oriented Threat Analysis

### Spoofing

**Threat:** An attacker impersonates a legitimate principal in an access-analysis request.

**Example:**

```json
{
  "principal": {
    "id": "user:alice@example.com",
    "type": "user"
  }
}
```

A caller could claim to be Alice because the current API accepts the principal identity as request data.

**Current mitigation:**

- Pydantic validates the request structure.
- The analyzer evaluates the supplied principal against configured policy data.

**Important limitation:**

The API does not authenticate the caller or cryptographically establish that the caller is actually Alice.

**Risk:** High for production use.

**Future mitigation:**

- API authentication
- Identity-aware authorization
- mTLS or OAuth/OIDC
- Trusted identity propagation
- Caller-to-principal binding

---

### Tampering

**Threat:** A caller modifies principal, resource, action, or context values to influence the authorization result.

**Example attack:**

```text
Legitimate request:
environment=production

Tampered request:
environment=development
```

or changing the requested action to a less restricted operation.

**Current mitigation:**

- Pydantic validates the request schema.
- Conditions are evaluated by the analyzer.
- Explicit DENY takes precedence.
- Policy expiration is enforced.

**Risk:** Medium to High depending on deployment trust.

**Future mitigation:**

- Authenticate API callers.
- Authorize who can submit analysis requests.
- Treat trusted security context as server-derived rather than caller-supplied.
- Add request integrity controls where required.

---

### Repudiation

**Threat:** A caller denies having made an authorization request or an administrator cannot prove what decision was generated.

**Current mitigation:**

v0.3 creates an `AuditEvent` containing:

```text
timestamp
principal
resource
action
effect
reason
```

The analyzer records the event through `AuditLogger` when a logger is configured.

**Important limitation:**

The current logger is in-memory and is not a durable, centralized audit system.

**Risk:** Medium.

**Future mitigation:**

- Durable audit storage
- Centralized logging
- Immutable event storage
- Request/correlation IDs
- Authenticated caller identity
- SIEM integration

---

### Information Disclosure

**Threat:** The API exposes security-sensitive authorization information to an unauthorized caller.

Potentially useful information includes:

```text
effect
reason
risk_score
privileged
```

For example:

```json
{
  "effect": "allow",
  "reason": "Matching allow policy found",
  "risk_score": 70,
  "privileged": true
}
```

This metadata can reveal information about authorization policy behavior.

**Current mitigation:**

- API is designed for local/portfolio use.
- The implementation does not expose persistent policy-management endpoints.

**Risk:** Medium for local use; potentially High if exposed publicly.

**Future mitigation:**

- API authentication and authorization
- Response minimization
- Tenant isolation
- Rate limiting
- Structured security logging
- Avoid exposing policy internals unnecessarily

---

### Denial of Service

**Threat:** A caller sends excessive or expensive requests to exhaust application resources.

Potential attack surface:

```text
HTTP request volume
       |
       v
Pydantic validation
       |
       v
Policy evaluation
       |
       v
Audit event creation
```

**Current mitigation:**

The analyzer performs deterministic in-process evaluation and has no external database dependency in v0.3.

**Risk:** Low for local development; Medium or High for internet-facing deployment.

**Future mitigation:**

- Rate limiting
- Authentication
- Request size limits
- Concurrency controls
- Container resource limits
- Reverse proxy / API gateway
- Observability and alerting

---

### Elevation of Privilege

**Threat:** A caller manipulates a request or policy relationship to obtain access to a privileged operation.

A particularly important example is:

```text
iam.roles.update
```

The current analyzer classifies this action as privileged:

```text
privileged = True
```

The authorization decision remains separate from the privileged classification.

**Current mitigation:**

- Explicit DENY precedence
- Principal matching
- Resource matching
- Action matching
- Condition evaluation
- Policy expiration
- Privileged-action detection
- Risk scoring

**Risk:** High if policy data or principal identity can be manipulated.

**Future mitigation:**

- Strong caller authentication
- Policy administration controls
- Complete privileged-action taxonomy
- Privileged access approval workflows
- Separation of duties
- Policy change auditing

---

## Threat Summary

| Threat | Example | Current Control | Residual Risk |
|---|---|---|---|
| Spoofing | Claim to be another principal | Request validation only | High |
| Tampering | Modify action/context | Policy evaluation + validation | Medium/High |
| Repudiation | Deny having requested access | In-memory audit event | Medium |
| Information disclosure | Learn authorization metadata | Local deployment scope | Medium |
| Denial of service | Flood API | Lightweight synchronous processing | Medium |
| Elevation of privilege | Request IAM administrative action | DENY precedence + privileged detection | High |

The most important production gap is **caller authentication and authorization**. The analyzer currently evaluates the identity presented in the request; it does not independently establish that identity.

---

# Security Abuse Cases Demonstrated

The final gate demonstrates three representative authorization/security outcomes.

## Abuse Case 1 — Ordinary Access

Request:

```text
Principal:
user:alice@example.com

Resource:
bucket:prod-data

Action:
storage.objects.get
```

Observed result:

```text
effect       = allow
risk_score   = 10
privileged   = False
```

This demonstrates a normal low-risk resource read.

## Abuse Case 2 — Privileged IAM Access

Request:

```text
Principal:
user:alice@example.com

Resource:
project:prod

Action:
iam.roles.update
```

Observed result:

```text
effect       = allow
risk_score   = 70
privileged   = True
```

This demonstrates that an access request can be authorized while simultaneously being identified as privileged and high-risk.

This distinction is important:

> Authorization success does not mean that the access is low-risk.

The analyzer deliberately returns both dimensions.

## Abuse Case 3 — Unauthorized Principal

Request:

```text
Principal:
user:bob@example.com

Resource:
bucket:prod-data

Action:
storage.objects.get
```

Observed result:

```text
effect       = deny
reason       = No matching policy found
risk_score   = 10
privileged   = False
```

This demonstrates default-deny behavior for a principal without a matching policy.

---

# Gate Demo Evidence

The gate deliverable requires:

```text
Threat model
+
Demo evidence
```

The repository contains screenshot evidence under:

```text
docs/
└── demo/
    ├── 01-health-check.png
    ├── 02-normal-access-allowed.png
    ├── 03-privileged-access-detected.png
    ├── 04-denied-access.png
    ├── 05-test-suite.png
    └── 06-docker-runtime.png
```

These screenshots are intended to make the final architecture/security gate independently reviewable without requiring the reviewer to reproduce the complete local environment.

## Evidence 01 — Health Check

![Dockerized API health check](docs/demo/01-health-check.png)

The health check demonstrates that the containerized FastAPI service is reachable through the published host port.

Validated endpoint:

```text
GET http://localhost:8000/health
```

Expected:

```text
status
------
ok
```

## Evidence 02 — Normal Access Allowed

![Normal access allowed](docs/demo/02-normal-access-allowed.png)

Request:

```text
user:alice@example.com
        |
        v
bucket:prod-data
        |
        v
storage.objects.get
```

Observed:

```text
effect       allow
risk_score   10
privileged   False
```

This demonstrates normal authorized resource access.

## Evidence 03 — Privileged Access Detected

![Privileged access detected](docs/demo/03-privileged-access-detected.png)

Request:

```text
user:alice@example.com
        |
        v
project:prod
        |
        v
iam.roles.update
```

Observed:

```text
effect       allow
risk_score   70
privileged   True
```

This is the primary security-analysis demonstration.

The system distinguishes:

```text
Authorization:
ALLOW

Security classification:
PRIVILEGED

Risk:
70
```

## Evidence 04 — Denied Access

![Denied access](docs/demo/04-denied-access.png)

Request:

```text
user:bob@example.com
        |
        v
bucket:prod-data
        |
        v
storage.objects.get
```

Observed:

```text
effect       deny
reason       No matching policy found
```

This demonstrates that the analyzer does not grant access merely because the action itself is valid.

## Evidence 05 — Full Test Suite

![Full pytest suite](docs/demo/05-test-suite.png)

The final regression suite was executed before the gate demonstration.

Observed:

```text
41 passed
1 warning
0 failed
```

The warning is a dependency deprecation warning from the FastAPI/Starlette test-client stack and does not represent an application test failure.

## Evidence 06 — Docker Runtime

![Docker runtime validation](docs/demo/06-docker-runtime.png)

The runtime evidence demonstrates:

```text
Container:
iam-access-analyzer

Image:
iam-access-analyzer:0.3.0

Status:
running

Published port:
8000 -> 8000
```

Additional validation included:

```text
docker inspect iam-access-analyzer
docker image inspect iam-access-analyzer:0.3.0
docker logs iam-access-analyzer
```

The container was also stopped and restarted successfully.

---

# Gate Demonstration Walkthrough

The recommended demonstration sequence is:

```text
1. Show architecture / threat model
             |
             v
2. Show Docker container running
             |
             v
3. GET /health
             |
             v
4. Normal read access
             |
             v
5. Privileged IAM action
             |
             v
6. Unauthorized principal
             |
             v
7. Show pytest = 41 passed
             |
             v
8. Explain security boundaries + limitations
```

## Step 1 — Show the Architecture

Start with the HLD:

```text
Client
  |
  v
FastAPI
  |
  v
AccessAnalyzer
  |
  +--> Authorization
  +--> Risk Scoring
  +--> Privileged Detection
  +--> Audit Logging
  |
  v
AccessDecision
```

Then explain that the Docker container provides the runtime boundary around the API and analyzer.

## Step 2 — Show the Container

Run:

```powershell
docker ps
```

Point out:

```text
iam-access-analyzer:0.3.0
0.0.0.0:8000->8000/tcp
```

## Step 3 — Demonstrate Health

Run:

```powershell
Invoke-RestMethod http://localhost:8000/health
```

Expected:

```text
status
------
ok
```

## Step 4 — Demonstrate Normal Access

Use:

```text
storage.objects.get
```

Expected:

```text
allow
risk_score = 10
privileged = False
```

Explain:

> This is a normal authorized resource read and is classified as low risk by the current baseline scoring model.

## Step 5 — Demonstrate Privileged Access

Use:

```text
iam.roles.update
```

Expected:

```text
allow
risk_score = 70
privileged = True
```

Explain:

> The analyzer does not treat authorization and security classification as the same thing. An action can be allowed while still being identified as privileged and high-risk.

## Step 6 — Demonstrate Denial

Use:

```text
user:bob@example.com
```

against:

```text
bucket:prod-data
storage.objects.get
```

Expected:

```text
deny
No matching policy found
```

Explain:

> The analyzer follows default-deny behavior when no applicable policy matches the request.

## Step 7 — Show Regression Evidence

Run:

```powershell
pytest
```

Expected:

```text
41 passed
1 warning
0 failed
```

## Step 8 — Explain the Main Production Gaps

The most important limitations to call out during the gate are:

```text
No API authentication
No API authorization
No persistent policy store
In-memory audit logging
Limited privileged-action taxonomy
Simplified IAM semantics
No centralized SIEM integration
```

These are known limitations rather than hidden risks.

---

# Threat Model Conclusions

The v0.3 analyzer demonstrates the core security-engineering pattern:

```text
Authorization
      +
Security Classification
      +
Auditability
      +
Risk Awareness
      +
Containerized Runtime
```

The strongest architectural property is the separation between:

```text
"Is access allowed?"
```

and:

```text
"How security-sensitive is this access?"
```

This allows the analyzer to produce a richer decision:

```text
ALLOW
+
Risk Score
+
Privileged Classification
+
Audit Event
```

The most significant threat-model finding is that the current API trusts the principal identity supplied by the request. Therefore, the current implementation should be treated as a **policy-analysis engine**, not as a production identity enforcement point.

A production evolution would place authenticated identity and policy-management controls around the analyzer:

```text
Identity Provider
       |
       v
API Gateway / Auth Layer
       |
       v
IAM Access Analyzer
       |
       +----> Policy Store
       |
       +----> Audit / SIEM
       |
       +----> Risk Engine
       |
       v
Security Decision
```

This provides a clear architectural path from the current portfolio implementation toward an enterprise IAM security-analysis service.

---

# Final Gate Evidence Matrix

| Gate Requirement | Evidence | Location |
|---|---|---|
| Threat model | STRIDE-oriented threat analysis | `docs/threat-model.md` |
| Architecture | HLD | `docs/architecture/iam-access-analyzer-hld.png` |
| Architecture | LLD | `docs/architecture/iam-access-analyzer-lld.png` |
| Working service | Health check | `docs/demo/01-health-check.png` |
| Normal access | Authorized read | `docs/demo/02-normal-access-allowed.png` |
| Privileged access | IAM role update detection | `docs/demo/03-privileged-access-detected.png` |
| Denial | Default deny | `docs/demo/04-denied-access.png` |
| Regression safety | 41 tests passing | `docs/demo/05-test-suite.png` |
| Container runtime | Docker image/container | `docs/demo/06-docker-runtime.png` |
| Docker artifact | `iam-access-analyzer:0.3.0` | Local Docker image |
| Source implementation | Analyzer + security modules | `src/iam_analyzer/` |

---

# Gate Completion Status

```text
Threat model
        ✓

STRIDE-oriented threat analysis
        ✓

Security boundaries documented
        ✓

Abuse cases documented
        ✓

HLD architecture
        ✓

LLD architecture
        ✓

Docker image
        ✓

Container runtime
        ✓

Health check
        ✓

Normal access demo
        ✓

Privileged access demo
        ✓

Denied access demo
        ✓

41 automated tests
        ✓

Screenshot evidence
        ✓
```

The IAM Access Analyzer v0.3 security-analysis build is therefore supported by both **design evidence** and **runtime evidence**.

---

# Version

```text
IAM Access Analyzer
Version: 0.3.0
Gate: Threat Model + Demo
Status: Security Analyzer + Docker containerization + threat-model evidence complete
```

The final gate objective is:

> Threat-model the IAM Access Analyzer, demonstrate its authorization and security-analysis behavior through the containerized API, and provide reproducible architecture and runtime evidence.
