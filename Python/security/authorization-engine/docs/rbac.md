# RBAC Authorization Engine v0.1

> A minimal, deterministic Role-Based Access Control (RBAC) authorization engine implemented in Python.

---

## 1. Overview

This project implements the core authorization logic of a Role-Based Access Control (RBAC) system.

The engine answers one fundamental authorization question:

> **Can this subject perform this action on this resource?**

The decision is based on the roles assigned to the subject and the permissions granted by those roles.

The core authorization relationship is:

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

### Example

Suppose:

```text
Subject:  alice
Role:     developer
Resource: reports
Action:   read
```

The `developer` role contains:

```text
reports:read
reports:write
```

Therefore:

```text
Alice
  |
  v
Developer
  |
  +---- reports:read
  +---- reports:write

Request:
Alice -> reports:read

Result:
ALLOW
```

However:

```text
Request:
Alice -> reports:delete

Result:
DENY
```

because the `developer` role does not grant `reports:delete`.

---

# 2. What is RBAC?

RBAC stands for **Role-Based Access Control**.

Instead of assigning permissions directly to individual users, permissions are grouped into roles.

Users or other subjects are then assigned roles.

The relationship is:

```text
User
  |
  v
Role
  |
  v
Permissions
```

For example:

```text
Alice
  |
  +---- Developer
           |
           +---- reports:read
           +---- reports:write
```

Alice receives the permissions through the `developer` role.

---

# 3. Why RBAC?

Without RBAC, an authorization system could assign permissions individually:

```text
Alice   -> reports:read
Alice   -> reports:write

Bob     -> reports:read

Charlie -> reports:read
Charlie -> reports:write
Charlie -> reports:delete
```

This becomes difficult to manage as the organization grows.

RBAC introduces an abstraction layer:

```text
                 Roles
                  |
        +---------+---------+
        |         |         |
        v         v         v
     Viewer   Developer    Admin
        |         |         |
        v         v         v
   Permissions Permissions Permissions
        ^
        |
      Users
```

Now permissions are associated with job responsibilities rather than individual users.

---

# 4. Core RBAC Concepts

## 4.1 Subject

A **subject** is the entity requesting access.

In this v0.1 implementation, a subject is represented by a string identifier.

Examples:

```text
alice
bob
service-account-1
```

The engine does not authenticate the subject.

It assumes that authentication has already occurred.

---

## 4.2 Role

A role represents a collection of permissions.

Examples:

```text
viewer
developer
auditor
admin
```

Example:

```text
Developer
├── reports:read
└── reports:write
```

---

## 4.3 Permission

A permission represents an allowed operation on a resource.

The implementation models a permission as:

```text
(resource, action)
```

Example:

```text
("reports", "read")
```

Conceptually:

```text
reports:read
```

Another example:

```text
("reports", "write")
```

---

# 5. RBAC Data Model

The implementation contains three primary domain concepts.

```text
+----------------+
|    Subject     |
+----------------+
        |
        | assigned roles
        v
+----------------+
|      Role      |
+----------------+
        |
        | contains
        v
+----------------+
|   Permission   |
+----------------+
```

The Python model is:

```python
@dataclass(frozen=True)
class Permission:
    resource: str
    action: str
```

A role contains a set of permissions:

```python
@dataclass
class Role:
    name: str
    permissions: set[Permission]
```

The authorization result is represented as:

```python
@dataclass(frozen=True)
class AuthorizationDecision:
    decision: Decision
    reason: str
```

---

# 6. Decision Model

The engine has two possible decisions:

```text
ALLOW
DENY
```

They are represented by:

```python
class Decision(Enum):
    ALLOW = "allow"
    DENY = "deny"
```

The engine does not return only a Boolean.

It returns an `AuthorizationDecision`.

Example:

```text
Decision:
    ALLOW

Reason:
    role 'developer' grants 'reports:read'
```

Or:

```text
Decision:
    DENY

Reason:
    no assigned role grants 'reports:delete'
```

This makes the authorization result explainable.

---

# 7. Authorization Engine Architecture

The v0.1 engine has two primary internal registries.

```text
                  AuthorizationEngine
                           |
             +-------------+-------------+
             |                           |
             v                           v
       Role Registry             Subject -> Roles
             |                           |
             v                           v
        Role objects                  Alice
             |                           |
             v                    +------+------+
        Permissions               |             |
                                  v             v
                             Developer       Auditor
```

Conceptually:

```text
_roles

developer
    |
    +-- reports:read
    +-- reports:write

auditor
    |
    +-- audit:read
```

And:

```text
_subject_roles

alice
    |
    +-- developer
    +-- auditor
```

---

# 8. Authorization Flow

The authorization process follows this sequence:

```text
                  Authorization Request
                           |
                           v
                  +----------------+
                  |     Subject    |
                  |     = Alice    |
                  +----------------+
                           |
                           v
                 Find assigned roles
                           |
                           v
                 +-------------------+
                 | Developer, Auditor|
                 +-------------------+
                           |
                           v
                  Build requested
                    Permission
                           |
                           v
                   resource:action
                           |
                           v
                Search role permissions
                           |
                    +------+------+
                    |             |
                 MATCH         NO MATCH
                    |             |
                    v             v
                 ALLOW          Continue
                                  |
                                  v
                         More roles available?
                           |             |
                          YES            NO
                           |             |
                           v             v
                     Check next       DENY
                       role
```

---

# 9. Authorization Algorithm

Given:

```text
subject
resource
action
```

the engine:

1. Creates the requested permission.
2. Finds the roles assigned to the subject.
3. Iterates through those roles.
4. Checks whether any role contains the requested permission.
5. Returns `ALLOW` if a match is found.
6. Returns `DENY` if no match is found.

Pseudocode:

```text
authorize(subject, resource, action):

    requested_permission = Permission(resource, action)

    roles = roles_assigned_to(subject)

    for role in roles:

        if requested_permission exists in role.permissions:

            return ALLOW

    return DENY
```

---

# 10. Default Deny

The engine follows a **default-deny** model.

This means:

> If no assigned role explicitly grants the requested permission, access is denied.

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

Default deny is a fundamental security property of authorization systems.

---

# 11. Example: Developer

Define:

```text
Role: developer

Permissions:
    reports:read
    reports:write
```

Assign:

```text
Alice -> developer
```

Now:

| Subject | Resource | Action | Result |
|---|---|---|---|
| Alice | reports | read | ALLOW |
| Alice | reports | write | ALLOW |
| Alice | reports | delete | DENY |

The engine does not infer permissions.

For example:

```text
reports:write
```

does not automatically imply:

```text
reports:delete
```

Every permission must explicitly exist.

---

# 12. Multiple Roles

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

Therefore Alice can access:

```text
reports:read
reports:write
audit:read
```

But not:

```text
reports:delete
audit:write
```

because neither role grants those permissions.

---

# 13. Permission Isolation

A critical RBAC property is permission isolation.

Consider:

```text
Developer
├── reports:read
└── reports:write

Auditor
└── audit:read
```

Alice has both roles:

```text
Alice
├── Developer
└── Auditor
```

The engine must not accidentally grant:

```text
audit:write
```

just because Alice has the `Auditor` role.

Likewise, it must not grant:

```text
reports:delete
```

because Alice has the `Developer` role.

The permission must exist explicitly in at least one assigned role.

---

# 14. Invalid Role Assignment

The engine validates role assignment.

If a role does not exist:

```text
Alice -> nonexistent-role
```

the engine raises:

```text
ValueError
```

This prevents the authorization state from containing references to undefined roles.

Flow:

```text
assign_role("alice", "nonexistent-role")
                  |
                  v
          Does role exist?
             /       \
           NO         YES
           |           |
           v           v
       ValueError    Assign
```

---

# 15. Domain Validation

The model also validates basic input invariants.

A permission requires:

```text
resource != ""
action   != ""
```

A role requires:

```text
name != ""
```

Examples that are rejected:

```python
Permission("", "read")
Permission("reports", "")
Role("", {...})
```

These produce `ValueError`.

This prevents obviously invalid authorization configuration from entering the engine.

---

# 16. Authentication vs Authorization

This engine implements **authorization**, not authentication.

These are separate security concerns.

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

> Who is this subject?

Authorization answers:

> What is this subject allowed to do?

For v0.1, the engine receives an already-established subject identifier.

---

# 17. Authentication and Authorization in a Real System

A production architecture could look like:

```text
             Identity Provider
                    |
                    | Authentication
                    v
              Access Token
                    |
                    v
              API Gateway
                    |
                    v
            Application/API
                    |
                    v
          Authorization Engine
                    |
                    v
               RBAC Decision
                 /       \
                v         v
             ALLOW       DENY
                |         |
                v         v
           Application    403
           operation
```

The identity provider and authentication protocol are outside this v0.1 engine.

---

# 18. Why the Engine Is Separate

Keeping authorization logic separate from authentication provides architectural separation.

```text
Authentication Layer
        |
        | authenticated subject
        v
Authorization Layer
        |
        | authorization decision
        v
Application
```

This allows the authorization engine to potentially work with subjects originating from:

- local authentication
- SAML federation
- OpenID Connect
- OAuth-based applications
- service accounts
- cloud identity systems

The RBAC engine does not need to know how the subject was authenticated.

---

# 19. Implementation Structure

Current project structure:

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

Responsibilities:

### `models.py`

Contains the authorization domain model:

```text
Permission
Role
Decision
AuthorizationDecision
```

### `engine.py`

Contains authorization logic:

```text
AuthorizationEngine
```

Responsibilities include:

```text
Add role
Assign role
Evaluate permission
Return decision
```

### `test_rbac.py`

Contains automated tests for the authorization behavior.

---

# 20. Test Strategy

The engine is tested using `pytest`.

The tests verify both positive and negative authorization paths.

Current test coverage includes:

```text
1. Granted permission -> ALLOW
2. Ungranted permission -> DENY
3. Unknown subject -> DENY
4. Multiple roles
5. Invalid role assignment
6. Permission isolation
7. Empty permission resource
8. Empty permission action
9. Empty role name
```

---

# 21. Test Evidence

The current test suite was executed with:

```powershell
pytest
```

Result:

```text
collected 9 items

tests	est_rbac.py ......... [100%]

9 passed in 0.06s
```

This demonstrates that all current v0.1 RBAC tests pass.

---

# 22. Security Properties Demonstrated

The current implementation demonstrates several important authorization properties.

## 22.1 Default Deny

Unmatched permissions result in:

```text
DENY
```

## 22.2 Explicit Permission Grants

Permissions are granted only when explicitly present in an assigned role.

## 22.3 Role-Based Assignment

Subjects receive permissions through roles.

```text
Subject -> Role -> Permission
```

## 22.4 Permission Isolation

Permissions from one role do not implicitly create permissions for another resource or action.

## 22.5 Invalid Configuration Rejection

Undefined roles and invalid domain values are rejected.

## 22.6 Explainable Decisions

Authorization results contain a reason.

Example:

```text
ALLOW
role 'developer' grants 'reports:read'
```

or:

```text
DENY
no assigned role grants 'reports:delete'
```

---

# 23. What RBAC v0.1 Does NOT Implement

This version is intentionally limited.

It does not currently implement:

```text
Authentication
OAuth 2.0
OIDC
SAML
JWT validation
Token validation
HTTP API
Database persistence
Hierarchical roles
Role inheritance
ABAC
ReBAC
Deny policies
Policy conditions
Time-based access
IP-based access
Resource ownership
Audit logging
Risk scoring
```

These are potential future capabilities, not requirements for the current v0.1 task.

---

# 24. Current Authorization Model

The current authorization model can be summarized as:

```text
Subject
   |
   | assigned roles
   v
Role
   |
   | contains
   v
Permission
   |
   | matches request
   v
AuthorizationDecision
   |
   +---- ALLOW
   |
   +---- DENY
```

The engine therefore implements the basic authorization rule:

```text
ALLOW(subject, resource, action)
    if
requested permission is contained in the permissions
of any assigned role
```

Otherwise:

```text
DENY
```

---

# 25. Real-World Example

Consider an internal company reporting system.

Roles:

```text
Viewer
├── reports:read

Developer
├── reports:read
└── reports:write

Admin
├── reports:read
├── reports:write
└── reports:delete
```

Employees:

```text
Alice   -> Viewer
Bob     -> Developer
Charlie -> Admin
```

Authorization requests:

```text
Alice -> reports:read
       -> ALLOW

Alice -> reports:write
       -> DENY

Bob -> reports:write
    -> ALLOW

Bob -> reports:delete
    -> DENY

Charlie -> reports:delete
        -> ALLOW
```

The engine evaluates each request independently.

---

# 26. Service Account Example

RBAC is not limited to human users.

A service account can also be treated as a subject.

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
billing-service
      |
      +---- billing:read
```

Result:

```text
ALLOW
```

This illustrates an important IAM concept:

> Authorization applies to principals, not necessarily only humans.

---

# 27. RBAC vs Direct Permission Assignment

### Direct assignment

```text
Alice -> reports:read
Alice -> reports:write

Bob -> reports:read

Charlie -> reports:read
Charlie -> reports:write
Charlie -> reports:delete
```

### RBAC

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

Then:

```text
Alice   -> Viewer
Bob     -> Developer
Charlie -> Admin
```

RBAC provides a reusable abstraction around permission management.

---

# 28. RBAC Request Lifecycle

The complete lifecycle is:

```text
                 Request
                   |
                   v
          +----------------+
          |    Subject     |
          +----------------+
                   |
                   v
           Assigned Roles
                   |
                   v
         Role Permissions
                   |
                   v
        Requested Permission
                   |
                   v
            Permission Match
              /          \
            YES           NO
             |             |
             v             v
           ALLOW         DENY
             |             |
             +------+------+
                    |
                    v
        AuthorizationDecision
```

---

# 29. v0.1 Design Principles

The implementation intentionally follows several principles.

### Principle 1 — Keep authorization deterministic

The same authorization state and request should produce the same decision.

```text
Same input
    ↓
Same RBAC state
    ↓
Same decision
```

### Principle 2 — Default deny

Unknown or ungranted access should not become allowed accidentally.

### Principle 3 — Explicit permissions

The engine should not infer permissions.

### Principle 4 — Separate authentication from authorization

The engine evaluates authorization for an already identified subject.

### Principle 5 — Test authorization behavior

Both `ALLOW` and `DENY` paths must be tested.

---

# 30. Current Limitations

The current implementation is intentionally in-memory.

For example:

```python
engine = AuthorizationEngine()
```

creates an engine whose state exists only within the process.

Restarting the process removes:

```text
Roles
Role assignments
```

A production system would likely introduce persistent storage:

```text
                 Authorization Engine
                         |
                         v
                    Repository
                         |
                         v
                     Database
```

This is outside the v0.1 scope.

---

# 31. Future Evolution

A natural evolution path is:

```text
RBAC v0.1
   |
   v
Basic RBAC
   |
   v
RBAC v0.2
   |
   +-- Persistent role store
   +-- API layer
   +-- Better decision model
   |
   v
RBAC v0.3
   |
   +-- Role hierarchy
   +-- Deny policies
   +-- Conditions
   |
   v
Advanced Authorization
   |
   +-- ABAC
   +-- ReBAC
   +-- Policy engine
   +-- Audit logging
   +-- Risk evaluation
```

These extensions should be introduced only when the requirements justify them.

---

# 32. RBAC vs ABAC

RBAC makes decisions primarily based on roles.

```text
Subject
   ↓
Role
   ↓
Permission
   ↓
Decision
```

ABAC evaluates attributes and context.

```text
Subject attributes
        +
Resource attributes
        +
Action
        +
Environment/context
        ↓
    Policy
        ↓
    Decision
```

Example RBAC:

```text
Alice has Developer role
→ reports:write
→ ALLOW
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
→ ALLOW
```

This distinction is important for future authorization architecture.

---

# 33. RBAC vs ReBAC

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

A policy could determine whether Alice can access Project A based on that relationship.

RBAC:

```text
Alice → Developer → project:read
```

ReBAC:

```text
Alice → member of → Engineering
Engineering → owns → Project A
```

The current project is intentionally limited to RBAC.

---

# 34. Interview Explanation

A concise explanation of this implementation:

> "I implemented a small RBAC authorization engine in Python. Subjects are assigned roles, roles contain explicit resource-action permissions, and the engine evaluates an authorization request by checking whether any assigned role grants the requested permission. The engine follows default deny and returns an explicit authorization decision with a reason. I also added validation for invalid role and permission configuration and covered the main allow, deny, multi-role, and isolation scenarios with pytest."

---

# 35. Architecture Interview Question

### Question

How would you design a simple RBAC authorization engine?

### Answer

Start with:

```text
Subject → Role → Permission
```

Maintain:

```text
Role registry
Subject-to-role mapping
```

For each request:

```text
1. Identify subject
2. Resolve assigned roles
3. Construct requested permission
4. Check role permissions
5. Return ALLOW if any role grants it
6. Otherwise return DENY
```

Important security properties:

```text
Default deny
Explicit grants
Permission isolation
Deterministic decisions
Validation
Test coverage
```

---

# 36. Why This Is an Authorization Engine

This project is more than a collection of Python classes.

The engine provides a decision boundary:

```text
                 Application
                      |
                      | authorization request
                      v
             +-------------------+
             | Authorization      |
             | Engine             |
             +-------------------+
                      |
                      | decision
                      v
                 ALLOW / DENY
```

The application does not need to implement the RBAC algorithm itself.

Instead:

```text
Application
     |
     v
AuthorizationEngine
     |
     v
Decision
```

This creates a reusable authorization component.

---

# 37. v0.1 Deliverable

### Task

```text
Implement RBAC in authorization engine
```

### Type

```text
Build
```

### Deliverable

```text
RBAC Engine v0.1
```

### Status

```text
IMPLEMENTED
```

### Evidence

```text
9 automated tests passed
```

---

# 38. Final v0.1 Summary

The current engine implements:

```text
                    RBAC ENGINE v0.1
                           |
             +-------------+-------------+
             |                           |
             v                           v
          Subjects                     Roles
             |                           |
             | assigned                  | contain
             v                           v
          Role Set  ----------------> Permissions
                                          |
                                  requested permission
                                          |
                                          v
                                  Permission Matching
                                      /         \
                                   MATCH       NO MATCH
                                      |             |
                                      v             v
                                   ALLOW          DENY
                                      |             |
                                      +------+------+
                                             |
                                             v
                                  AuthorizationDecision
                                      + reason
```

The implementation establishes the core authorization foundation while deliberately leaving authentication, federation, tokens, policy conditions, persistence, and advanced authorization models outside the v0.1 scope.

---

# 39. Evidence Command

The primary verification command is:

```powershell
pytest
```

Expected evidence:

```text
collected 9 items

tests	est_rbac.py ......... [100%]

9 passed
```

This test result is the current verification evidence for **RBAC Engine v0.1**.
