# Failure Analysis — Zanzibar-Inspired Authorizer

## 1. Purpose

This document records the main failure modes considered for the small Zanzibar-inspired authorization prototype.

The goal is not to reproduce Google's production architecture. The goal is to show how authorization correctness can fail and which safeguards the prototype or a production system should use.

## 2. Failure philosophy

For authorization, uncertainty should generally fail closed.

The core rule is:

```text
Cannot prove authorization
        |
        v
      DENY
```

An authorization system should not convert datastore, evaluation, cache, or freshness uncertainty into an accidental `ALLOW`.

---

## 3. Failure scenarios

### 3.1 Unknown object type

Scenario:

```text
Check(user:alice, document:design, viewer)
```

but no `document` namespace exists.

Behavior:

```text
namespace lookup fails
        |
        v
      DENY
```

Reason:

The evaluator cannot safely interpret the requested relation.

Prototype behavior:

```python
if namespace is None:
    return False
```

---

### 3.2 Unknown relation

Scenario:

```text
Check(..., relation="owner")
```

but the namespace does not define `owner`.

Behavior:

The namespace rejects the undefined relation rather than silently inventing semantics.

This prevents configuration errors from becoming accidental permissions.

---

### 3.3 Missing tuple

Scenario:

```text
document:design#viewer@user:alice
```

does not exist.

Behavior:

```text
no matching relationship
        |
        v
      DENY
```

This is the default-deny baseline.

---

### 3.4 Group membership removed

Suppose:

```text
group:engineering#member@user:alice
document:design#viewer@group:engineering#member
```

Initially Alice is authorized.

If the membership relationship is removed, a later authorization check must no longer derive access from that relationship.

The important question is not only:

> Was the tuple removed?

It is:

> At what authorization snapshot should it be considered absent?

That is why snapshot-aware tuple visibility exists in this prototype.

---

### 3.5 Historical snapshot evaluation

Suppose a tuple is valid from version 100 through, but not including, version 105:

```text
valid_from = 100
valid_to   = 105
```

Then:

```text
V=100 -> visible
V=104 -> visible
V=105 -> not visible
```

This boundary is intentional:

```python
valid_from <= snapshot_version < valid_to
```

Off-by-one errors here can create security defects.

---

### 3.6 Recursive relationship cycle

Consider a malformed relationship graph:

```text
A -> B -> C -> A
```

A naive recursive evaluator could loop forever.

The prototype uses a visited set:

```text
(subject, subject_id, object, object_id, relation)
```

Before evaluating a check, the engine tests whether that state has already been visited.

If it has:

```text
cycle detected
       |
       v
     DENY
```

This converts unbounded recursion into a bounded failure.

---

### 3.7 Excessive graph depth

Even without a literal cycle, a deeply nested relationship graph can consume excessive resources.

The prototype has:

```python
MAX_DEPTH = 10
```

When the limit is exceeded:

```text
depth > MAX_DEPTH
       |
       v
     DENY
```

A production service would also consider request timeouts, CPU budgets, query complexity limits, and graph-shape controls.

---

### 3.8 Partial graph evaluation

A production authorization graph can span multiple storage or indexing components.

Example:

```text
document
   |
   v
folder
   |
   v
group
   |
   X
 membership datastore unavailable
```

The engine cannot prove that the user belongs to the group.

Correct behavior:

```text
uncertain relationship
        |
        v
      DENY
```

Never treat an unavailable dependency as evidence of authorization.

---

## 4. Consistency failures

### 4.1 Stale replica returns ALLOW

Suppose:

```text
T0: Alice is a viewer
T1: Alice is removed
```

A stale replica may still contain the old relationship.

If a security-sensitive check reads that stale state, it might return:

```text
ALLOW
```

when the authoritative state should be:

```text
DENY
```

Therefore a production architecture needs an explicit freshness/consistency policy.

Possible approaches include:

- authoritative reads
- minimum snapshot/version requirements
- bounded staleness
- routing fresh-sensitive requests away from stale replicas

---

### 4.2 Stale cached decision

Suppose a cache contains:

```text
Check(Alice, document:design, viewer)
snapshot = 100
result   = ALLOW
```

but the client requires snapshot 105.

A cache keyed only by:

```text
(subject, object, relation)
```

is unsafe.

The prototype's consistency model implies that the relevant logical version must participate in cache validity.

Conceptually:

```text
cache key
=
subject
+ object
+ relation
+ snapshot / freshness context
```

A stale cached `ALLOW` must not be reused for a newer required snapshot without establishing that it remains valid.

---

## 5. Token propagation failure

A consistency token is useful only if the entire graph evaluation respects it.

Bad implementation:

```text
root check at V=105
       |
       v
recursive group check at V=current
```

This mixes two different authorization states.

Correct implementation:

```text
ConsistencyToken(105)
        |
        +--> document check @105
        |
        +--> folder check @105
        |
        +--> group check @105
```

The prototype explicitly propagates one snapshot through recursive evaluation.

---

## 6. Write/read race

A common distributed-systems question is:

```text
Client writes relationship
        |
        v
immediately performs Check
```

Potential problem:

```text
write committed at V=106
        |
        v
read replica only has V=104
```

A read from that replica cannot satisfy a request requiring visibility through V=106.

A production design therefore needs a contract such as:

```text
Write -> returns consistency token V
Check(token=V)
       |
       +-- read from a snapshot >= V
       |
       +-- otherwise wait / route authoritative
```

The current prototype models the consistency token and snapshot semantics but deliberately does not implement distributed replication.

---

## 7. Duplicate tuple writes

The in-memory store avoids inserting the exact same tuple object twice.

Conceptually:

```text
add(T)
add(T)
```

results in one stored tuple rather than two identical entries.

In a production system, idempotency needs to be considered across retries, transactions, request IDs, and distributed storage semantics.

---

## 8. Cache invalidation after relationship mutation

Relationship changes affect authorization results.

Example:

```text
Before:
Alice -> Engineering -> Document
ALLOW

After:
Alice removed from Engineering
DENY
```

A stale decision cache may continue returning `ALLOW`.

This creates the classic authorization cache problem:

```text
mutation
   |
   +--> data state changes
   |
   +--> cached decisions may become invalid
```

A production system needs explicit invalidation or version-aware cache validity rather than relying on time-based expiration alone for security-critical freshness.

---

## 9. Malformed namespace configuration

Bad configuration can define:

- a relation that references an undefined relation
- recursive rewrites with no useful termination
- conflicting or impossible relationship semantics

Production systems should validate namespace configuration before serving traffic.

Useful controls include:

```text
configuration load
      |
      v
schema validation
      |
      v
relation/reference validation
      |
      v
cycle / complexity analysis
      |
      v
activate configuration
```

A fail-safe deployment model should prevent invalid authorization configuration from becoming active.

---

## 10. Resource exhaustion

Authorization checks can become computationally expensive due to:

- deeply nested relationships
- large unions
- repeated subchecks
- adversarial graph shapes
- excessive concurrent requests

The prototype addresses only the most basic controls:

```text
visited set
MAX_DEPTH
```

A production implementation should additionally consider:

```text
request timeout
CPU budget
query budget
fan-out limits
concurrency limits
backpressure
```

---

## 11. Failure matrix

| Failure | Risk | Safe behavior |
|---|---|---|
| Namespace unavailable | Cannot interpret relation | DENY / fail closed |
| Relation undefined | Ambiguous authorization semantics | DENY |
| Tuple missing | No proof of access | DENY |
| Membership datastore unavailable | Cannot prove derived access | DENY |
| Recursive cycle | Infinite evaluation | DENY |
| Max depth exceeded | Resource exhaustion | DENY |
| Stale replica | Old authorization state | Reject/reroute fresh-sensitive check |
| Stale cache | Old ALLOW may survive revocation | Version-aware invalidation/validation |
| Token not propagated | Mixed authorization snapshots | Preserve one snapshot throughout check |
| Write/read lag | Newly committed permission may not be visible | Read at required snapshot or wait |
| Invalid namespace config | Undefined authorization behavior | Reject configuration before activation |

---

## 12. Production evolution

The prototype's failure controls map naturally to a production architecture:

```text
                     +-------------------+
                     | Authorization API |
                     +---------+---------+
                               |
                               v
                     +-------------------+
                     | Consistency /     |
                     | freshness policy  |
                     +---------+---------+
                               |
                               v
                     +-------------------+
                     | Check / Graph     |
                     | Evaluation Engine |
                     +----+---------+----+
                          |         |
                          |         |
                          v         v
                    Tuple Store   Decision Cache
                          |
                          v
                    Change / Watch
                          |
                          v
                     Replicas
```

Each component introduces its own failure mode, so correctness depends on explicit contracts between them.

---

## 13. Interview takeaways

The strongest design points to explain are:

1. **Default deny:** authorization uncertainty should not become an `ALLOW`.
2. **Graph safety:** recursive authorization needs cycle and depth protection.
3. **Consistency is explicit:** a decision should be tied to a defined authorization snapshot/freshness contract.
4. **Cache correctness is semantic:** cache invalidation must respect relationship-version changes, not merely elapsed time.
5. **Scale is separate from semantics:** the core relationship evaluator can remain simple while the production system adds distributed storage, replication, caching, and indexing.

## 14. Scope boundary

This document describes failure behavior for the educational prototype and the production architecture it points toward.

The prototype intentionally does not implement:

- distributed transactions
- multi-region consensus
- replication repair
- production-grade cache invalidation
- global watch infrastructure
- advanced indexing
- operational failover automation

Those are system-design topics to defend in an interview rather than additional code required for this learning artifact.
