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

# 30. Policy Versioning and Audit Trail

The authorization engine has been extended with **policy versioning and an audit trail**.

This build addresses the policy-management requirement:

| Focus | Policy |
|---|---|
| Task | Add policy versioning and audit trail |
| Type | Build |
| Deliverable / Evidence | Versioned policy store |

The implementation introduces a versioned policy lifecycle while preserving the existing RBAC, ABAC, and ReBAC components.

## 30.1 Policy Version Model

Each policy version is represented by a `PolicyVersion` object containing:

```text
policy_id
version
rule
created_at
created_by
```

Conceptually:

```text
Policy
  |
  +-- Version 1
  |     |
  |     +-- Rule
  |     +-- Created timestamp
  |     +-- Created by
  |
  +-- Version 2
        |
        +-- Rule
        +-- Created timestamp
        +-- Created by
```

Example:

```python
PolicyVersion(
    "document-read",
    1,
    "alice can read report-123",
    timestamp,
    "admin",
)
```

The model is immutable using a frozen dataclass, preventing accidental mutation of historical policy records.

## 30.2 Versioned Policy Store

`VersionedPolicyStore` maintains policy history by `policy_id`.

The store supports:

```text
add_version()
get_latest()
get_version()
list_versions()
```

Example:

```text
document-read

Version 1
    alice can read report-123

Version 2
    alice and bob can read report-123
```

The latest version is explicitly retrievable:

```text
get_latest("document-read")
    |
    v
Version 2
```

A historical version can also be retrieved:

```text
get_version("document-read", 1)
    |
    v
Version 1
```

The complete version history can be retrieved:

```text
list_versions("document-read")
    |
    +-- Version 1
    +-- Version 2
```

## 30.3 Sequential Versioning

Policy versions must be created sequentially.

For example:

```text
Version 1
   |
   v
Version 2
   |
   v
Version 3
```

Attempting to create version 3 when version 2 does not exist is rejected.

Example evidence:

```text
ValueError: Policy versions must be sequential
```

This prevents gaps in the policy history and keeps the version sequence deterministic.

## 30.4 Audit Event Model

Policy lifecycle events are represented by `AuditEvent`.

The event contains:

```text
policy_id
version
action
actor
timestamp
```

Example:

```python
AuditEvent(
    "document-read",
    2,
    "policy_created",
    "admin",
    timestamp,
)
```

This provides the minimum information required to answer:

```text
What policy changed?
Which version?
What happened?
Who performed the action?
When did it happen?
```

## 30.5 Audit Store

`AuditStore` records policy lifecycle events.

It supports:

```text
record()
list_events()
list_policy_events()
```

Example audit history:

```text
document-read
    |
    +-- Version 1
    |     action: policy_created
    |     actor: admin
    |
    +-- Version 2
          action: policy_created
          actor: security-admin
```

Policy-specific audit history can be retrieved independently:

```text
list_policy_events("document-read")
```

This keeps the audit trail queryable by policy.

## 30.6 Policy Manager

`PolicyManager` coordinates policy version creation and auditing.

Architecture:

```text
                PolicyManager
                      |
          +-----------+-----------+
          |                       |
          v                       v
 VersionedPolicyStore         AuditStore
          |                       |
          v                       v
 Policy Versions              Audit Events
```

When a new policy version is created:

```text
Create policy version
        |
        v
Determine next version
        |
        v
Create PolicyVersion
        |
        +--------------------+
        |                    |
        v                    v
Policy Store             Audit Store
        |                    |
        v                    v
Persist version         Record event
```

The manager therefore provides a single coordination point for policy creation and its corresponding audit event.

## 30.7 Creating Policy Versions

Example:

```python
from authorization_engine.policy_manager import PolicyManager
from authorization_engine.policy_store import VersionedPolicyStore
from authorization_engine.audit_store import AuditStore

manager = PolicyManager(
    VersionedPolicyStore(),
    AuditStore(),
)

p1 = manager.create_version(
    "document-read",
    "alice can read report-123",
    "admin",
)

p2 = manager.create_version(
    "document-read",
    "alice and bob can read report-123",
    "security-admin",
)
```

The resulting state is:

```text
document-read

v1:
alice can read report-123
created_by: admin

v2:
alice and bob can read report-123
created_by: security-admin
```

The latest policy is version 2.

## 30.8 Historical Version Retrieval

Historical versions remain available after newer versions are created.

Example:

```python
manager.policy_store.get_version(
    "document-read",
    1,
)
```

returns the original version rather than the current version.

This is important for:

- policy investigation
- compliance review
- change analysis
- incident response
- rollback preparation

## 30.9 Rollback Semantics

Rollback is implemented as **creation of a new version from a historical version**, rather than destructive replacement of the current version.

Example:

```text
Version 1
alice can read report-123

Version 2
alice and bob can read report-123

Rollback to Version 1

Version 3
alice can read report-123
```

The history therefore remains:

```text
v1 → v2 → v3
```

rather than deleting version 2.

This is an important policy-governance property because historical state remains auditable.

The rollback actor is recorded as the creator of the new version.

## 30.10 Audit Evidence

Example policy history:

```text
Policy: document-read

Version 1
  Rule: alice can read report-123
  Actor: admin
  Action: policy_created

Version 2
  Rule: alice and bob can read report-123
  Actor: security-admin
  Action: policy_created
```

Example audit records:

```text
AuditEvent(
    policy_id='document-read',
    version=1,
    action='policy_created',
    actor='admin',
    timestamp=...
)

AuditEvent(
    policy_id='document-read',
    version=2,
    action='policy_created',
    actor='security-admin',
    timestamp=...
)
```

This provides concrete evidence that policy changes are associated with both a version and an actor.

## 30.11 Project Structure

The policy versioning and audit implementation adds:

```text
authorization-engine/
│
├── src/
│   └── authorization_engine/
│       ├── audit_models.py
│       ├── audit_store.py
│       ├── policy_manager.py
│       ├── policy_models.py
│       └── policy_store.py
│
└── tests/
    ├── test_audit_store.py
    ├── test_policy_manager.py
    └── test_policy_store.py
```

Existing RBAC, ABAC, and ReBAC files remain part of the project.

## 30.12 Test Coverage

The policy versioning implementation is covered by dedicated automated tests.

Current project-wide verification after implementing this feature:

```text
collected 53 items

tests/test_abac.py .........
tests/test_audit_store.py .....
tests/test_policy_manager.py ........
tests/test_policy_store.py ...........
tests/test_rbac.py .........
tests/test_rebac.py .............

53 passed
```

The dedicated test suites verify:

```text
✓ Policy version creation
✓ Sequential version enforcement
✓ Latest version retrieval
✓ Historical version retrieval
✓ Version history listing
✓ Missing policy handling
✓ Audit event creation
✓ Audit event recording
✓ Policy-specific audit history
✓ Policy manager integration
✓ Rollback from historical version
✓ Rollback creates a new version
✓ Existing RBAC behavior remains passing
✓ Existing ABAC behavior remains passing
✓ Existing ReBAC behavior remains passing
```

The final project-wide evidence is:

```text
53 passed in 0.13s
```

## 30.13 Manual Verification Evidence

Policy version creation was manually verified with:

```powershell
python -c "from authorization_engine.policy_models import PolicyVersion; from authorization_engine.policy_store import VersionedPolicyStore; from datetime import datetime, timezone; store=VersionedPolicyStore(); now=datetime.now(timezone.utc); store.add_version(PolicyVersion('document-read',1,'alice can read report-123',now,'admin')); store.add_version(PolicyVersion('document-read',2,'alice and bob can read report-123',now,'admin')); print('latest:',store.get_latest('document-read')); print('v1:',store.get_version('document-read',1)); print('versions:',store.list_versions('document-read'))"
```

Observed result:

```text
latest: PolicyVersion(... version=2 ...)
v1: PolicyVersion(... version=1 ...)
versions: [PolicyVersion(... version=1 ...), PolicyVersion(... version=2 ...)]
```

Sequential version enforcement was also verified. Attempting to add version 3 immediately after version 1 produced:

```text
ValueError: Policy versions must be sequential
```

Audit recording was manually verified:

```text
all:
[
  AuditEvent(... version=1, action='policy_created', actor='admin' ...),
  AuditEvent(... version=2, action='policy_created', actor='admin' ...)
]

policy:
[
  AuditEvent(... version=1, action='policy_created', actor='admin' ...),
  AuditEvent(... version=2, action='policy_created', actor='admin' ...)
]
```

Policy manager integration was also verified:

```text
latest:
PolicyVersion(
    policy_id='document-read',
    version=2,
    rule='alice and bob can read report-123',
    ...
    created_by='security-admin'
)

audit:
[
    AuditEvent(... version=1, action='policy_created', actor='admin' ...),
    AuditEvent(... version=2, action='policy_created', actor='security-admin' ...)
]
```

Rollback was tested to ensure that restoring an historical policy creates a new version rather than overwriting history.

## 30.14 Policy Governance Model

The implementation now supports the following lifecycle:

```text
Policy Author
     |
     v
Create Version
     |
     v
Versioned Policy Store
     |
     +------------------+
     |                  |
     v                  v
Current Version      Historical Versions
     |
     v
Authorization / Policy Evaluation
     |
     v
Audit Trail
     |
     v
Investigation / Compliance / Rollback
```

The important architectural property is that **policy history is append-oriented**.

A historical version is not silently overwritten.

Instead:

```text
Current v2
   |
   | rollback to v1
   v
New v3 containing v1 rule
```

This preserves the audit history:

```text
v1 → v2 → v3
```

## 30.15 Security and IAM Significance

Policy versioning and audit logging are important capabilities in enterprise authorization systems.

Versioning provides:

- traceability of policy changes
- historical reconstruction
- controlled rollback
- deterministic policy state
- easier incident investigation

Audit events provide:

- actor attribution
- timestamped change history
- policy/version correlation
- evidence for security review
- a foundation for compliance controls

Together they move the project beyond a simple authorization evaluator toward a more realistic **policy management architecture**.

## 30.16 Deliverable Status

| Item | Status |
|---|---|
| Policy version model | Complete |
| Versioned policy store | Complete |
| Sequential version enforcement | Complete |
| Latest policy retrieval | Complete |
| Historical policy retrieval | Complete |
| Policy version listing | Complete |
| Audit event model | Complete |
| Audit event store | Complete |
| Policy manager | Complete |
| Policy creation auditing | Complete |
| Historical rollback | Complete |
| Rollback as new version | Complete |
| Dedicated automated tests | Complete |
| Full regression suite | **53 passed** |
| Policy versioning and audit trail | **Complete** |

## 30.17 Interview Explanation

A concise explanation of this extension:

> I extended the authorization engine with a versioned policy store and an audit trail. Each policy has an immutable, sequential version history containing the policy rule, creator, and timestamp. Policy lifecycle events are recorded as audit events tied to the policy version and actor. I also implemented rollback by creating a new version from a historical version instead of overwriting history. The feature is covered by dedicated pytest tests and the complete authorization-engine regression suite passes.

## 30.18 Architecture Interview Questions

### Q1. Why version policies?

Policy changes affect authorization behavior, so historical policy state needs to be reconstructable for investigation, compliance, and rollback.

### Q2. Why not overwrite the current policy?

Overwriting destroys historical state. Versioning preserves the complete change history.

### Q3. Why must versions be sequential?

Sequential versions provide a deterministic and gap-free policy history and prevent accidental version jumps.

### Q4. How does rollback work?

Rollback retrieves the historical version and creates a new current version containing the historical rule.

```text
v1 → v2 → rollback(v1) → v3
```

### Q5. What does the audit trail record?

At minimum:

```text
policy
version
action
actor
timestamp
```

### Q6. Why separate the policy store and audit store?

They represent different concerns:

```text
PolicyStore → policy state and history
AuditStore  → security/event history
```

Separating them makes the design easier to evolve toward durable storage, centralized logging, or an event-driven architecture.

---

# 31. Current Authorization Engine Evolution

The project has now evolved beyond the original RBAC-only implementation:

```text
RBAC
  |
  +-- Role-based authorization
  |
  v
ABAC
  |
  +-- Attribute/context-based authorization
  |
  v
ReBAC
  |
  +-- Relationship-based authorization
  |
  v
Policy Management
  |
  +-- Versioned policies
  +-- Historical versions
  +-- Rollback
  |
  v
Audit
  |
  +-- Policy lifecycle events
  +-- Actor attribution
  +-- Timestamped history
```

The architecture now demonstrates multiple major authorization models plus policy lifecycle governance.

## Current Build Evidence

```text
RBAC tests:                 9 passed
ABAC tests:                 7 passed
ReBAC tests:               13 passed
Audit store tests:          5 passed
Policy manager tests:       8 passed
Policy store tests:        11 passed
                            -----------
Total:                     53 passed
```

Final verification:

```powershell
pytest
```

Expected/current result for this completed build:

```text
53 passed in 0.13s
```

---

# 32. Updated Project Structure

The current implementation is:

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
│       ├── engine.py
│       ├── abac_models.py
│       ├── abac_engine.py
│       ├── rebac_models.py
│       ├── rebac_store.py
│       ├── rebac_engine.py
│       ├── policy_models.py
│       ├── policy_store.py
│       ├── audit_models.py
│       ├── audit_store.py
│       └── policy_manager.py
│
├── tests/
│   ├── test_rbac.py
│   ├── test_abac.py
│   ├── test_rebac.py
│   ├── test_policy_store.py
│   ├── test_audit_store.py
│   └── test_policy_manager.py
│
└── pyproject.toml
```

This structure reflects the current implementation rather than the original RBAC-only v0.1 structure.

---

# 33. Overall Project Status

```text
┌───────────────────────────────────────────────┐
│         AUTHORIZATION ENGINE                  │
├───────────────────────────────────────────────┤
│                                               │
│  RBAC                         COMPLETE        │
│  ABAC                         COMPLETE        │
│  ReBAC                        COMPLETE        │
│  Policy Versioning            COMPLETE        │
│  Audit Trail                  COMPLETE        │
│  Historical Rollback          COMPLETE        │
│                                               │
│  Automated Tests:             53 passed       │
│                                               │
│  STATUS: BUILD COMPLETE                      │
│                                               │
└───────────────────────────────────────────────┘
```

The project now provides a compact implementation demonstrating:

```text
Authorization Models
        |
        +-- RBAC
        +-- ABAC
        +-- ReBAC
        |
        v
Policy Management
        |
        +-- Versioning
        +-- Historical state
        +-- Rollback
        |
        v
Security Governance
        |
        +-- Audit trail
        +-- Actor attribution
        +-- Timestamped events
```
---

# 34. Failure-Mode Security Testing

The authorization engine has been extended with a dedicated failure-mode security lab covering **fail-open behavior, fail-closed behavior, stale policy detection, and stale-policy protection**.

This work focuses on an important authorization-engineering principle:

> Authorization security depends not only on the policy decision, but also on what happens when policy state is unavailable or no longer current.

## 34.1 Failure-Mode Scope

The lab covers:

```text
Policy unavailable
        |
        +-- Fail-open  -> ALLOW  (security risk)
        |
        +-- Fail-closed -> DENY  (secure default)

Policy stale
        |
        +-- Cached policy may produce obsolete ALLOW
        |
        +-- Staleness detection
        |
        +-- Stale policy -> DENY
```

The failure-mode implementation is isolated from the existing RBAC, ABAC, ReBAC, policy-store, policy-manager, and audit-store implementations.

## 34.2 Project Components

The lab adds:

```text
src/
└── authorization_engine/
    ├── failure_modes.py
    └── stale_policy.py

tests/
├── test_failure_modes.py
└── test_stale_policy.py

docs/
└── failure-modes.md
```

### `failure_modes.py`

Provides:

```text
PolicyUnavailableError
authorize_fail_open()
authorize_fail_closed()
```

`PolicyUnavailableError` distinguishes a policy-source failure from a normal policy DENY.

### `stale_policy.py`

Provides:

```text
SimplePolicy
authorize_with_policy()
is_policy_stale()
authorize_with_stale_policy_protection()
```

The policy contains a version number and the set of users it allows.

---

## 34.3 Fail-Open Scenario

A fail-open authorization path returns ALLOW when the policy source is unavailable.

```text
Policy unavailable
       |
       v
   FAIL OPEN
       |
       v
     ALLOW
```

This is security-sensitive because an infrastructure failure can become an access-control failure.

The lab verifies:

```text
Policy ALLOW       -> ALLOW
Policy DENY        -> DENY
Policy unavailable -> ALLOW
```

The third behavior is intentionally demonstrated as the unsafe fail-open condition.

---

## 34.4 Fail-Closed Scenario

A fail-closed authorization path returns DENY when the policy source is unavailable.

```text
Policy unavailable
       |
       v
  FAIL CLOSED
       |
       v
      DENY
```

The lab verifies:

```text
Policy ALLOW       -> ALLOW
Policy DENY        -> DENY
Policy unavailable -> DENY
```

This provides the safer authorization default because access is not granted when the applicable policy cannot be established.

---

## 34.5 Stale Policy Scenario

The lab models two policy versions:

```text
Policy v1:
    alice -> ALLOW
    bob   -> ALLOW

Policy v2:
    alice -> ALLOW
    bob   -> DENY
```

Version 2 represents the current policy after Bob's access has been removed.

If an authorization request uses cached policy version 1 after version 2 becomes current:

```text
Current policy: v2
Bob should be:  DENY

Cached policy:  v1
Bob receives:   ALLOW
```

Therefore, stale authorization state can produce an obsolete authorization decision.

The tests explicitly demonstrate:

```text
v1 + bob -> True
v2 + bob -> False
```

This proves that the same authorization request can produce different decisions depending on the policy version used.

---

## 34.6 Stale Policy Detection

The lab treats a cached policy as stale when:

```text
cached_policy.version < current_version
```

Example:

```text
Cached version:  1
Current version: 2
                 |
                 v
              STALE
```

The implementation provides:

```python
is_policy_stale(
    cached_policy,
    current_version,
)
```

The tests verify that:

- version 1 is stale when version 2 is current;
- version 2 is not stale when version 2 is current.

---

## 34.7 Stale-Policy Protection

Detecting stale policy state is not sufficient. The authorization layer must define the behavior after staleness is detected.

The protection flow is:

```text
             Check policy version
                     |
              +------+------+
              |             |
            STALE        CURRENT
              |             |
              v             v
            DENY       Evaluate policy
                            |
                       +----+----+
                       |         |
                     ALLOW      DENY
```

The lab implements:

```python
authorize_with_stale_policy_protection(
    policy,
    user,
    current_version,
)
```

When the supplied policy is stale, the function returns `False` immediately.

This means that even if a stale policy would have allowed the user, the authorization layer refuses to use that obsolete decision.

### Security property

```text
Stale policy
     +
Potentially permissive cached decision
     |
     v
   DENY
```

This establishes a deny-by-default response to stale authorization state.

---

## 34.8 Security Findings

### Finding 1 — Fail-open authorization is unsafe during policy-source failure

If policy retrieval fails and authorization defaults to ALLOW, an infrastructure failure can result in unauthorized access.

**Risk:** Access may be granted without a successful policy evaluation.

**Preferred posture:** Fail closed.

### Finding 2 — Stale policy can preserve revoked access

A cached policy can continue granting access after a newer policy version has revoked that access.

**Risk:** Revoked permissions may remain effective until stale policy state is refreshed or invalidated.

**Preferred posture:** Detect policy-version mismatch and reject authorization using stale state.

### Finding 3 — Policy freshness is part of authorization correctness

Authorization correctness depends not only on evaluating a policy but also on evaluating the correct policy version.

**Security implication:** Policy availability and freshness are security properties of the authorization system.

---

## 34.9 Recommended Controls

A production authorization system should consider:

1. **Fail closed when policy evaluation cannot be trusted.**
2. **Track policy versions or revisions.**
3. **Detect cached-policy version mismatches.**
4. **Reject authorization requests when required policy state is stale.**
5. **Invalidate or refresh authorization caches after policy changes.**
6. **Record policy version information in authorization/audit events where appropriate.**
7. **Monitor policy-store availability and cache freshness.**
8. **Define explicit operational behavior for policy-store outages rather than relying on implicit defaults.**

The exact implementation should depend on the consistency, availability, and latency requirements of the production authorization architecture.

---

## 34.10 Failure-Mode Test Evidence

### Fail-open / Fail-closed

Command:

```powershell
pytest tests/test_failure_modes.py
```

Result:

```text
6 passed in 0.05s
```

The six tests cover:

```text
✓ Fail-open preserves ALLOW
✓ Fail-open preserves DENY
✓ Fail-open allows when policy is unavailable
✓ Fail-closed preserves ALLOW
✓ Fail-closed preserves DENY
✓ Fail-closed denies when policy is unavailable
```

### Stale Policy

Command:

```powershell
pytest tests/test_stale_policy.py
```

Result:

```text
9 passed in 0.06s
```

The nine tests cover:

```text
✓ Current policy behavior
✓ Stale policy behavior
✓ Different decisions between stale and current policy
✓ Stale-version detection
✓ Current-version validation
✓ Stale-policy protection
✓ Current-policy ALLOW
✓ Current-policy DENY
✓ Protection against an otherwise-permissive stale policy
```

---

## 34.11 Full Regression Evidence

After adding the failure-mode lab, the complete project test suite was executed:

```powershell
pytest
```

Result:

```text
collected 68 items

68 passed in 0.16s
```

Current test distribution:

| Area | Tests |
|---|---:|
| RBAC | 9 |
| ABAC | 7 |
| ReBAC | 13 |
| Policy Store | 11 |
| Policy Manager | 8 |
| Audit Store | 5 |
| Fail-open / Fail-closed | 6 |
| Stale Policy | 9 |
| **Total** | **68** |

This confirms that the failure-mode security lab was added without causing regressions in the existing authorization-engine functionality.

---

## 34.12 Architecture Implication

The authorization architecture now needs to consider policy availability and freshness in addition to normal authorization evaluation.

```text
                Policy Store
                     |
                     v
              Policy Version
                     |
                     v
               Policy Cache
                     |
              freshness check
                     |
          +----------+----------+
          |                     |
        STALE                 CURRENT
          |                     |
          v                     v
        DENY              Policy evaluation
                                |
                         +------+------+
                         |             |
                         v             v
                       ALLOW          DENY
```

This extends the authorization model from:

```text
Subject → Policy → Decision
```

to a more realistic operational model:

```text
Policy State
     |
     +-- Availability
     |
     +-- Version
     |
     +-- Freshness
     |
     v
Authorization Decision
```

---

## 34.13 Relationship to Existing Policy Versioning and Audit

The failure-mode lab builds directly on the project's existing policy-versioning capability.

Policy versioning provides historical policy state:

```text
v1 → v2 → v3
```

The stale-policy lab adds the runtime security question:

```text
Is the policy being used current?
```

Together:

```text
Policy Management
      |
      +-- Version history
      +-- Historical retrieval
      +-- Rollback
      |
      v
Authorization Runtime
      |
      +-- Policy freshness
      +-- Stale-policy detection
      +-- Fail-closed behavior
      |
      v
Secure Authorization Decision
```

The audit trail can provide additional evidence of policy changes, while the failure-mode controls address what happens when runtime authorization state is unavailable or stale.

---

## 34.14 Deliverable Status

| Item | Status |
|---|---|
| Fail-open behavior test | Complete |
| Fail-closed behavior test | Complete |
| Policy-unavailable scenario | Complete |
| Stale policy scenario | Complete |
| Policy-version staleness detection | Complete |
| Stale-policy protection | Complete |
| Failure-mode test suite | Complete |
| Failure-mode documentation | Complete |
| Full regression verification | **68 passed** |
| Failure-mode security lab | **Complete** |

Detailed evidence is available in:

```text
docs/failure-modes.md
```

---

## 34.15 Interview Explanation

A concise explanation of this security lab:

> I tested authorization failure semantics for policy-store outages and stale policy state. I demonstrated that fail-open behavior can turn policy unavailability into an ALLOW decision, while fail-closed behavior safely returns DENY. I then modeled versioned policies where a stale cached policy could continue granting access after a newer policy revoked it. I added policy-version freshness checks and stale-policy protection so obsolete policy state results in DENY. The complete project regression suite passes with 68 tests.

---

## 34.16 Current Build Evidence

The project now has automated evidence covering:

```text
RBAC
  └── Role-based authorization

ABAC
  └── Attribute/context-based authorization

ReBAC
  └── Relationship-based authorization

Policy Management
  ├── Versioned policies
  ├── Historical versions
  └── Rollback

Audit
  ├── Policy lifecycle events
  ├── Actor attribution
  └── Timestamped history

Failure Modes
  ├── Fail-open behavior
  ├── Fail-closed behavior
  ├── Policy unavailability
  ├── Stale policy detection
  └── Stale-policy protection
```

Final verification:

```text
68 / 68 tests passed
```

This represents the current verified state of the authorization-engine project.
