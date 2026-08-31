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
                     /                             YES           NO
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
                   /                       /                        v         v
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
              /                    v         v
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
                  /                          v           v
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

tests\test_rbac.py ......... [100%]

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
             /                      YES            NO
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

tests\test_rbac.py ......... [100%]

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

# 30. ABAC — Attribute-Based Access Control

The authorization engine was extended after RBAC v0.1 with an independent **ABAC implementation**.

ABAC evaluates access using attributes of:

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

The ABAC implementation is intentionally separate from the original RBAC engine so that each authorization model can be understood and tested independently.

## ABAC Project Goal

The goal is to implement attribute-based authorization where access is determined by comparing user attributes, resource attributes, requested actions, and contextual attributes.

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
```

Decision:

```text
department matches
        +
corporate network
        |
        v
      ALLOW
```

If the user and resource departments do not match:

```text
User department != Resource department
        |
        v
      DENY
```

## ABAC Components

```text
ABACRequest
├── User
│   └── attributes
├── Resource
│   └── attributes
├── Action
└── AccessContext
    └── attributes
```

The implementation contains:

```text
src/authorization_engine/
├── abac_models.py
└── abac_engine.py
```

Tests:

```text
tests/
├── test_rbac.py
├── test_abac.py
└── test_rebac.py
```

Detailed ABAC documentation:

```text
docs/abac.md
```

## ABAC Implementation

The ABAC domain model includes:

```text
User
Resource
AccessContext
ABACRequest
ABACDecision
```

A simplified request looks like:

```python
user = User(
    "alice",
    {"department": "engineering"},
)

resource = Resource(
    "report-123",
    {"department": "engineering"},
)

context = AccessContext(
    {"network": "corporate"},
)

request = ABACRequest(
    user,
    resource,
    "read",
    context,
)
```

The authorization engine evaluates the request using the attributes.

## ABAC Example

Successful authorization:

```text
User department:     engineering
Resource department: engineering
Network:             corporate
Action:              read

                 |
                 v

              ALLOW
```

Failed authorization:

```text
User department:     engineering
Resource department: finance
Network:             corporate
Action:              read

                 |
                 v

               DENY
```

The implementation therefore demonstrates that ABAC can make authorization decisions without relying solely on static role membership.

## ABAC Test Evidence

The ABAC implementation contains **7 automated tests**.

Run:

```powershell
pytest tests/test_abac.py
```

Expected:

```text
collected 7 items

tests	est_abac.py ....... [100%]

7 passed
```

Full project verification after adding ABAC:

```powershell
pytest
```

The combined authorization engine test suite includes both RBAC and ABAC tests.

## ABAC Design Principles

The implementation follows:

```text
✓ Attribute-based decisions
✓ Explicit policy checks
✓ Default deny
✓ Context-aware authorization
✓ Resource/user attribute comparison
✓ Negative authorization tests
✓ Deterministic decisions
✓ Automated verification
```

## ABAC vs RBAC

RBAC:

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

ABAC:

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
    Decision
```

RBAC is useful when permissions naturally map to organizational roles.

ABAC is useful when access depends on richer contextual conditions.

## ABAC Deliverable

| Item | Status |
|---|---|
| ABAC domain model | Complete |
| User attributes | Complete |
| Resource attributes | Complete |
| Action evaluation | Complete |
| Context attributes | Complete |
| Attribute comparison | Complete |
| ALLOW / DENY decisions | Complete |
| Default deny | Complete |
| Automated tests | Complete |
| Test evidence | 7 passed |
| ABAC implementation | **Complete** |

Detailed implementation and study notes:

```text
docs/abac.md
```

---

# 31. ReBAC — Relationship-Based Access Control

The authorization engine was subsequently extended with a separate **ReBAC implementation** for relationship-based resource sharing.

ReBAC answers authorization questions based on relationships between subjects, groups, and resources rather than only static roles or attributes.

The core relationship is represented as a tuple:

```text
(subject, relation, resource)
```

Example:

```text
(alice, owner, document:report-123)
```

This means:

```text
Alice
  |
  | owner
  v
document:report-123
```

Another example:

```text
(bob, editor, document:report-123)
```

## ReBAC Project Goal

The goal is to implement relationship tuples and evaluate authorization based on the relationship between a subject and a specific resource.

The ReBAC model is:

```text
Subject
   |
   | relationship
   v
Resource
   |
   v
Authorization Decision
```

Unlike RBAC:

```text
Alice → Developer → reports:write
```

ReBAC evaluates the relationship directly:

```text
Alice → owner → document:report-123
```

The relationship determines the actions available to the subject.

## ReBAC Relationship Model

The implementation defines:

```text
RelationshipTuple
├── subject
├── relation
└── resource
```

Example:

```python
RelationshipTuple(
    "alice",
    "owner",
    "document:report-123",
)
```

Conceptually:

```text
alice
  |
  | owner
  v
document:report-123
```

The tuple is immutable and hashable so it can safely be stored in a set.

## Relationship Store

ReBAC relationships are stored by `RelationshipStore`.

The store supports:

```text
add()
remove()
exists()
```

Example:

```python
store.add(
    RelationshipTuple(
        "alice",
        "owner",
        "document:report-123",
    )
)
```

A relationship can then be queried:

```python
store.exists(
    "alice",
    "owner",
    "document:report-123",
)
```

Expected:

```text
True
```

A different subject:

```python
store.exists(
    "bob",
    "owner",
    "document:report-123",
)
```

returns:

```text
False
```

This demonstrates that relationships are resource-specific.

## ReBAC Permission Mapping

The v0.1 ReBAC implementation maps relationships to actions:

```text
owner
├── read
├── write
└── delete

editor
├── read
└── write

viewer
└── read
```

Therefore:

```text
Alice → owner → document
```

allows:

```text
read
write
delete
```

while:

```text
Bob → editor → document
```

allows:

```text
read
write
```

but not:

```text
delete
```

And:

```text
Charlie → viewer → document
```

allows:

```text
read
```

but not:

```text
write
delete
```

## ReBAC Authorization Flow

```text
Authorization Request
        |
        v
      Subject
        |
        v
   Resource + Action
        |
        v
Relationship Store
        |
        v
Find subject/resource relationship
        |
        v
Relationship → Allowed Actions
        |
        v
   +-----------+
   |           |
   v           v
 ALLOW       DENY
```

Example:

```text
alice
  |
  | owner
  v
document:report-123
  |
  +---- read
  +---- write
  +---- delete
```

Request:

```text
alice -> delete -> document:report-123
```

Result:

```text
ALLOW
```

## Resource-Specific Relationships

A major ReBAC property is that access can be specific to an individual resource.

Example:

```text
alice → owner → document:report-123
alice → viewer → document:design-456
```

Alice therefore has different access to different resources.

For `report-123`:

```text
read   -> ALLOW
write  -> ALLOW
delete -> ALLOW
```

For `design-456`:

```text
read   -> ALLOW
write  -> DENY
delete -> DENY
```

This is different from a global role assignment because the relationship is attached directly to the resource.

## Group Membership

The implementation also supports group-based relationship inheritance.

Example:

```text
Alice
  |
  | member of
  v
group:engineering
  |
  | viewer
  v
document:report-123
```

The relationship chain means Alice inherits the group's access to the resource.

For example:

```text
Group:
group:engineering → viewer → document:report-123

Membership:
alice → member of → group:engineering
```

The engine can therefore resolve:

```text
alice → viewer → document:report-123
```

and authorize:

```text
alice → read → document:report-123
```

while still denying:

```text
alice → write → document:report-123
alice → delete → document:report-123
```

This demonstrates an important ReBAC concept: **relationships can be composed to derive access**.

## ReBAC Implementation

The ReBAC implementation contains:

```text
src/authorization_engine/
├── rebac_models.py
├── rebac_store.py
└── rebac_engine.py
```

### `rebac_models.py`

Defines:

```text
RelationshipTuple
GroupMembership
```

### `rebac_store.py`

Maintains:

```text
Relationship tuples
Group memberships
```

and provides relationship lookup operations.

### `rebac_engine.py`

Contains the authorization logic:

```text
ReBACEngine
```

Responsibilities include:

```text
✓ relationship lookup
✓ resource-specific authorization
✓ relationship-to-permission mapping
✓ group membership resolution
✓ default deny
```

Tests:

```text
tests/test_rebac.py
```

Detailed ReBAC documentation:

```text
docs/rebac.md
```

## ReBAC Test Evidence

The ReBAC implementation contains **13 automated tests**.

Run:

```powershell
pytest tests/test_rebac.py
```

Expected:

```text
collected 13 items

tests	est_rebac.py ............. [100%]

13 passed
```

The tests cover:

```text
✓ Owner can read
✓ Owner can write
✓ Owner can delete
✓ Editor can read
✓ Editor can write
✓ Editor cannot delete
✓ Viewer can read
✓ Viewer cannot write
✓ Viewer cannot delete
✓ Unknown user is denied
✓ Relationship is resource-specific
✓ Same user can have different relationships with different resources
✓ Group member inherits resource access
```

## Full Authorization Engine Verification

Run the complete test suite:

```powershell
pytest
```

Current combined evidence:

```text
tests	est_abac.py .......       7 tests
tests	est_rbac.py .........     9 tests
tests	est_rebac.py ............. 13 tests

29 passed
```

This verifies that the RBAC, ABAC, and ReBAC implementations coexist within the same authorization-engine project.

## ReBAC vs RBAC vs ABAC

### RBAC

RBAC evaluates:

```text
Subject → Role → Permission
```

Example:

```text
Alice → Developer → reports:write
```

### ABAC

ABAC evaluates:

```text
Subject attributes
+
Resource attributes
+
Action
+
Context
→ Policy → Decision
```

Example:

```text
Alice.department == report.department
+
network == corporate
→ ALLOW
```

### ReBAC

ReBAC evaluates:

```text
Subject → Relationship → Resource
```

Example:

```text
Alice → owner → document:report-123
```

A useful comparison is:

```text
RBAC
Who are you assigned as?
        |
        v
      Role

ABAC
What attributes/context apply?
        |
        v
      Policy

ReBAC
How are you related to this resource?
        |
        v
   Relationship
```

These models solve different authorization problems and can also be combined in production authorization systems.

## ReBAC Security Principles

The implementation follows:

```text
✓ Default deny
✓ Explicit relationships
✓ Resource-specific authorization
✓ Deterministic evaluation
✓ Immutable relationship tuples
✓ Explicit relationship-to-action mapping
✓ Unknown subjects denied
✓ Unknown relationships denied
✓ Automated negative-path testing
```

The engine does not infer arbitrary access.

For example:

```text
viewer
```

does not automatically imply:

```text
write
delete
```

and:

```text
editor
```

does not automatically imply:

```text
delete
```

## ReBAC Deliverable

| Item | Status |
|---|---|
| Relationship tuple model | Complete |
| Relationship store | Complete |
| Relationship lookup | Complete |
| Owner relationship | Complete |
| Editor relationship | Complete |
| Viewer relationship | Complete |
| Resource-specific access | Complete |
| Group membership | Complete |
| Group-derived access | Complete |
| Default deny | Complete |
| Negative authorization tests | Complete |
| Automated tests | Complete |
| Test evidence | 13 passed |
| ReBAC implementation | **Complete** |

Detailed implementation and study notes:

```text
docs/rebac.md
```

---

# 32. Authorization Models — Current Project Status

The authorization-engine project now demonstrates three major authorization models:

```text
                    Authorization Engine
                            |
            +---------------+---------------+
            |               |               |
            v               v               v
           RBAC            ABAC            ReBAC
            |               |               |
            v               v               v
     Role-based       Attribute-based   Relationship-based
       access             access             access
            |               |               |
            +---------------+---------------+
                            |
                            v
                       ALLOW / DENY
```

### RBAC

```text
Subject → Role → Permission
```

Evidence:

```text
9 tests passed
```

### ABAC

```text
User attributes
+
Resource attributes
+
Action
+
Context
→ Policy → Decision
```

Evidence:

```text
7 tests passed
```

### ReBAC

```text
Subject → Relationship → Resource
```

Evidence:

```text
13 tests passed
```

Combined:

```text
9 + 7 + 13 = 29 tests
```

Current verification:

```text
29 passed
```

The project therefore demonstrates three complementary authorization paradigms within a single Python authorization-engine codebase.

## Current Project Structure

```text
authorization-engine/
│
├── docs/
│   ├── rbac.md
│   ├── abac.md
│   └── rebac.md
│
├── src/
│   └── authorization_engine/
│       ├── __init__.py
│       │
│       ├── models.py
│       ├── engine.py
│       │
│       ├── abac_models.py
│       ├── abac_engine.py
│       │
│       ├── rebac_models.py
│       ├── rebac_store.py
│       └── rebac_engine.py
│
├── tests/
│   ├── test_rbac.py
│   ├── test_abac.py
│   └── test_rebac.py
│
├── .gitignore
├── pyproject.toml
└── README.md
```

## Authorization Evolution

The project has evolved from a simple RBAC engine into a small authorization-model laboratory:

```text
RBAC v0.1
   |
   | Role-based authorization
   v
ABAC
   |
   | Attribute + context based authorization
   v
ReBAC
   |
   | Relationship + resource based authorization
   v
Advanced Authorization
```

The implementations remain separated by module so that the behavior and trade-offs of each authorization model can be studied independently.

---

# 33. Overall Interview Explanation

A concise explanation of the current authorization-engine project:

> I built a lightweight Python authorization engine and evolved it across three authorization models: RBAC, ABAC, and ReBAC. RBAC evaluates explicit permissions through role assignments, ABAC evaluates subject, resource, action, and environmental attributes, and ReBAC evaluates relationships between subjects, groups, and specific resources. Each model follows a default-deny approach and is independently tested with positive and negative authorization scenarios. The project currently has 29 automated pytest tests covering the three models.

---

# 34. Current Deliverables

| Authorization Model | Implementation | Documentation | Tests | Status |
|---|---|---|---:|---|
| RBAC | `engine.py`, `models.py` | `docs/rbac.md` | 9 | **Complete** |
| ABAC | `abac_engine.py`, `abac_models.py` | `docs/abac.md` | 7 | **Complete** |
| ReBAC | `rebac_engine.py`, `rebac_models.py`, `rebac_store.py` | `docs/rebac.md` | 13 | **Complete** |
| Combined engine | All modules | `README.md` | 29 | **Complete** |

Final verification:

```powershell
pytest
```

Expected:

```text
tests	est_abac.py .......       [ 24%]
tests	est_rbac.py .........     [ 55%]
tests	est_rebac.py ............. [100%]

29 passed
```

The authorization-engine project now demonstrates:

```text
RBAC
+
ABAC
+
ReBAC
+
Default Deny
+
Explicit Authorization
+
Resource-specific Access
+
Context-aware Access
+
Relationship-based Sharing
+
Automated Security Testing
```

