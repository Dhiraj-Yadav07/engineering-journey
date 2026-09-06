# Simplified Zanzibar-Inspired Authorization Data Model

## 1. Design Principle

Model authorization as **relationships between objects and subjects**, rather than as a flat user-to-role-to-permission table.

The core tuple is:

```text
<object>#<relation>@<subject>
```

Examples:

```text
folder:engineering#viewer@user:alice
group:eng#member@user:alice
document:design#parent@folder:engineering
document:design#viewer@group:eng#member
```

For this project, the subject portion can be either a concrete user or a userset reference.

---

## 2. Object Types

Object types define the nouns in the authorization graph.

Example types:

```text
user
group
folder
document
organization
```

An object is represented as:

```text
<type>:<id>
```

Examples:

```text
user:alice
group:engineering
folder:finance
document:budget-2026
```

---

## 3. Relations

A relation describes what an object relationship means.

Examples:

```text
member
owner
editor
viewer
parent
manager
```

A relation should describe a **relationship**, not an implementation-specific action.

For example:

```text
document:123#viewer
```

is preferable to storing:

```text
document:123#read_permission
```

because the effective viewer set can be derived from several relationships.

---

## 4. Tuple Schema

Logical tuple schema:

| Field | Example | Meaning |
|---|---|---|
| `object_type` | `document` | Object namespace/type |
| `object_id` | `design` | Specific object |
| `relation` | `viewer` | Relationship name |
| `subject_type` | `group` | user / group / object-set |
| `subject_id` | `engineering` | Referenced subject |
| `subject_relation` | `member` | Optional userset relation |
| `version` | `1052` | Version in which tuple became effective |
| `created_at` | timestamp | Audit metadata |
| `deleted_at` | timestamp/null | Version/time of removal |

Canonical representation:

```text
Tuple(
    object = document:design,
    relation = viewer,
    subject = group:engineering#member,
    version = 1052
)
```

---

## 5. Userset

A userset is:

```text
<object>#<relation>
```

Example:

```text
group:engineering#member
```

It means:

> the set of users who satisfy the `member` relation on `group:engineering`.

This lets one tuple refer to an entire group instead of writing one tuple per user/object relationship.

---

## 6. Example Relationship Graph

Consider:

```text
user:alice
    |
    | member
    v
group:engineering
    |
    | viewer
    v
folder:engineering-docs
    |
    | parent
    v
document:design
```

Stored relationships might be:

```text
group:engineering#member@user:alice
folder:engineering-docs#viewer@group:engineering#member
document:design#parent@folder:engineering-docs
```

The check:

```text
Check(user:alice, document:design, viewer)
```

can traverse the graph to determine whether Alice is an effective viewer.

---

## 7. Namespace / Type Definition

Each object type has a small schema describing relations and rewrite rules.

Example:

```yaml
namespace: group
relations:
  - member
```

```yaml
namespace: folder
relations:
  - owner
  - viewer
```

```yaml
namespace: document
relations:
  - owner
  - editor
  - viewer
  - parent
rules:
  viewer:
    union:
      - direct_viewer
      - editor
      - owner
```

A more explicit model could define:

```text
viewer = direct_viewer UNION editor UNION owner
editor = direct_editor UNION owner
```

The exact syntax is an implementation choice. The architectural idea is that **stored relationships and derived relations are separate**.

---

## 8. Userset Rewrite Operators

### Union

```text
viewer = owner UNION editor
```

A user is a viewer when either relation grants access.

### Intersection

```text
allowed = employee INTERSECTION finance_member
```

The user must belong to both sets.

### Exclusion

```text
allowed = viewer EXCEPT suspended
```

The user is allowed only if they are a viewer and not suspended.

These operators allow relationship expressions to behave like set algebra.

---

## 9. Direct vs Derived Relationships

### Direct

```text
document:design#viewer@user:alice
```

Alice is explicitly a viewer.

### Group-derived

```text
group:engineering#member@user:alice
document:design#viewer@group:engineering#member
```

Alice becomes a viewer through the group.

### Hierarchical

```text
document:design#parent@folder:engineering-docs
folder:engineering-docs#viewer@group:engineering#member
```

The document can inherit access from its parent folder according to namespace rules.

---

## 10. Authorization Check Algorithm

Conceptual recursive evaluator:

```text
check(subject, object, relation, snapshot):

    1. Load relation definition for object type.

    2. Find direct tuples for object#relation at snapshot.

    3. If subject matches a direct tuple:
           return ALLOW

    4. Expand any referenced usersets.

    5. Recursively evaluate referenced relations.

    6. Apply UNION / INTERSECTION / EXCLUSION rules.

    7. Return ALLOW only when the expression evaluates true.

    8. Otherwise return DENY.
```

Implementation safeguards:

```text
visited-check set
maximum recursion depth
maximum fan-out
sub-check memoization
```

These prevent graph cycles and runaway evaluation cost.

---

## 11. Snapshot / Version Model

Every mutation produces a version.

Example:

```text
1000: Alice is viewer
1001: Bob is viewer
1002: Bob removed
```

A tuple is visible according to its validity interval.

Conceptually:

```text
start_version <= snapshot_version
AND
(snapshot_version < end_version OR end_version IS NULL)
```

This allows the evaluator to answer:

```text
What was true at snapshot 1002?
```

or:

```text
What is true at least as fresh as token 1002?
```

---

## 12. Consistency Token

Return an opaque token from writes and checks:

```json
{
  "snapshot": 1052
}
```

In the real system this should be opaque to clients; this JSON is only a conceptual representation.

API example:

```text
Write(tuple) -> { token: T1052 }
```

Later:

```text
Check(..., consistency_token=T1052)
```

Semantics:

```text
selected_snapshot >= 1052
```

The evaluator may choose a newer snapshot.

---

## 13. Relational Storage Model for v1

A simple SQL model can be:

### `tuples`

```sql
CREATE TABLE tuples (
    id BIGINT PRIMARY KEY,
    object_type TEXT NOT NULL,
    object_id TEXT NOT NULL,
    relation TEXT NOT NULL,
    subject_type TEXT NOT NULL,
    subject_id TEXT NOT NULL,
    subject_relation TEXT NULL,
    valid_from BIGINT NOT NULL,
    valid_to BIGINT NULL
);
```

Suggested index:

```sql
CREATE INDEX idx_tuple_lookup
ON tuples(object_type, object_id, relation);
```

Suggested index for subject-driven lookups:

```sql
CREATE INDEX idx_subject_lookup
ON tuples(subject_type, subject_id, relation);
```

For a production-scale implementation, the physical storage and partitioning strategy would need workload-specific design.

---

## 14. Namespace Tables

Conceptually:

### `namespaces`

```text
namespace_id
name
version
configuration
```

The configuration contains relation definitions and rewrite rules.

An implementation can store the configuration as JSON initially, then evolve toward a typed representation or compiled policy graph.

---

## 15. Change Log Schema

A simple change log:

```text
change_id
version
operation
object_type
object_id
relation
subject_type
subject_id
subject_relation
created_at
```

Example:

```text
1052 | REMOVE | document | design | viewer | user | bob | null
```

Consumers can maintain:

```text
cache invalidation
regional replicas
graph indexes
audit views
```

---

## 16. Cache Key

A safe logical cache key is:

```text
(subject,
 resource,
 relation,
 tenant/context,
 snapshot_version)
```

Example:

```text
user:alice |
document:design |
viewer |
engineering |
1052
```

Do **not** reuse a cached ALLOW from an older snapshot for a request that requires a newer snapshot.

---

## 17. Data Lifecycle

```text
Client
  |
  v
Write tuple
  |
  v
Validate
  |
  v
Assign version V
  |
  +------> Tuple Store
  |
  +------> Change Log
  |
  +------> Invalidation / replication pipeline
  |
  v
Return consistency token V
```

For a later regional architecture:

```text
Authoritative tuple state
        |
        v
ordered change stream
        |
   +----+----+
   |    |    |
   v    v    v
 R1    R2    R3
```

---

## 18. Example End-to-End Dataset

### Users

```text
user:alice
user:bob
user:carol
```

### Groups

```text
group:engineering
group:security
```

### Relationships

```text
group:engineering#member@user:alice
group:engineering#member@user:bob
group:security#member@user:carol
```

### Resources

```text
folder:eng-docs
document:architecture
```

### Resource relationships

```text
folder:eng-docs#viewer@group:engineering#member
document:architecture#parent@folder:eng-docs
document:architecture#owner@user:carol
```

### Expected checks

```text
Check(alice, document:architecture, viewer) -> ALLOW
Check(bob,   document:architecture, viewer) -> ALLOW
Check(carol, document:architecture, viewer) -> ALLOW
Check(bob,   document:architecture, owner)  -> DENY
```

The first three demonstrate different paths to effective viewer access; the last demonstrates that viewer and owner are distinct relations.

---

## 19. Relation Tuple vs RBAC Mapping

### Traditional RBAC

```text
alice -> developer -> reports:read
```

### Zanzibar-inspired

```text
alice -> engineering#member -> document#viewer
```

RBAC is role-centric.

The Zanzibar-inspired model is **relationship-centric**.

Roles can still be represented as relationships, but the data model does not require every authorization concept to be encoded as a role.

---

## 20. Data-Model Invariants

The implementation should enforce:

1. Object identifiers are non-empty and normalized.
2. Relation names are defined by the object namespace.
3. Referenced namespaces and relations must exist.
4. A tuple cannot reference an invalid userset relation.
5. Writes receive exactly one committed version.
6. Deletes are represented as versioned state transitions, not destructive history erasure.
7. Duplicate active tuples are prevented.
8. Recursive evaluation is bounded.
9. Cache entries are version-aware.
10. Authorization defaults to DENY when the graph cannot be evaluated safely.

---

## 21. Recommended v1 Classes

A clean implementation could use:

```text
Tuple
TupleStore
Namespace
Relation
UsersetExpression
AuthorizationRequest
AuthorizationDecision
ConsistencyToken
CheckEngine
DecisionCache
ChangeEvent
```

Potential module structure:

```text
src/
└── zanzibar_authz/
    ├── api.py
    ├── models.py
    ├── namespace.py
    ├── tuples.py
    ├── store.py
    ├── evaluator.py
    ├── cache.py
    └── changelog.py
```

---

## 22. Interview Summary

The data model can be summarized in one sentence:

> **Authorization is evaluated by traversing typed object-relation-subject tuples and userset expressions against a versioned snapshot of relationship state.**

The three most important entities are:

```text
Object
Relation
Subject / Userset
```

and the three most important runtime concepts are:

```text
Graph traversal
Consistent snapshot
Decision cache
```
