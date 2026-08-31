# Authorization Engine — RBAC v0.1

A lightweight Python authorization engine implementing **Role-Based Access Control (RBAC)**.

This project is part of the IAM / Security engineering journey and focuses specifically on the **authorization** layer.

---

## 1. Project Goal

The goal of RBAC Engine v0.1 is to implement the fundamental authorization relationship:

```text
Subject
   |
   | assigned
   v
 Role
   |
   | grants
   v
Permission
   |
   | evaluated against
   v
Authorization Request
   |
   v
ALLOW / DENY
```

The engine answers:

> **Can this subject perform this action on this resource?**

Example:

```text
Alice
  |
  v
Developer
  |
  +---- reports:read
  +---- reports:write
```

Therefore:

```text
Alice -> reports:read  -> ALLOW
Alice -> reports:write -> ALLOW
Alice -> reports:delete -> DENY
```

---

# 2. Why RBAC?

Without RBAC, permissions can become difficult to manage when assigned individually to users.

For example:

```text
Alice   -> reports:read
Alice   -> reports:write
Bob     -> reports:read
Charlie -> reports:read
Charlie -> reports:write
Charlie -> reports:delete
```

RBAC introduces reusable roles:

```text
Viewer
└── reports:read

Developer
├── reports:read
└── reports:write

Admin
├── reports:read
├── reports:write
└── reports:delete
```

Users are then assigned roles:

```text
Alice   -> Viewer
Bob     -> Developer
Charlie -> Admin
```

This separates **who receives access** from **what permissions a role provides**.

---

# 3. Core Authorization Model

The v0.1 model is:

```text
Subject → Role → Permission
```

A permission consists of:

```text
(resource, action)
```

For example:

```text
("reports", "read")
```

Conceptually:

```text
reports:read
```

A role contains a set of permissions.

Example:

```text
Developer
├── reports:read
└── reports:write
```

---

# 4. Architecture

The authorization engine maintains two important relationships:

```text
                    AuthorizationEngine
                            |
              +-------------+-------------+
              |                           |
              v                           v
        Role Registry             Subject → Roles
              |                           |
              v                           v
        Developer                    Alice
              |                           |
              v                    +------+------+
        Permissions                 |             |
              |                     v             v
              +--------------> Developer      Auditor
```

Authorization flow:

```text
                 Authorization Request
                          |
                          v
                  +---------------+
                  |    Subject    |
                  |     Alice     |
                  +---------------+
                          |
                          v
                  Resolve Roles
                          |
                          v
              +-----------------------+
              | Developer / Auditor   |
              +-----------------------+
                          |
                          v
               Requested Permission
                          |
                          v
                Permission Matching
                     /          \
                   YES           NO
                    |             |
                    v             v
                  ALLOW        Check next role
                                  |
                                  v
                         No role matches
                                  |
                                  v
                                DENY
```

---

# 5. Default Deny

The engine follows a **default-deny** security model.

If no assigned role explicitly grants a permission:

```text
DENY
```

Example:

```text
Alice
  |
  v
Developer
  |
  +---- reports:read
  +---- reports:write
```

Request:

```text
Alice -> reports:delete
```

Evaluation:

```text
reports:delete
      |
      v
Developer permissions
      |
      +---- reports:read
      +---- reports:write
      |
      v
No match
      |
      v
DENY
```

The engine does not infer permissions.

For example:

```text
reports:write
```

does not automatically imply:

```text
reports:delete
```

---

# 6. Project Structure

```text
authorization-engine/
│
├── docs/
│   └── rbac.md
│
├── src/
│   └── authorization_engine/
│       ├── __init__.py
│       ├── models.py
│       └── engine.py
│
├── tests/
│   └── test_rbac.py
│
└── pyproject.toml
```

## Components

### `models.py`

Defines the core authorization domain objects:

```text
Permission
Role
Decision
AuthorizationDecision
```

### `engine.py`

Contains the RBAC authorization logic:

```text
AuthorizationEngine
```

Responsibilities include:

- registering roles
- assigning roles to subjects
- evaluating authorization requests
- returning ALLOW / DENY decisions

### `tests/test_rbac.py`

Contains automated tests covering the core RBAC behavior.

### `docs/rbac.md`

Contains the detailed study and implementation notes for RBAC.

---

# 7. Example Usage

Create permissions:

```python
from authorization_engine.models import Permission, Role
from authorization_engine.engine import AuthorizationEngine
```

Create a role:

```python
developer = Role(
    "developer",
    {
        Permission("reports", "read"),
        Permission("reports", "write"),
    },
)
```

Create the engine:

```python
engine = AuthorizationEngine()
```

Register the role:

```python
engine.add_role(developer)
```

Assign the role to a subject:

```python
engine.assign_role("alice", "developer")
```

Authorize requests:

```python
engine.authorize("alice", "reports", "read")
engine.authorize("alice", "reports", "write")
engine.authorize("alice", "reports", "delete")
```

Expected result:

```text
read: True
write: True
delete: False
```

---

# 8. Authorization Decision

The engine can provide an authorization decision rather than treating authorization as only a Boolean operation.

Conceptually:

```text
ALLOW
reason:
role 'developer' grants 'reports:read'
```

or:

```text
DENY
reason:
no assigned role grants 'reports:delete'
```

This makes authorization behavior easier to understand and debug.

---

# 9. Multiple Roles

A subject can have multiple roles.

Example:

```text
                    Alice
                   /     \
                  /       \
                 v         v
            Developer     Auditor
                |             |
                v             v
         reports:read     audit:read
         reports:write
```

Alice therefore receives:

```text
reports:read
reports:write
audit:read
```

But does not automatically receive:

```text
reports:delete
audit:write
```

Permissions remain explicitly defined by the assigned roles.

---

# 10. Permission Isolation

Permission isolation is an important RBAC property.

Consider:

```text
Developer
├── reports:read
└── reports:write

Auditor
└── audit:read
```

Even if:

```text
Alice -> Developer
Alice -> Auditor
```

the engine must not infer:

```text
reports:delete
audit:write
```

Only explicitly granted permissions are allowed.

---

# 11. Authentication vs Authorization

This project implements **authorization**, not authentication.

They are separate concerns.

```text
                User
                 |
                 v
          Authentication
                 |
                 | Who are you?
                 v
               Alice
                 |
                 v
          Authorization
                 |
                 | What can you do?
                 v
          RBAC Engine
             /       \
            v         v
         ALLOW      DENY
```

Authentication answers:

> Who are you?

Authorization answers:

> What are you allowed to do?

The RBAC engine assumes the subject has already been identified.

---

# 12. Real-World Architecture

In a production environment, authentication and authorization could be separated:

```text
              Identity Provider
                      |
                      | Authentication
                      v
                Identity / Token
                      |
                      v
                 API Gateway
                      |
                      v
                Application
                      |
                      v
             Authorization Engine
                      |
                      v
                 RBAC Decision
                  /         \
                 v           v
              ALLOW         DENY
                 |           |
                 v           v
             Operation       403
```

The identity provider could use technologies such as:

```text
OIDC
OAuth 2.0
SAML
```

Those protocols are outside the scope of this RBAC v0.1 implementation.

---

# 13. Service Account Example

RBAC can also authorize non-human principals.

Example:

```text
billing-service
      |
      v
billing-reader
      |
      v
billing:read
```

Request:

```text
billing-service -> billing:read
```

Result:

```text
ALLOW
```

This reflects an important IAM concept:

> Authorization applies to principals, not only human users.

---

# 14. Validation

The engine validates basic authorization configuration.

Examples of invalid permissions:

```python
Permission("", "read")
Permission("reports", "")
```

Invalid role:

```python
Role("", {...})
```

These invalid values are rejected.

Role assignment also validates that the target role exists.

Example:

```text
assign_role("alice", "does-not-exist")
```

results in an error rather than creating an invalid role reference.

---

# 15. Testing

The project uses `pytest`.

Run:

```powershell
pytest
```

The current test suite contains **9 tests** covering the core RBAC behavior.

Successful verification:

```text
collected 9 items

tests	est_rbac.py ......... [100%]

9 passed
```

This is the primary evidence for the RBAC Engine v0.1 implementation.

---

# 16. Current Test Coverage

The tests cover:

```text
✓ Granted permission -> ALLOW
✓ Ungranted permission -> DENY
✓ Unknown subject -> DENY
✓ Multiple roles
✓ Invalid role assignment
✓ Permission isolation
✓ Empty permission resource rejected
✓ Empty permission action rejected
✓ Empty role name rejected
```

Both positive and negative authorization paths are intentionally tested.

---

# 17. Design Principles

The v0.1 implementation follows these principles.

### 1. Default deny

No explicit permission means:

```text
DENY
```

### 2. Explicit grants

Permissions must be explicitly present in an assigned role.

### 3. Role-based assignment

Subjects receive permissions through roles:

```text
Subject → Role → Permission
```

### 4. Separation of concerns

Authentication and authorization are separate.

### 5. Deterministic authorization

The same authorization state and request should produce the same decision.

### 6. Test-driven verification

Authorization behavior is validated with automated tests.

---

# 18. What v0.1 Implements

```text
✓ Permission model
✓ Role model
✓ Subject-to-role assignment
✓ Role registration
✓ Permission matching
✓ ALLOW decision
✓ DENY decision
✓ Default deny
✓ Multiple roles
✓ Permission isolation
✓ Input validation
✓ Automated tests
```

---

# 19. What v0.1 Does Not Implement

The following are intentionally outside the current scope:

```text
✗ Authentication
✗ OAuth 2.0
✗ OpenID Connect
✗ SAML
✗ JWT validation
✗ Token validation
✗ HTTP API
✗ Database persistence
✗ Role hierarchy
✗ Role inheritance
✗ Attribute-Based Access Control (ABAC)
✗ Relationship-Based Access Control (ReBAC)
✗ Deny policies
✗ Policy conditions
✗ Time-based access
✗ IP-based access
✗ Resource ownership
✗ Audit logging
✗ Risk scoring
```

These can be considered future extensions rather than requirements for v0.1.

---

# 20. RBAC vs ABAC

RBAC primarily evaluates roles:

```text
Subject
   |
   v
Role
   |
   v
Permission
   |
   v
Decision
```

ABAC evaluates attributes and context:

```text
Subject attributes
        +
Resource attributes
        +
Action
        +
Environment
        |
        v
      Policy
        |
        v
     Decision
```

Example RBAC:

```text
Alice
  |
Developer
  |
reports:write
  |
ALLOW
```

Example ABAC:

```text
Alice
+
Developer
+
reports
+
write
+
corporate network
+
business hours
      |
      v
    ALLOW
```

RBAC is the foundation implemented by this project.

---

# 21. RBAC vs ReBAC

Relationship-Based Access Control (ReBAC) evaluates relationships between entities.

Example:

```text
Alice
  |
  | member of
  v
Engineering Team
  |
  | owns
  v
Project A
```

RBAC:

```text
Alice → Developer → project:read
```

ReBAC:

```text
Alice → member of → Engineering
Engineering → owns → Project A
```

ReBAC is not part of v0.1.

---

# 22. v0.1 Authorization Algorithm

The core algorithm can be represented as:

```text
authorize(subject, resource, action)
                |
                v
     Create requested permission
                |
                v
       Find subject's roles
                |
                v
       Iterate through roles
                |
                v
      Does role contain permission?
             /           \
           YES            NO
            |              |
            v              v
         ALLOW       Check next role
                           |
                           v
                    No roles match
                           |
                           v
                         DENY
```

Pseudocode:

```text
requested_permission = Permission(resource, action)

roles = roles_assigned_to(subject)

for role in roles:
    if requested_permission in role.permissions:
        return ALLOW

return DENY
```

---

# 23. Deliverable

| Item | Status |
|---|---|
| RBAC domain model | Complete |
| Role management | Complete |
| Role assignment | Complete |
| Authorization evaluation | Complete |
| Default deny | Complete |
| Multiple roles | Complete |
| Validation | Complete |
| Automated tests | Complete |
| Test evidence | 9 passed |
| RBAC Engine v0.1 | **Complete** |

---

# 24. Verification

From the project root:

```powershell
pytest
```

Expected:

```text
============================= test session starts =============================
collected 9 items

tests	est_rbac.py ......... [100%]

============================== 9 passed ======================================
```

A basic manual verification can also be performed:

```powershell
python -c "from authorization_engine.models import Permission, Role; from authorization_engine.engine import AuthorizationEngine; engine=AuthorizationEngine(); developer=Role('developer',{Permission('reports','read'),Permission('reports','write')}); engine.add_role(developer); engine.assign_role('alice','developer'); print('read:',engine.authorize('alice','reports','read')); print('write:',engine.authorize('alice','reports','write')); print('delete:',engine.authorize('alice','reports','delete'))"
```

Expected:

```text
read: True
write: True
delete: False
```

---

# 25. Interview Explanation

A concise explanation of this project:

> I implemented a lightweight RBAC authorization engine in Python. Subjects are assigned roles, roles contain explicit resource-action permissions, and the engine evaluates authorization requests by checking whether any assigned role grants the requested permission. The engine follows a default-deny model, supports multiple roles, validates authorization configuration, and provides explainable authorization decisions. The implementation is covered by automated pytest tests.

---

# 26. Architecture Interview Questions

### Q1. What is RBAC?

RBAC is Role-Based Access Control, where permissions are grouped into roles and subjects receive access by being assigned those roles.

```text
Subject → Role → Permission
```

### Q2. Why use roles?

Roles reduce duplicated permission assignments and make authorization easier to manage.

### Q3. What happens when no role grants a permission?

The engine returns:

```text
DENY
```

### Q4. Can a subject have multiple roles?

Yes.

```text
Alice
├── Developer
└── Auditor
```

Permissions from both roles are evaluated.

### Q5. Does authentication happen inside this engine?

No.

Authentication establishes identity. The RBAC engine performs authorization.

### Q6. Why default deny?

Because authorization should fail closed when no explicit grant exists.

### Q7. What would you add for production?

Potential extensions include:

```text
Persistent policy storage
API layer
Role hierarchy
Policy conditions
Deny semantics
ABAC
ReBAC
Audit logging
Policy versioning
Distributed caching
High-availability deployment
```

---

# 27. Future Evolution

A possible evolution path is:

```text
RBAC v0.1
   |
   v
Basic Role-Based Authorization
   |
   v
RBAC v0.2
   |
   +-- Persistent storage
   +-- API
   +-- Better decision model
   |
   v
RBAC v0.3
   |
   +-- Role hierarchy
   +-- Conditions
   +-- Explicit deny
   |
   v
Advanced Authorization
   |
   +-- ABAC
   +-- ReBAC
   +-- Policy engine
   +-- Audit logging
   +-- Risk scoring
```

The architecture should evolve incrementally rather than introducing unnecessary complexity into the first version.

---

# 28. Relationship to IAM

This project focuses specifically on the **authorization** part of IAM.

A simplified IAM architecture is:

```text
                         IAM
                          |
            +-------------+-------------+
            |                           |
            v                           v
     Authentication              Authorization
            |                           |
            v                           v
       Who are you?              What can you do?
                                        |
                                        v
                                   RBAC Engine
                                        |
                                        v
                                   ALLOW / DENY
```

The broader IAM ecosystem can include:

```text
Identity
Authentication
Federation
SSO
Authorization
Policy
Audit
Governance
Privileged Access
Risk
```

RBAC is one authorization model within that larger IAM domain.

---

# 29. Final Status

```text
┌───────────────────────────────────────┐
│       RBAC AUTHORIZATION ENGINE       │
│               v0.1                    │
├───────────────────────────────────────┤
│                                       │
│  Subject → Role → Permission          │
│                                       │
│  Default Deny                          │
│  Multiple Roles                        │
│  Permission Isolation                  │
│  Input Validation                      │
│  Explainable Decisions                 │
│                                       │
│  Tests: 9 passed                       │
│                                       │
│  STATUS: COMPLETE                      │
│                                       │
└───────────────────────────────────────┘
```

## Deliverable

**RBAC Engine v0.1 — Complete**

The detailed implementation and study notes are available in:

```text
docs/rbac.md
```


---

# 30. ABAC Implementation

The project now also includes an **Attribute-Based Access Control (ABAC)** implementation.

ABAC extends authorization beyond static role membership by evaluating attributes associated with:

```text
User / Subject
      +
Resource
      +
Action
      +
Environment / Context
      |
      v
     Policy
      |
      v
ALLOW / DENY
```

The ABAC implementation is a separate authorization model within this project. **ReBAC remains a separate lab.**

## ABAC Project Goal

The ABAC lab implements authorization using:

- user attributes
- resource attributes
- requested action
- context/environment attributes

The v0.1 policy is:

```text
ALLOW if:

action == "read"

AND

user.department == resource.department

AND

context.network == "corporate"
```

Example:

```text
User:
department = engineering

Resource:
department = engineering

Context:
network = corporate

Action:
read

                    |
                    v
             ABAC Policy
                    |
                    v
                  ALLOW
```

---

# 31. ABAC Architecture

The project now contains both RBAC and ABAC authorization models:

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
     Role / Permission         User / Resource / Context
             |                           |
             v                           v
       RBAC Decision              ABAC Decision
       ALLOW / DENY               ALLOW / DENY
```

Conceptually:

```text
RBAC:
Subject → Role → Permission → Decision


ABAC:
Subject attributes
       +
Resource attributes
       +
Action
       +
Context attributes
       |
       v
     Policy
       |
       v
    Decision
```

---

# 32. ABAC Project Structure

The current project structure is:

```text
authorization-engine/
│
├── docs/
│   ├── rbac.md
│   └── abac.md
│
├── src/
│   └── authorization_engine/
│       ├── __init__.py
│       ├── models.py
│       ├── engine.py
│       ├── abac_models.py
│       └── abac_engine.py
│
├── tests/
│   ├── test_rbac.py
│   └── test_abac.py
│
├── .gitignore
├── pyproject.toml
└── README.md
```

## ABAC Components

### `abac_models.py`

Defines the ABAC domain objects:

```text
User
Resource
AccessContext
ABACRequest
ABACDecision
```

### `abac_engine.py`

Contains the ABAC authorization logic:

```text
ABACEngine
```

The engine evaluates user, resource, action, and context attributes against the v0.1 ABAC policy.

### `tests/test_abac.py`

Contains the automated ABAC test suite.

### `docs/abac.md`

Contains the detailed ABAC study and implementation notes.

---

# 33. ABAC Example Usage

Create a user:

```python
from authorization_engine.abac_models import (
    User,
    Resource,
    AccessContext,
    ABACRequest,
)
from authorization_engine.abac_engine import ABACEngine

user = User(
    "alice",
    {
        "department": "engineering",
    },
)
```

Create a resource:

```python
resource = Resource(
    "report-123",
    {
        "department": "engineering",
    },
)
```

Create the request context:

```python
context = AccessContext(
    {
        "network": "corporate",
    }
)
```

Create an authorization request:

```python
request = ABACRequest(
    user,
    resource,
    "read",
    context,
)
```

Evaluate it:

```python
decision = ABACEngine().authorize(request)

print(decision)
```

Expected:

```text
ABACDecision(
    allowed=True,
    reason='department matches and request is from corporate network'
)
```

---

# 34. ABAC DENY Example

Change the resource department:

```python
resource = Resource(
    "report-123",
    {
        "department": "finance",
    },
)
```

The user remains:

```text
department = engineering
```

The request is:

```text
Alice
engineering
    |
    v
Report
finance
    |
    v
Department mismatch
    |
    v
DENY
```

The implementation returns:

```text
ABACDecision(
    allowed=False,
    reason='user department does not match resource department'
)
```

This demonstrates that authorization depends on the relationship between attributes rather than only the identity of the user.

---

# 35. ABAC Test Evidence

The ABAC-specific test suite was executed with:

```powershell
pytest tests/test_abac.py
```

Result:

```text
collected 7 items

tests\test_abac.py ....... [100%]

7 passed
```

The complete regression suite was also executed:

```powershell
pytest
```

Result:

```text
collected 16 items

tests\test_abac.py ....... [ 43%]
tests\test_rbac.py ....... [100%]

16 passed
```

Therefore:

```text
RBAC tests = 9 passed
ABAC tests = 7 passed
----------------------
Total      = 16 passed
```

The ABAC implementation therefore has automated test coverage while preserving the existing RBAC behavior.

---

# 36. ABAC Test Scenarios

The ABAC test suite covers both successful and denied authorization paths.

```text
✓ Matching user/resource department + corporate network -> ALLOW

✓ User/resource department mismatch -> DENY

✓ Non-corporate network -> DENY

✓ Unsupported action -> DENY

✓ Missing user department -> DENY

✓ Missing resource department -> DENY

✓ Missing network context -> DENY
```

The tests demonstrate the key ABAC security property:

```text
Conditions satisfied
        |
        v
      ALLOW

Conditions not satisfied
        |
        v
       DENY
```

---

# 37. ABAC Fail-Closed Behavior

The ABAC implementation follows a **fail-closed** approach.

If a required attribute is missing, the engine does not assume that access is permitted.

Example:

```text
User.department = missing
Resource.department = engineering
Network = corporate
        |
        v
Policy cannot establish a valid match
        |
        v
      DENY
```

Similarly:

```text
User.department = engineering
Resource.department = engineering
Network = missing
        |
        v
Corporate-network condition not satisfied
        |
        v
      DENY
```

This is important because missing security information should not accidentally become an authorization grant.

---

# 38. RBAC and ABAC Together

The project now demonstrates two major authorization models.

## RBAC

```text
Subject
   |
   v
Role
   |
   v
Permission
   |
   v
ALLOW / DENY
```

RBAC is useful when access can be expressed through stable organizational roles.

Example:

```text
Alice → Developer → reports:read
```

## ABAC

```text
User attributes
       +
Resource attributes
       +
Action
       +
Context
       |
       v
     Policy
       |
       v
ALLOW / DENY
```

ABAC is useful when authorization depends on dynamic or contextual information.

Example:

```text
Alice
department = engineering

Report
department = engineering

Network
corporate

Action
read

        |
        v
      ALLOW
```

---

# 39. When to Use RBAC vs ABAC

A practical decision guide:

```text
Can access be expressed cleanly as a role?
                  |
              YES | NO
                  |  \
                  v   v
                RBAC  ABAC
```

Use **RBAC** when permissions are relatively stable:

```text
Developer → reports:read
Admin     → reports:delete
Auditor   → audit:read
```

Use **ABAC** when decisions depend on attributes or context:

```text
department
classification
network
location
device trust
time
risk
clearance
```

In a mature enterprise IAM architecture, RBAC and ABAC can also be combined.

For example:

```text
User must have Developer role
             AND
user.department == resource.department
             AND
network == corporate
             |
             v
           ALLOW
```

---

# 40. Current Authorization Engine Deliverables

The authorization-engine project now contains:

| Capability | Status |
|---|---|
| RBAC domain model | Complete |
| RBAC role management | Complete |
| RBAC role assignment | Complete |
| RBAC authorization evaluation | Complete |
| RBAC default deny | Complete |
| RBAC automated tests | Complete |
| ABAC user attributes | Complete |
| ABAC resource attributes | Complete |
| ABAC action evaluation | Complete |
| ABAC context attributes | Complete |
| ABAC policy evaluation | Complete |
| ABAC ALLOW / DENY decisions | Complete |
| ABAC fail-closed behavior | Complete |
| ABAC automated tests | Complete |
| RBAC + ABAC regression suite | **16 tests passed** |

---

# 41. Updated Project Status

```text
┌──────────────────────────────────────────┐
│       AUTHORIZATION ENGINE               │
├──────────────────────────────────────────┤
│                                          │
│  RBAC                                    │
│  Subject → Role → Permission             │
│  Status: COMPLETE                        │
│  Tests: 9 passed                         │
│                                          │
│  ABAC                                    │
│  User + Resource + Action + Context      │
│  Status: COMPLETE                        │
│  Tests: 7 passed                         │
│                                          │
│  Total regression tests: 16 passed       │
│                                          │
└──────────────────────────────────────────┘
```

The project currently demonstrates two distinct authorization models:

```text
Authorization
     |
     +-------------------+
     |                   |
     v                   v
    RBAC                ABAC
     |                   |
Role-based          Attribute-based
authorization       authorization
```

**ReBAC remains a separate lab and is not included in the ABAC implementation.**

Detailed notes:

```text
docs/rbac.md
docs/abac.md
```
