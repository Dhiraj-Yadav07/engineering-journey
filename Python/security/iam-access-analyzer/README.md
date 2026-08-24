# IAM Access Analyzer — Policy Evaluator v0.2

A Python-based IAM policy evaluation engine that models principals, resources, actions, policies, contextual conditions, wildcard actions, policy expiration, and explicit deny precedence.

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
│       ├── analyzer.py
│       ├── conditions.py
│       ├── expiration.py
│       ├── matching.py
│       └── models.py
│
└── tests/
    └── test_analyzer.py
```

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

The project uses `pytest`.

Run:

```powershell
pytest
```

Current test evidence:

```text
23 tests collected
23 passed
0 failed
```

Test categories include:

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

Install the package:

```powershell
python -m pip install -e .
```

Install pytest:

```powershell
python -m pip install pytest
```

Run tests:

```powershell
pytest
```

---

# Python Environment

Developed and tested with:

```text
Python 3.14.7
pytest 9.1.1
```

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

## v0.3

Potential enhancements:

```text
JSON policy parser
Multiple condition operators
CIDR/IP conditions
Resource wildcard matching
Multiple principals
Policy collections
Structured decision reasons
```

## v0.4

Potential cloud IAM modeling:

```text
Identity policies
Resource policies
Role assumption
Groups
Permission boundaries
```

## v0.5

Potential enterprise IAM simulation:

```text
AWS IAM semantics
GCP IAM semantics
Policy inheritance
Organization constraints
Policy analysis/reporting
Access graph visualization
```

---

# Portfolio Outcome

This project demonstrates practical Python implementation of an IAM authorization engine.

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
23 automated tests
        |
        v
Future
Enterprise IAM policy simulation
```
