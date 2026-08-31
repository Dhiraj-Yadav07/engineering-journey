# ReBAC — Relationship-Based Access Control

## 1. What is ReBAC?

**Relationship-Based Access Control (ReBAC)** is an authorization model where access is determined by the relationship between a subject and a resource.

Instead of asking only:

> "What role does Alice have?"

ReBAC asks:

> "What relationship does Alice have with this particular resource?"

Examples:

- Alice is the **owner** of document `report-123`
- Bob is an **editor** of document `report-123`
- Charlie is a **viewer** of document `report-123`
- Alice belongs to the `engineering` group, and that group has viewer access to a document

This makes ReBAC particularly useful for systems where access depends on resource-specific relationships.

Typical examples include:

- Google Drive / file sharing
- GitHub repositories
- Slack channels
- SaaS multi-tenant applications
- Project-management systems
- Enterprise document management
- Cloud resource sharing

---

## 2. ReBAC vs RBAC vs ABAC

| Model | Authorization based on | Example |
|---|---|---|
| RBAC | Role | Alice is a developer |
| ABAC | Attributes | Alice's department is engineering |
| ReBAC | Relationships | Alice is owner of document X |

### RBAC

RBAC answers:

```text
Does Alice have the required role?
```

Example:

```text
alice -> developer
developer -> reports:read
```

### ABAC

ABAC answers:

```text
Do the subject, resource, and environment attributes satisfy policy?
```

Example:

```text
user.department == resource.department
AND
context.network == "corporate"
```

### ReBAC

ReBAC answers:

```text
Does Alice have a relationship with this specific resource?
```

Example:

```text
alice --owner--> document:report-123
```

The key distinction is **resource-specific relationships**.

---

# 3. Core ReBAC Concepts

A relationship tuple contains:

```text
(subject, relation, resource)
```

Example:

```text
("alice", "owner", "document:report-123")
```

Meaning:

```text
Alice is an owner of document report-123.
```

Another example:

```text
("bob", "editor", "document:report-123")
```

Meaning:

```text
Bob is an editor of document report-123.
```

---

# 4. Relationship Tuples

A relationship tuple contains:

```text
subject
relation
resource
```

Our implementation:

```python
@dataclass(frozen=True)
class RelationshipTuple:
    subject: str
    relation: str
    resource: str
```

Example:

```python
RelationshipTuple(
    "alice",
    "owner",
    "document:report-123",
)
```

This produces:

```text
RelationshipTuple(
    subject='alice',
    relation='owner',
    resource='document:report-123'
)
```

The tuple is immutable because it is defined using:

```python
@dataclass(frozen=True)
```

It is also hashable and can therefore be stored in a Python `set`.

---

# 5. Relationship Store

The relationship store maintains the relationship tuples.

The implementation uses:

```python
self._tuples: set[RelationshipTuple] = set()
```

Relationships can be added:

```python
store.add(
    RelationshipTuple(
        "alice",
        "owner",
        "document:report-123",
    )
)
```

They can be removed:

```python
store.remove(
    RelationshipTuple(
        "alice",
        "owner",
        "document:report-123",
    )
)
```

And queried:

```python
store.exists(
    "alice",
    "owner",
    "document:report-123",
)
```

The result is:

```text
True
```

for an existing relationship and:

```text
False
```

for a missing relationship.

---

# 6. Basic Relationship Examples

Our ReBAC example uses:

```text
alice   -> owner  -> document:report-123
bob     -> editor -> document:report-123
charlie -> viewer -> document:report-123
```

The relationships mean:

### Alice

```text
alice --owner--> document:report-123
```

Owner permissions:

```text
read
write
delete
```

### Bob

```text
bob --editor--> document:report-123
```

Editor permissions:

```text
read
write
```

### Charlie

```text
charlie --viewer--> document:report-123
```

Viewer permissions:

```text
read
```

---

# 7. Relationship-to-Permission Mapping

The ReBAC engine defines:

```python
RELATION_PERMISSIONS = {
    "owner": {"read", "write", "delete"},
    "editor": {"read", "write"},
    "viewer": {"read"},
}
```

Therefore:

| Relationship | read | write | delete |
|---|---:|---:|---:|
| owner | Yes | Yes | Yes |
| editor | Yes | Yes | No |
| viewer | Yes | No | No |

This is the authorization policy for ReBAC v0.1.

---

# 8. Authorization Flow

The authorization flow is:

```text
                Access Request
                      |
                      v
          +-----------------------+
          |   ReBAC Authorization |
          |        Engine         |
          +-----------+-----------+
                      |
                      v
              Check relationships
                      |
                      v
              Relationship Store
                      |
                      v
        subject + relation + resource
                      |
                      v
            Relationship exists?
                 /          \
               No            Yes
               |              |
               v              v
             DENY       Check permission
                              |
                       action allowed?
                         /         \
                       No           Yes
                       |             |
                       v             v
                     DENY          ALLOW
```

The engine therefore separates:

1. **Relationship storage**
2. **Relationship lookup**
3. **Permission mapping**
4. **Authorization decision**

---

# 9. Our Implementation

The ReBAC implementation contains three modules:

```text
src/
└── authorization_engine/
    ├── rebac_models.py
    ├── rebac_store.py
    └── rebac_engine.py
```

Tests:

```text
tests/
├── test_rbac.py
├── test_abac.py
└── test_rebac.py
```

Documentation:

```text
docs/
├── rbac.md
├── abac.md
└── rebac.md
```

---

# 10. `rebac_models.py`

The model defines the relationship tuple.

```python
from dataclasses import dataclass


@dataclass(frozen=True)
class RelationshipTuple:
    subject: str
    relation: str
    resource: str
```

This provides a strongly structured representation of:

```text
subject + relation + resource
```

Example:

```python
RelationshipTuple(
    subject="alice",
    relation="owner",
    resource="document:report-123",
)
```

---

# 11. `rebac_store.py`

The store maintains relationships in memory.

Core structure:

```python
class RelationshipStore:
    def __init__(self):
        self._tuples: set[RelationshipTuple] = set()
```

Adding:

```python
def add(self, relationship: RelationshipTuple) -> None:
    self._tuples.add(relationship)
```

Removing:

```python
def remove(self, relationship: RelationshipTuple) -> None:
    self._tuples.discard(relationship)
```

Checking:

```python
def exists(
    self,
    subject: str,
    relation: str,
    resource: str,
) -> bool:
    relationship = RelationshipTuple(
        subject=subject,
        relation=relation,
        resource=resource,
    )

    return relationship in self._tuples
```

The important property is that the lookup is **resource-specific**.

For example:

```text
alice owner document:report-123
```

does not automatically imply:

```text
alice owner document:other-456
```

---

# 12. `rebac_engine.py`

The engine contains the authorization logic.

Core policy:

```python
RELATION_PERMISSIONS = {
    "owner": {"read", "write", "delete"},
    "editor": {"read", "write"},
    "viewer": {"read"},
}
```

Authorization:

```python
def authorize(
    self,
    subject: str,
    action: str,
    resource: str,
) -> bool:
    for relation, allowed_actions in self.RELATION_PERMISSIONS.items():
        if self.store.exists(subject, relation, resource):
            return action in allowed_actions

    return False
```

The engine:

1. Looks for a relationship.
2. Identifies the relationship type.
3. Gets the actions allowed for that relationship.
4. Checks whether the requested action is allowed.
5. Returns `True` or `False`.

---

# 13. Owner Example

Relationship:

```text
alice --owner--> document:report-123
```

Requests:

```text
alice + read + report-123
alice + write + report-123
alice + delete + report-123
```

Results:

```text
read   -> True
write  -> True
delete -> True
```

Because owners have:

```text
read
write
delete
```

---

# 14. Editor Example

Relationship:

```text
bob --editor--> document:report-123
```

Requests:

```text
bob + read + report-123
bob + write + report-123
bob + delete + report-123
```

Results:

```text
read   -> True
write  -> True
delete -> False
```

Editors can modify the resource but cannot delete it.

---

# 15. Viewer Example

Relationship:

```text
charlie --viewer--> document:report-123
```

Requests:

```text
charlie + read + report-123
charlie + write + report-123
charlie + delete + report-123
```

Results:

```text
read   -> True
write  -> False
delete -> False
```

---

# 16. Unknown User

Suppose:

```text
david
```

has no relationship with:

```text
document:report-123
```

Request:

```text
david + read + document:report-123
```

The store cannot find a matching relationship.

Therefore:

```text
DENY
```

Result:

```text
False
```

---

# 17. Resource-Specific Access

One of the most important ReBAC properties is resource specificity.

Suppose:

```text
alice --owner--> document:report-123
```

Alice can access:

```text
document:report-123
```

But this does not automatically grant access to:

```text
document:other-456
```

Therefore:

```python
engine.authorize(
    "alice",
    "read",
    "document:other-456",
)
```

returns:

```text
False
```

This demonstrates why ReBAC is different from simple global role assignment.

---

# 18. Same User, Different Relationships

A user can have different relationships with different resources.

Example:

```text
alice --owner--> document:report-123
alice --viewer--> document:design-456
```

Therefore:

### report-123

```text
alice -> owner
```

Allows:

```text
read
write
delete
```

### design-456

```text
alice -> viewer
```

Allows:

```text
read
```

So:

```text
alice read design-456   -> True
alice write design-456  -> False
alice delete design-456 -> False
```

This is a fundamental ReBAC capability.

---

# 19. Group-Based Relationships

The implementation was extended to support group membership.

The model includes:

```python
@dataclass(frozen=True)
class GroupMembership:
    subject: str
    group: str
```

Example:

```text
david -> member of -> group:engineering
```

Represented as:

```python
GroupMembership(
    "david",
    "group:engineering",
)
```

The group can then have a relationship with a resource:

```text
group:engineering --viewer--> document:report-123
```

This means members of the group inherit the group's resource access.

---

# 20. Group Authorization Flow

The flow becomes:

```text
                 david
                   |
                   v
          Member of engineering?
                   |
                  Yes
                   |
                   v
          group:engineering
                   |
                   | viewer
                   v
          document:report-123
                   |
                   v
               read allowed
```

Therefore:

```text
david read report-123 -> True
```

But because the group relationship is `viewer`:

```text
david write report-123 -> False
david delete report-123 -> False
```

---

# 21. Group Membership Example

The test scenario:

```python
engine.store.add(
    RelationshipTuple(
        "group:engineering",
        "viewer",
        "document:report-123",
    )
)

engine.store.add_membership(
    GroupMembership(
        "david",
        "group:engineering",
    )
)
```

Then:

```python
assert engine.authorize(
    "david",
    "read",
    "document:report-123",
) is True
```

But:

```python
assert engine.authorize(
    "david",
    "write",
    "document:report-123",
) is False
```

and:

```python
assert engine.authorize(
    "david",
    "delete",
    "document:report-123",
) is False
```

This demonstrates **relationship inheritance through group membership**.

---

# 22. Test Scenarios

The ReBAC test suite contains 13 tests.

Current test coverage includes:

### Owner

```text
owner can read
owner can write
owner can delete
```

### Editor

```text
editor can read
editor can write
editor cannot delete
```

### Viewer

```text
viewer can read
viewer cannot write
viewer cannot delete
```

### Unknown user

```text
unknown user is denied
```

### Resource isolation

```text
relationship is resource specific
```

### Multiple relationships

```text
same user can have different relationships with different resources
```

### Group inheritance

```text
group member inherits resource access
```

---

# 23. Test Evidence

Run:

```powershell
pytest tests/test_rebac.py
```

Expected result:

```text
13 passed
```

Then run the complete authorization-engine test suite:

```powershell
pytest
```

Expected result from the completed lab:

```text
29 passed
```

The complete suite covers:

```text
ABAC:  7 tests
RBAC:  9 tests
ReBAC: 13 tests
----------------
Total: 29 tests
```

---

# 24. Manual ReBAC Demonstration

A manual demonstration can verify owner, editor, viewer, and unknown-user behavior.

Expected output:

```text
alice read: True
alice write: True
alice delete: True
bob read: True
bob write: True
bob delete: False
charlie read: True
charlie write: False
charlie delete: False
unknown read: False
```

---

# 25. Fail-Closed Behavior

The implementation follows a fail-closed authorization model.

If there is no matching relationship:

```python
return False
```

Therefore:

```text
No relationship
      |
      v
    DENY
```

This is preferable to fail-open behavior:

```text
No relationship
      |
      v
    ALLOW
```

Fail-open authorization is dangerous because missing, malformed, or incomplete relationship data could unintentionally grant access.

The ReBAC engine therefore follows the security principle:

> **Access must be explicitly established.**

---

# 26. Security Properties

The implementation demonstrates several important security properties.

## Explicit relationships

Access requires an explicit relationship:

```text
subject -> relation -> resource
```

## Resource isolation

A relationship with one resource does not automatically grant access to another resource.

## Least privilege

Different relationships provide different permissions:

```text
viewer < editor < owner
```

## Default deny

Unknown users are denied.

## Immutable relationship tuples

`RelationshipTuple` is frozen:

```python
@dataclass(frozen=True)
```

This prevents accidental mutation after insertion into the relationship store.

---

# 27. ReBAC Architecture

Current architecture:

```text
                  +--------------------+
                  |   Authorization    |
                  |       Request      |
                  +---------+----------+
                            |
                            v
                  +--------------------+
                  |    ReBAC Engine    |
                  +---------+----------+
                            |
                 +----------+----------+
                 |                     |
                 v                     v
       +------------------+   +------------------+
       | Relationship     |   | Permission       |
       | Store            |   | Mapping          |
       +--------+---------+   +------------------+
                |
                v
       Relationship Tuples
                |
                v
       Subject / Relation /
           Resource
```

Group support adds:

```text
Subject
   |
   v
Group Membership
   |
   v
Group
   |
   v
Relationship Tuple
   |
   v
Resource
```

---

# 28. Why ReBAC Is Powerful

Consider a collaboration platform.

A user may be:

```text
owner of project A
editor of document B
viewer of document C
member of team D
admin of workspace E
```

A global role cannot naturally express all of these resource-specific relationships.

ReBAC can represent them directly.

Example:

```text
alice --owner--> project:payments
alice --editor--> document:architecture
alice --viewer--> document:roadmap
alice --member--> group:security
```

Authorization is evaluated based on the relationship relevant to the requested resource.

---

# 29. Real-World Scenario: Google Drive

A simplified Google Drive relationship model:

```text
alice --owner--> file:report.pdf
bob --editor--> file:report.pdf
charlie --viewer--> file:report.pdf
```

The access model is resource-specific.

Bob being an editor of one file does not make Bob an editor of every file.

---

# 30. Real-World Scenario: GitHub

A repository can have relationships such as:

```text
alice --admin--> repository:payments
bob --maintainer--> repository:payments
charlie --contributor--> repository:payments
david --viewer--> repository:payments
```

Different relationships imply different permissions.

This is naturally modeled as a graph of relationships.

---

# 31. Real-World Scenario: SaaS Multi-Tenancy

Consider:

```text
tenant:acme
    |
    +-- member --> alice
    |
    +-- member --> bob
```

And:

```text
tenant:acme --owns--> project:payments
```

Authorization can then derive access through tenant membership.

This is useful for:

- Tenant isolation
- Project sharing
- Team membership
- Organization membership
- Resource ownership

---

# 32. ReBAC Limitations

The current implementation is intentionally small and educational.

It does not yet provide:

- Persistent storage
- Distributed relationship storage
- Relationship hierarchies
- Arbitrary relationship graphs
- Recursive graph traversal
- Cyclic relationship detection
- Policy versioning
- Audit logging
- Decision explanations
- Caching
- Concurrency controls
- API layer
- Authentication integration
- Multi-tenant isolation
- Policy administration

The in-memory `set` is suitable for demonstrating the authorization model but not for production-scale authorization infrastructure.

---

# 33. Important Limitation in v0.1

The current engine has a simple mapping:

```python
RELATION_PERMISSIONS = {
    "owner": {"read", "write", "delete"},
    "editor": {"read", "write"},
    "viewer": {"read"},
}
```

This means permissions are currently hard-coded.

A production ReBAC system would normally externalize relationship definitions and authorization policy.

For example:

```text
viewer
    -> read

editor
    -> viewer
    -> write

owner
    -> editor
    -> delete
```

This would allow more sophisticated permission inheritance.

---

# 34. Future Improvements

Potential next versions could introduce:

## Relationship inheritance

```text
owner -> editor -> viewer
```

## Nested groups

```text
alice
  |
  v
engineering
  |
  v
platform
  |
  v
organization
```

## Resource hierarchies

```text
organization
      |
      v
    project
      |
      v
   document
```

## Recursive graph evaluation

Instead of checking only direct relationships:

```text
alice -> member -> engineering
engineering -> editor -> project
project -> viewer -> document
```

The engine could traverse the relationship graph.

## Policy configuration

Move authorization policy outside the Python source code.

## Persistent storage

Replace:

```python
set()
```

with a database or dedicated relationship store.

## Caching

Cache frequently evaluated relationship checks.

## Audit logging

Record:

```text
subject
resource
action
relationship
decision
timestamp
```

## Decision explanations

Instead of:

```text
True
```

return:

```text
allowed because alice is an editor of document:report-123
```

This is useful for debugging and auditability.

---

# 35. Production ReBAC Systems

The concepts implemented here are closely related to modern authorization systems such as:

- Google Zanzibar
- OpenFGA
- SpiceDB
- Auth0 Fine-Grained Authorization

These systems model authorization as relationships and graph-based permission evaluation.

The major difference from this lab is scale and sophistication.

Production systems need:

- Distributed storage
- Consistency guarantees
- High availability
- Caching
- Graph traversal
- Policy management
- Observability
- Auditability
- Multi-tenant security

---

# 36. ReBAC vs Zanzibar-Style Authorization

Google Zanzibar popularized the concept of representing authorization using relationship tuples.

Conceptually:

```text
user:alice#owner@document:report-123
```

or equivalently:

```text
subject = alice
relation = owner
resource = document:report-123
```

Our implementation deliberately uses the simpler Python representation:

```python
RelationshipTuple(
    "alice",
    "owner",
    "document:report-123",
)
```

The goal is to understand the underlying authorization model before introducing distributed authorization infrastructure.

---

# 37. Interview Questions

## Q1. What is ReBAC?

ReBAC is an authorization model where permissions are derived from relationships between subjects and resources.

## Q2. How is ReBAC different from RBAC?

RBAC assigns permissions through roles.

ReBAC determines permissions through resource-specific relationships.

Example:

```text
RBAC:
alice -> developer

ReBAC:
alice -> owner -> document:123
```

## Q3. How is ReBAC different from ABAC?

ABAC evaluates attributes.

ReBAC evaluates relationships.

Example:

```text
ABAC:
user.department == resource.department

ReBAC:
alice --editor--> document:123
```

## Q4. What is a relationship tuple?

A relationship tuple represents:

```text
subject + relation + resource
```

Example:

```text
alice + owner + document:123
```

## Q5. Why is the resource included in the tuple?

Because ReBAC is resource-specific.

This:

```text
alice --owner--> document:A
```

must not automatically imply:

```text
alice --owner--> document:B
```

## Q6. What happens when no relationship exists?

The engine denies access.

This is fail-closed behavior:

```python
return False
```

## Q7. Why are relationship tuples immutable?

The implementation uses:

```python
@dataclass(frozen=True)
```

This prevents mutation and allows tuples to safely be stored in a set.

## Q8. How does group-based authorization work?

A user is associated with a group:

```text
david -> member -> engineering
```

The group has a relationship with a resource:

```text
engineering -> viewer -> document:123
```

The user can inherit the group's access.

## Q9. What are the challenges of production ReBAC?

Major challenges include:

- Graph traversal
- Consistency
- Performance
- Caching
- Distributed storage
- Policy management
- Cyclic relationships
- Auditability
- Availability

## Q10. What is Zanzibar?

Zanzibar is Google's large-scale authorization system and a major reference architecture for relationship-based authorization.

It models authorization using relationships between users and resources and evaluates permissions over a relationship graph.

## Q11. Why is ReBAC useful for SaaS?

Because SaaS applications frequently require resource-specific sharing.

For example:

```text
Alice owns project A
Bob edits project A
Charlie views project A
Bob owns project B
```

ReBAC models this naturally.

## Q12. Can ReBAC replace RBAC?

Not necessarily.

In real systems, the models can complement each other.

For example:

```text
RBAC:
user is platform-admin

ReBAC:
user is editor of project X
```

A mature authorization architecture may combine multiple authorization concepts.

---

# 38. Lab Completion Evidence

The ReBAC lab is considered complete when the following are demonstrated:

### Source implementation

```text
src/authorization_engine/
├── rebac_models.py
├── rebac_store.py
└── rebac_engine.py
```

### Tests

```text
tests/test_rebac.py
```

### Test result

```text
13 passed
```

### Full regression test

```text
29 passed
```

### Core capabilities demonstrated

```text
[x] Relationship tuples
[x] Relationship store
[x] Owner access
[x] Editor access
[x] Viewer access
[x] Resource-specific authorization
[x] Unknown-user denial
[x] Multiple relationships
[x] Group membership
[x] Group-inherited access
[x] Fail-closed behavior
```

---

# 39. Final Architecture Across Authorization Labs

The authorization-engine project now demonstrates three authorization models:

```text
authorization-engine
│
├── RBAC
│   ├── Roles
│   ├── Permissions
│   └── Role assignment
│
├── ABAC
│   ├── User attributes
│   ├── Resource attributes
│   ├── Action
│   └── Context attributes
│
└── ReBAC
    ├── Relationship tuples
    ├── Relationship store
    ├── Resource relationships
    └── Group membership
```

Conceptually:

```text
                  Authorization Engine
                          |
          +---------------+---------------+
          |               |               |
          v               v               v
        RBAC            ABAC            ReBAC
          |               |               |
        Role          Attributes      Relationships
          |               |               |
     Permissions       Policy          Resource graph
```

This gives the project a useful progression:

```text
RBAC
  ↓
ABAC
  ↓
ReBAC
```

from simple role-based authorization toward increasingly fine-grained, context-aware, and relationship-aware authorization.

---

# 40. ReBAC v0.1 Summary

The implementation demonstrates the fundamental ReBAC authorization model using:

```text
RelationshipTuple
RelationshipStore
ReBACEngine
```

The engine supports:

```text
owner
editor
viewer
```

and evaluates resource-specific access using relationship tuples.

It also supports group membership and inherited resource access.

The current test evidence is:

```text
13 ReBAC tests passed
29 total authorization tests passed
```

The implementation is intentionally an educational **ReBAC Engine v0.1**, providing the foundation for more advanced relationship graphs, recursive permission evaluation, policy configuration, persistence, and production-grade authorization infrastructure.
