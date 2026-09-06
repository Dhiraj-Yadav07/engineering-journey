# Simplified Zanzibar-Inspired Authorization Service — HLD

## 1. Objective

Design a simplified authorization service inspired by Google's Zanzibar model.

The service must support relationship-based authorization at moderate scale while remaining simple enough to implement as a learning project.

The design focuses on three Zanzibar ideas:

1. **Relationship tuples** instead of only role/permission tables.
2. **Userset-based recursive evaluation** for groups and resource relationships.
3. **Explicit consistency/freshness semantics** so callers can request an authorization decision that is at least as fresh as a previously observed state.

This is intentionally **Zanzibar-inspired, not a production reimplementation of Google Zanzibar**.

---

## 2. Scope

### In scope

- Relation tuple storage
- Namespace/type configuration
- Usersets
- Basic userset rewrites: union, intersection, exclusion
- `Check` API
- `Read` API
- `Write` API
- Versioned tuple state
- Local authorization evaluation
- Read-through caching
- Basic request deduplication
- Regional replicas as a future scale boundary
- Consistency token (`zookie`-like token) in the API model

### Out of scope for v1

- Full Spanner implementation
- Full Leopard-style graph indexing
- Cross-region consensus implementation
- Production-grade sharding
- Multi-tenant billing/quota infrastructure
- Global operational control plane
- Full policy language/compiler

---

## 3. Problem Statement

A normal RBAC engine answers questions such as:

```text
Does Alice have reports:read?
```

A Zanzibar-style system answers relationship questions such as:

```text
Can Alice view document:123?
```

where the answer may depend on a graph:

```text
Alice
  |
  v
Engineering group
  |
  v
Folder viewer
  |
  v
Document viewer
```

The system therefore needs to evaluate **relationships**, not merely look up a single permission.

---

## 4. High-Level Architecture

```text
                              +----------------------+
                              |      Client/App      |
                              +----------+-----------+
                                         |
                                         | Check / Read / Write
                                         v
                              +----------------------+
                              | Authorization API    |
                              +----------+-----------+
                                         |
                           +-------------+-------------+
                           |                           |
                           v                           v
                 +-------------------+       +-------------------+
                 | Decision Cache   |       | Namespace Config  |
                 | + request dedup  |       | / Policy Metadata |
                 +---------+---------+       +---------+---------+
                           |                           |
                           +-------------+-------------+
                                         |
                                         v
                              +----------------------+
                              | Check / Evaluation   |
                              | Engine               |
                              +----+------------+----+
                                   |            |
                         tuple reads|            | recursion
                                   v            v
                         +----------------+  +----------------+
                         | Tuple Store    |  | Userset Graph  |
                         | versioned      |  | traversal      |
                         +-------+--------+  +----------------+
                                 |
                                 v
                         +----------------+
                         | Change Log /   |
                         | Version Stream |
                         +-------+--------+
                                 |
                                 v
                         +----------------+
                         | Replica /      |
                         | Distribution   |
                         | (future v2)    |
                         +----------------+
```

### Core request path

```text
Client
  -> Authorization API
  -> Cache lookup
  -> Evaluation Engine
  -> Tuple Store / graph traversal
  -> ALLOW or DENY
```

For cache hits, the tuple-store path can be skipped.

---

## 5. Core Components

### 5.1 Authorization API

Exposes the public authorization contract.

Primary operations:

```text
Check(subject, resource, relation, consistency_token?)
Read(resource, relation?)
Write(tuple mutations)
```

Responsibilities:

- Validate request format.
- Authenticate the calling service.
- Validate namespace/type names.
- Pass consistency requirements to the evaluator.
- Return decision plus a consistency token.

---

### 5.2 Namespace Configuration Store

Stores the schema for each object type.

Example:

```text
namespace: document
relations:
  owner
  editor
  viewer
```

And rewrite rules such as:

```text
viewer = direct_viewer UNION editor UNION owner
```

A simplified implementation can keep this in a versioned relational/document store.

---

### 5.3 Tuple Store

Stores relationship tuples.

Example:

```text
folder:engineering#viewer@group:eng#member
group:eng#member@alice
document:design#parent@folder:engineering
document:design#viewer@bob
```

Each mutation gets a monotonically increasing logical version or timestamp.

For v1, SQLite/PostgreSQL can be used. The important learning objective is the **data model and evaluation semantics**, not the storage technology.

---

### 5.4 Evaluation Engine

Evaluates a request against a consistent snapshot.

Conceptually:

```text
Check(alice, document:design, viewer)
             |
             v
     load document#viewer rule
             |
             v
      expand referenced usersets
             |
             v
       evaluate graph/set rules
             |
             v
        ALLOW / DENY
```

The engine must:

- Prevent infinite recursion.
- Enforce a maximum traversal depth.
- Deduplicate repeated sub-checks.
- Carry the requested consistency version through recursive calls.
- Default to DENY on evaluation failure.

---

### 5.5 Decision Cache

Caches authorization results.

Suggested logical key:

```text
(subject,
 resource,
 relation,
 tenant,
 context_hash,
 snapshot_version)
```

The snapshot/version component is important: a decision computed for an older snapshot must not automatically satisfy a request that requires a newer snapshot.

For v1, an in-memory LRU cache with TTL is sufficient.

---

### 5.6 Change Log

Every tuple mutation produces a versioned change event:

```text
TupleAdded
TupleRemoved
```

Example:

```text
version=1052
operation=REMOVE
object=document:123
relation=viewer
subject=user:bob
```

The change stream is useful later for:

- cache invalidation,
- replicas,
- graph indexes,
- auditability.

For v1 it can be an append-only table.

---

## 6. Request Flows

### 6.1 Check

```text
Client
  |
  | Check(alice, document:123, viewer)
  v
API
  |
  +--> cache lookup
  |       |
  |       +--> hit -> return decision
  |
  v
Evaluator
  |
  +--> namespace configuration
  |
  +--> tuple reads
  |
  +--> recursive userset checks
  |
  v
Decision
  |
  v
Cache result
  |
  v
Return ALLOW/DENY + consistency token
```

### 6.2 Write

```text
Client
  |
  | add/remove tuple
  v
API
  |
  v
Validate tuple
  |
  v
Transactional write
  |
  +--> increment version
  |
  +--> append change event
  |
  v
Return new consistency token
```

The change event gives downstream components a precise version to process.

---

## 7. Consistency Model

The simplified service uses **versioned snapshots**.

Each successful write produces:

```text
version = V
```

A Check may contain:

```text
consistency_token = V
```

The semantics are:

> Evaluate the request using a snapshot at least as fresh as version V.

The service may choose a newer snapshot.

### Why this matters

Consider:

```text
V100: remove Bob from folder viewers
V101: create new document under the folder
```

A request that must see V101 should also see the earlier removal at V100.

Therefore the evaluator must not combine:

```text
new document from V101
```

with:

```text
old ACL state from before V100
```

This is the simplified version of the consistency idea behind Zanzibar's zookies and snapshot reads.

---

## 8. Failure Behavior

Authorization is security-sensitive.

The default failure posture is:

```text
uncertain state
     |
     v
   DENY
```

Examples:

| Failure | v1 behavior |
|---|---|
| Tuple store unavailable | DENY unless a safely usable cached decision exists |
| Namespace config unavailable | DENY |
| Corrupt tuple | Reject/ignore invalid tuple; log error |
| Recursive cycle | Stop traversal and DENY |
| Max traversal depth exceeded | DENY |
| Cache unavailable | Continue without cache |
| Change-log consumer unavailable | Continue local checks; mark replica/index stale |
| Stale replica beyond configured limit | Reject fresh-sensitive checks or route to authoritative store |

The system must never silently convert an authorization uncertainty into ALLOW.

---

## 9. Scaling Path

### v1 — Single region

```text
API
 |
 +--> cache
 |
 +--> evaluator
       |
       +--> PostgreSQL / SQLite
```

Goal: validate the data model and evaluator.

### v2 — Regional replicas

```text
               Authoritative Store
                       |
                 change stream
            +----------+----------+
            |          |          |
         Region A   Region B   Region C
            |          |          |
         evaluator  evaluator  evaluator
            |          |          |
          cache      cache      cache
```

The authoritative store owns writes. Regional replicas serve most checks.

### v3 — Specialized indexing

For very large or deeply nested groups:

```text
Tuple Store
    |
    +--> graph/index builder
             |
             v
       materialized index
             |
             v
      fast userset checks
```

This is the simplified project analogue of the role played by specialized indexing in Zanzibar. It is not a Leopard reimplementation.

---

## 10. Capacity and Latency Goals for the Learning Project

These are **project targets**, not claims about Google's Zanzibar.

Initial target:

```text
p50 check latency: < 5 ms locally
p95 check latency: < 20 ms locally
p99 check latency: < 50 ms locally
```

A later concurrent benchmark should measure:

```text
10 concurrent clients
50 concurrent clients
100 concurrent clients
```

and report:

```text
p50 / p95 / p99
throughput
error rate
cache hit rate
```

---

## 11. Security and Correctness Principles

1. **Default deny.**
2. **Tuple writes are validated before persistence.**
3. **Authorization checks use an explicit snapshot/version.**
4. **Cache entries are scoped to the snapshot they were computed from.**
5. **Recursive checks have cycle and depth protection.**
6. **Every mutation has an auditable version.**
7. **Freshness requirements are never silently relaxed.**
8. **A stale ALLOW is treated as security-sensitive.**

---

## 12. Observability

Track at minimum:

```text
check_count
allow_count
 deny_count
check_latency_p50
check_latency_p95
check_latency_p99
cache_hit_ratio
cache_miss_ratio
cache_stale_rejections
max_recursion_depth
cycle_detections
store_latency
store_errors
replica_version_lag
```

The most important distributed-system signal is:

```text
replica_version_lag
```

because it directly connects authorization correctness to data propagation.

---

## 13. Key Trade-offs

| Design choice | Benefit | Cost |
|---|---|---|
| Local evaluation | Low latency | Requires local policy state |
| Async replication | Scales reads | Introduces bounded staleness |
| Decision cache | Very low latency | Invalidation/freshness complexity |
| Recursive graph checks | Flexible model | Fan-out and tail latency |
| Specialized index | Fast complex checks | Operational complexity |
| Strong snapshot semantics | Correctness | More coordination/storage complexity |

---

## 14. Interview Defense

### Why not just RBAC?

RBAC maps users to roles. A Zanzibar-style model can express arbitrary relationships such as group membership, nested groups, ownership, and resource hierarchy without creating a new role for every relationship combination.

### Why is consistency special?

Authorization decisions are security decisions. A stale read can produce an incorrect ALLOW after a revocation. The system therefore needs explicit freshness semantics rather than treating all stale reads as harmless.

### Why replicate globally?

Authorization is usually on the request path. Serving checks from a nearby replica reduces latency and avoids forcing every request through a central region.

### Why can this become expensive?

A single relationship check may recursively expand several usersets. The resulting fan-out creates CPU, storage, and tail-latency pressure. Caching, request deduplication, and specialized indexes reduce repeated work.

### What is the key safety rule?

> When the system is uncertain whether a request is authorized, it must not turn that uncertainty into an ALLOW.

---

## 15. Difference from Real Zanzibar

This learning design intentionally simplifies several things.

| Real Zanzibar concept | Simplified project |
|---|---|
| Spanner | PostgreSQL/SQLite + version column |
| Zookies | Opaque version/freshness token |
| Leopard | Optional local graph index |
| Global fleet | Regional replicas |
| Large-scale sharding | Deferred |
| Production workload isolation | Basic rate/concurrency limits |
| Full Zanzibar protocol | Small Check/Read/Write API |

The goal is to reproduce the **architecture principles**, not Google's exact implementation.

---

## 16. Recommended Repository Layout

```text
Distributed-Systems/
└── projects/
    └── zanzibar-inspired-authorizer/
        ├── README.md
        ├── HLD.md
        ├── data-model.md
        ├── failure-analysis.md
        ├── benchmarks/
        ├── src/
        └── tests/
```

The architecture evidence for this tracker item is:

```text
HLD.md
+
data-model.md
```
