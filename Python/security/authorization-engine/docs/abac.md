# Attribute-Based Access Control (ABAC)

## Overview

This document covers the ABAC implementation in the `authorization-engine` project.

**Lab focus:** Authorization  
**Task:** Implement ABAC using resource, user, and context attributes  
**Deliverable:** ABAC tests

---

# 1. What is ABAC?

**Attribute-Based Access Control (ABAC)** is an authorization model where access decisions are made by evaluating attributes of:

- the user/subject making the request
- the resource being accessed
- the requested action
- the environment/context in which the request occurs

Instead of saying:

> "Alice has the Developer role, therefore Alice can read reports."

ABAC can say:

> "Allow Alice to read the report because Alice's department matches the report's department and the request comes from the corporate network."

### Basic model

```text
                 Access Request
                       |
        +--------------+--------------+
        |              |              |
        v              v              v
      User          Resource        Context
   attributes      attributes      attributes
        |              |              |
        +--------------+--------------+
                       |
                       v
                  ABAC Policy
                       |
                       v
                 Policy Evaluation
                       |
                 +-----+-----+
                 |           |
                 v           v
               ALLOW       DENY
```

ABAC is therefore **attribute-driven authorization**.

---

# 2. RBAC vs ABAC

## RBAC

**Role-Based Access Control** grants permissions through roles.

```text
Alice
  |
  v
Developer
  |
  +-- reports:read
  +-- reports:write
```

The decision primarily depends on role membership and role permissions.

## ABAC

ABAC evaluates attributes.

```text
Alice
department = engineering
        |
        +------------------+
                           |
Report                     v
department = engineering -> Policy
                           ^
                           |
Corporate network ---------+
                           |
                           v
                         ALLOW
```

## Comparison

| Feature | RBAC | ABAC |
|---|---|---|
| Primary decision input | Roles | Attributes |
| User permissions | Through roles | Through policy conditions |
| Resource attributes | Usually not central | First-class input |
| Context awareness | Limited | Strong |
| Example | `developer` can `reports:read` | Engineering users can read engineering reports |
| Policy complexity | Lower | Higher |
| Flexibility | Moderate | High |
| Best suited for | Stable organizational permissions | Dynamic/context-aware access |

### Simple rule of thumb

```text
RBAC:
"WHO are you?"

ABAC:
"WHO are you + WHAT are you accessing + WHAT are you doing + UNDER WHAT CONDITIONS?"
```

RBAC and ABAC are not mutually exclusive. Enterprise authorization systems can combine them.

---

# 3. ABAC Components

ABAC evaluates multiple inputs.

```text
             ABAC Request
                  |
      +-----------+-----------+
      |           |           |
      v           v           v
    Subject     Resource    Environment
      |           |           |
      v           v           v
  Attributes  Attributes  Attributes
      \           |           /
       \          |          /
        +---------+---------+
                  |
                  v
                Policy
                  |
                  v
              Decision
```

## 3.1 Subject / User Attributes

The subject is the entity requesting access.

Examples:

```text
id = alice
department = engineering
clearance = high
employment_type = employee
```

In this implementation:

```python
User(
    id="alice",
    attributes={
        "department": "engineering",
        "clearance": "high",
    },
)
```

The important point is that the user identity and the user's authorization attributes are represented separately.

---

## 3.2 Resource Attributes

The resource is the object the user wants to access.

Examples:

```text
id = report-123
department = engineering
classification = confidential
owner = alice
```

Our implementation represents this as:

```python
Resource(
    id="report-123",
    attributes={
        "department": "engineering",
        "classification": "confidential",
    },
)
```

Resource attributes allow policies to make decisions based on the properties of the target resource.

---

## 3.3 Action

The action describes what the subject wants to do.

Examples:

```text
read
write
delete
approve
download
```

Our request contains:

```python
ABACRequest(
    user=user,
    resource=resource,
    action="read",
    context=context,
)
```

The action is important because access to a resource is not necessarily all-or-nothing.

For example:

```text
Alice may READ a report
Alice may NOT DELETE the report
```

---

## 3.4 Environment / Context Attributes

Context describes the circumstances surrounding the request.

Examples:

```text
network = corporate
location = office
device_trusted = true
time = business_hours
risk_score = low
```

Our implementation uses:

```python
AccessContext(
    attributes={
        "network": "corporate",
        "location": "office",
    },
)
```

This allows decisions to change based on the request environment.

For example:

```text
Corporate network -> ALLOW
Public network    -> DENY
```

even when the user and resource are unchanged.

---

# 4. Policy Evaluation

A policy defines the conditions that must be satisfied.

Our v0.1 policy is:

```text
ALLOW READ when:

user.department == resource.department

AND

context.network == "corporate"
```

### Evaluation flow

```text
                 Request
                    |
                    v
          Is action "read"?
             /          \
           NO            YES
           |              |
         DENY             v
                 Does user.department
                 equal resource.department?
                    /           \
                  NO             YES
                  |                |
                DENY               v
                         Is network "corporate"?
                            /           \
                          NO             YES
                          |                |
                        DENY             ALLOW
```

The engine evaluates the conditions sequentially.

---

# 5. ALLOW / DENY Flow

## Successful request

```text
User
department = engineering
       |
       |
Resource
department = engineering
       |
       |
Context
network = corporate
       |
       v
+---------------------------+
|       ABAC Policy         |
|                           |
| user.dept == resource.dept|
| AND                       |
| network == corporate      |
+---------------------------+
             |
             v
           ALLOW
```

## Department mismatch

```text
User.department     = engineering
Resource.department = finance
                       |
                       v
              Condition fails
                       |
                       v
                     DENY
```

## Context mismatch

```text
User.department     = engineering
Resource.department = engineering
Context.network     = public
                       |
                       v
              Condition fails
                       |
                       v
                     DENY
```

---

# 6. Our Implementation

The ABAC implementation is intentionally small and focused on the v0.1 lab requirement.

```text
src/
└── authorization_engine/
    ├── __init__.py
    ├── engine.py
    ├── models.py
    ├── abac_models.py
    └── abac_engine.py

tests/
├── test_rbac.py
└── test_abac.py
```

### ABAC-specific files

```text
abac_models.py
    |
    +-- User
    +-- Resource
    +-- AccessContext
    +-- ABACRequest
    +-- ABACDecision

abac_engine.py
    |
    +-- ABACEngine
          |
          +-- authorize()
```

---

# 7. Architecture

The current architecture separates the existing RBAC implementation from the ABAC implementation.

```text
                    Authorization Engine
                           |
             +-------------+-------------+
             |                           |
             v                           v
            RBAC                        ABAC
             |                           |
        engine.py                  abac_engine.py
        models.py                  abac_models.py
             |                           |
             v                           v
       Role/Permission          User/Resource/Context
             |                           |
             +-------------+-------------+
                           |
                           v
                    Authorization
                      Decision
                    ALLOW / DENY
```

For the current lab, ABAC is implemented as a separate module so that the original RBAC behavior remains intact.

---

# 8. Code Walkthrough

## 8.1 User model

```python
@dataclass(frozen=True)
class User:
    id: str
    attributes: dict[str, Any]
```

Example:

```python
alice = User(
    id="alice",
    attributes={
        "department": "engineering",
    },
)
```

---

## 8.2 Resource model

```python
@dataclass(frozen=True)
class Resource:
    id: str
    attributes: dict[str, Any]
```

Example:

```python
report = Resource(
    id="report-123",
    attributes={
        "department": "engineering",
    },
)
```

---

## 8.3 Context model

```python
@dataclass(frozen=True)
class AccessContext:
    attributes: dict[str, Any]
```

Example:

```python
context = AccessContext(
    attributes={
        "network": "corporate",
    },
)
```

---

## 8.4 Request model

```python
@dataclass(frozen=True)
class ABACRequest:
    user: User
    resource: Resource
    action: str
    context: AccessContext
```

This combines the authorization inputs.

```text
WHO?       -> user
WHAT?      -> resource
DO WHAT?   -> action
UNDER WHAT CONDITIONS? -> context
```

---

## 8.5 Decision model

```python
@dataclass(frozen=True)
class ABACDecision:
    allowed: bool
    reason: str
```

Instead of returning only a boolean, the engine provides a reason.

Example:

```text
allowed = True
reason = "department matches and request is from corporate network"
```

or:

```text
allowed = False
reason = "user department does not match resource department"
```

This makes authorization behavior easier to test, debug, and audit.

---

## 8.6 ABAC engine

The engine receives an `ABACRequest`:

```python
def authorize(self, request: ABACRequest) -> ABACDecision:
```

It extracts the relevant attributes:

```python
user_department = request.user.attributes.get("department")
resource_department = request.resource.attributes.get("department")
network = request.context.attributes.get("network")
```

Then it evaluates:

```text
1. Is action "read"?
2. Does user department match resource department?
3. Is network corporate?
4. Return ALLOW or DENY.
```

The policy can be represented logically as:

```text
ALLOW =
    action == "read"
    AND user.department == resource.department
    AND context.network == "corporate"
```

---

# 9. Test Scenarios

The ABAC deliverable is `tests/test_abac.py`.

The test suite contains seven scenarios.

## Test 1 — Matching attributes

```text
User department     = engineering
Resource department = engineering
Network             = corporate

Expected: ALLOW
```

Result:

```text
PASS
```

---

## Test 2 — Department mismatch

```text
User department     = engineering
Resource department = finance
Network             = corporate

Expected: DENY
```

Result:

```text
PASS
```

---

## Test 3 — Non-corporate network

```text
User department     = engineering
Resource department = engineering
Network             = public

Expected: DENY
```

Result:

```text
PASS
```

---

## Test 4 — Unsupported action

```text
User department     = engineering
Resource department = engineering
Network             = corporate
Action              = delete

Expected: DENY
```

The v0.1 policy supports `read` only.

Result:

```text
PASS
```

---

## Test 5 — Missing user attribute

```text
User:
    department = missing

Resource:
    department = engineering

Network:
    corporate

Expected: DENY
```

Result:

```text
PASS
```

---

## Test 6 — Missing resource attribute

```text
User:
    department = engineering

Resource:
    department = missing

Network:
    corporate

Expected: DENY
```

Result:

```text
PASS
```

---

## Test 7 — Missing context attribute

```text
User:
    department = engineering

Resource:
    department = engineering

Context:
    network = missing

Expected: DENY
```

Result:

```text
PASS
```

---

# 10. Test Evidence

The ABAC-specific test run:

```text
pytest tests/test_abac.py
```

produced:

```text
collected 7 items

tests\test_abac.py ....... [100%]

7 passed
```

The complete regression suite:

```text
pytest
```

produced:

```text
collected 16 items

tests\test_abac.py ....... [ 43%]
tests\test_rbac.py ....... [100%]

16 passed
```

This demonstrates:

```text
ABAC tests
    7 passed
       +
RBAC tests
    9 passed
       =
Regression suite
   16 passed
```

Therefore, adding the ABAC implementation did not break the existing RBAC implementation.

---

# 11. Fail-Closed Behavior

A security-critical property of the implementation is **fail-closed authorization**.

Fail closed means:

> If the engine cannot establish that the policy conditions are satisfied, access is denied.

For example:

```text
Missing user.department
          |
          v
Condition cannot be satisfied
          |
          v
        DENY
```

Likewise:

```text
Missing resource.department
          |
          v
Condition cannot be satisfied
          |
          v
        DENY
```

And:

```text
Missing context.network
          |
          v
network != "corporate"
          |
          v
        DENY
```

This is safer than treating missing security attributes as implicitly trusted.

---

# 12. Real-World Scenarios

## Scenario 1 — Corporate reports

An organization wants employees to access reports belonging to their department.

Policy:

```text
user.department == resource.department
```

Example:

```text
Engineering user -> Engineering report -> ALLOW
Engineering user -> Finance report     -> DENY
```

---

## Scenario 2 — Corporate network restriction

An organization only allows sensitive application access from trusted corporate networks.

Policy:

```text
context.network == "corporate"
```

Example:

```text
Corporate network -> ALLOW
Public Wi-Fi      -> DENY
```

---

## Scenario 3 — Data classification

A more advanced ABAC policy might be:

```text
user.clearance >= resource.required_clearance
```

Example:

```text
User clearance       = 3
Resource requirement = 2

3 >= 2
   |
   v
ALLOW
```

But:

```text
User clearance       = 1
Resource requirement = 3

1 >= 3
   |
   v
DENY
```

---

## Scenario 4 — Business hours

A policy could use context:

```text
context.time between 09:00 and 18:00
```

This could produce:

```text
Employee + sensitive resource + business hours
                     |
                     v
                   ALLOW
```

while:

```text
Employee + sensitive resource + 02:00 AM
                     |
                     v
                   DENY
```

---

## Scenario 5 — Trusted device

An organization might require:

```text
context.device_trusted == true
```

A request could therefore depend on:

```text
User attributes
+
Resource attributes
+
Device attributes
+
Network attributes
```

This demonstrates why ABAC is useful for **context-aware authorization**.

---

# 13. Security Considerations

## 13.1 Attribute integrity

ABAC is only as trustworthy as its attributes.

If an attacker can change:

```text
department = engineering
```

to:

```text
department = finance
```

they may influence authorization decisions.

Therefore, security-sensitive attributes should come from trusted sources.

---

## 13.2 Fail closed

Missing or invalid attributes should not silently result in ALLOW.

```text
Unknown
  |
  v
DENY
```

is safer than:

```text
Unknown
  |
  v
ALLOW
```

---

## 13.3 Policy correctness

ABAC policies can become complex.

A policy such as:

```text
A AND B AND (C OR D) AND NOT E
```

must be carefully reviewed and tested.

---

## 13.4 Attribute freshness

Some attributes change over time.

Examples:

```text
employment_status
device_trust
risk_score
location
```

Stale attributes can lead to incorrect authorization decisions.

---

## 13.5 Policy testing

Every security-sensitive policy should have positive and negative tests.

At minimum:

```text
Expected ALLOW
Expected DENY
Missing attribute
Invalid attribute
Boundary condition
Unsupported action
```

---

## 13.6 Auditability

Authorization decisions should eventually produce audit records such as:

```text
user = alice
resource = report-123
action = read
decision = allow
reason = department match + corporate network
```

The current v0.1 implementation exposes a reason through `ABACDecision`, which provides a foundation for future audit logging.

---

# 14. ABAC Limitations

ABAC is powerful, but it introduces complexity.

## Policy complexity

As the number of attributes and rules grows, policies can become difficult to understand.

```text
Few rules
   |
   v
Simple

Many attributes
+
Many conditions
+
Exceptions
   |
   v
Complex policy
```

## Attribute management

The system must know:

- where attributes come from
- who is allowed to change them
- how they are validated
- how fresh they are
- what happens when they are unavailable

## Debugging

A DENY decision may result from many conditions.

For example:

```text
User department       ✓
Resource department   ✓
Network               ✗
Device trust          ?
Time                  ✓
Risk score             ✗
```

A good authorization system therefore needs explainability and auditability.

## Policy distribution

In a distributed enterprise, policy evaluation may happen across many services.

Keeping policies consistent becomes an architectural concern.

---

# 15. Future Improvements

The current implementation is intentionally **ABAC v0.1**.

Possible future versions could introduce:

## v0.2 — Multiple actions

Support:

```text
read
write
delete
approve
download
```

---

## v0.3 — Generic policy conditions

Instead of hard-coding:

```python
user_department != resource_department
```

introduce reusable conditions:

```text
equals
not_equals
greater_than
less_than
in
contains
```

---

## v0.4 — Policy objects

Represent policies explicitly:

```text
Policy
├── effect
├── action
├── conditions
└── priority
```

---

## v0.5 — Combined authorization

Eventually the authorization engine could support:

```text
              Authorization Engine
                       |
        +--------------+--------------+
        |              |              |
        v              v              v
       RBAC           ABAC           ReBAC
        |              |              |
        v              v              v
     Roles        Attributes      Relationships
        \              |              /
         \             |             /
          +------------+------------+
                       |
                       v
                  Authorization
                    Decision
```

**ReBAC is a separate authorization model and a separate lab.** It is not part of this ABAC implementation.

---

# 16. Interview Questions

## Q1. What is ABAC?

ABAC is an authorization model that evaluates attributes of the subject, resource, action, and environment/context to make an access decision.

## Q2. How is ABAC different from RBAC?

RBAC grants permissions through roles.

ABAC evaluates policy conditions against attributes.

```text
RBAC:
User -> Role -> Permission

ABAC:
User + Resource + Action + Context -> Policy -> Decision
```

## Q3. Why is ABAC more flexible than RBAC?

Because policies can consider dynamic properties such as:

```text
department
classification
location
network
device trust
time
risk
clearance
```

## Q4. What is a context attribute?

A context attribute describes the environment surrounding the request.

Examples:

```text
network
location
time
device trust
risk score
```

## Q5. Why should ABAC fail closed?

Because missing or invalid attributes must not accidentally grant access.

If the policy cannot establish that access is permitted:

```text
DENY
```

## Q6. Can RBAC and ABAC be combined?

Yes.

A system can first require a role and then apply attribute-based restrictions.

Example:

```text
User must be Developer
        AND
User department must match resource department
        AND
Request must come from corporate network
```

## Q7. What are the disadvantages of ABAC?

The main challenges are:

- policy complexity
- attribute management
- attribute freshness
- policy debugging
- policy distribution
- testing complexity

## Q8. What happens if an ABAC attribute is missing?

A secure implementation should normally fail closed unless the policy explicitly defines another behavior.

## Q9. Why do we separate User, Resource and Context?

Because they represent different authorization dimensions:

```text
User     -> WHO
Resource -> WHAT
Action   -> DO WHAT
Context  -> UNDER WHAT CONDITIONS
```

## Q10. Is ABAC an authentication mechanism?

No.

Authentication answers:

```text
"Who are you?"
```

Authorization answers:

```text
"Are you allowed to perform this action?"
```

ABAC is an **authorization model**, not an authentication protocol.

---

# 17. Quick Reference

```text
ABAC
 |
 +-- Subject/User attributes
 |
 +-- Resource attributes
 |
 +-- Action
 |
 +-- Environment/Context attributes
 |
 +-- Policy
 |
 +-- Evaluation
 |
 +-- ALLOW / DENY
```

### v0.1 policy

```text
ALLOW if:

action == "read"

AND

user.department == resource.department

AND

context.network == "corporate"
```

### Current evidence

```text
ABAC tests = 7 passed
RBAC tests = 9 passed
Total      = 16 passed
```

### Key mental model

```text
                 WHO?
                  |
                  v
               User
                  |
                  |
WHAT? --------> Resource
                  |
                  |
DO WHAT? ------> Action
                  |
                  |
UNDER WHAT
CONDITIONS? ---> Context
                  |
                  v
                Policy
                  |
                  v
             ALLOW / DENY
```

---

# Conclusion

The ABAC v0.1 implementation demonstrates how authorization can move beyond static role membership and make decisions using **user, resource, action, and context attributes**.

The implementation intentionally remains small:

```text
User
Resource
Context
   +
Action
   |
   v
ABAC Policy
   |
   v
ABACEngine
   |
   v
ABACDecision
```

The implementation is validated by automated tests:

```text
7 ABAC tests passed
9 existing RBAC tests passed
16 total tests passed
```

This establishes the foundation for more advanced policy evaluation while keeping **ReBAC as a separate future lab**.
