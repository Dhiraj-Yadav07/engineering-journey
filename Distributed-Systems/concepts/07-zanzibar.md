# Zanzibar Study Notes

## Study Goal

Understand Google's Zanzibar system through three lenses:

1. **Data model** — how authorization relationships are represented.
2. **Consistency** — how Zanzibar prevents stale or incorrectly ordered authorization decisions.
3. **Scaling** — how the system handles global authorization at very large scale.

Primary source: Ruoming Pang et al., **“Zanzibar: Google’s Consistent, Global Authorization System,” USENIX ATC 2019**.

Google describes Zanzibar as a global system for storing and evaluating access-control lists used by many Google services. The paper reports trillions of ACLs, millions of authorization requests per second, 95th-percentile latency below 10 ms, and availability above 99.999% over three years of production use. citeturn486793view0

---

# 1. Why Zanzibar Exists

Zanzibar is a shared authorization system intended to provide common semantics, flexibility, correctness, low latency, high availability, and global scale across many products.

Authorization is especially latency-sensitive because it often sits directly in the request path. Search workloads can require tens to hundreds of authorization checks for one user interaction. citeturn452768view0

---

# 2. Core Data Model: Relation Tuples

The central Zanzibar primitive is the **relation tuple**:

```text
<object>#<relation>@<user>
```

An object is:

```text
<namespace>:<object_id>
```

A user is either an individual user ID or a **userset**:

```text
<object>#<relation>
```

Examples:

```text
doc:readme#owner@10
group:eng#member@11
doc:readme#viewer@group:eng#member
```

These mean, respectively, that user 10 owns a document, user 11 belongs to a group, and members of that group are viewers of the document. The paper identifies the tuple using namespace, object ID, relation, and user. Usersets allow ACLs to refer to groups and support nested group membership. citeturn271573view0

### Key mental model

> Zanzibar stores **relationships**, then evaluates effective authorization from those relationships plus configuration.

Tuple-based storage unifies ACLs and groups and supports efficient reads and incremental updates. citeturn271573view0

---

# 3. Namespace Configuration and Userset Rewrites

Each Zanzibar namespace has configuration defining its relations and storage parameters. Relation configuration can contain **userset rewrite rules** that express object-agnostic relationships between relations.

For example, a namespace can express a rule conceptually like:

```text
viewer = direct_viewer UNION editor
```

without materializing redundant viewer tuples for every object.

Userset expressions support set-style composition including **union, intersection, and exclusion**. This is what allows Zanzibar to express rich policies while keeping stored relationships normalized. citeturn452768search1turn271573view2

---

# 4. Authorization Check

The fundamental question is:

```text
Does user U have relation R to object O?
```

A simple direct check can be reduced to the existence of a matching relation tuple. When a tuple refers to another userset, the engine recursively evaluates that referenced object-relation pair.

This creates **pointer chasing** through an authorization graph. A check can fan out into multiple sub-checks, and those sub-checks may recursively fan out again. citeturn452768view0turn271573view4

Zanzibar evaluates leaf nodes concurrently and cancels work once the result of a subtree is already determined. It also pools related reads to reduce backend RPCs. citeturn271573view4

---

# 5. The Consistency Problem: “New Enemy”

Ordinary eventual consistency can be unsafe for authorization.

Example:

```text
1. Alice removes Bob from a folder ACL.
2. Alice adds a new document to that folder.
3. Bob requests the new document.
```

If the authorization check observes an ACL state from before the removal, Bob could incorrectly receive access.

Another version is:

```text
1. Alice removes Bob from a document ACL.
2. Alice adds new content.
3. Bob requests the new content.
```

The check must not use a stale ACL snapshot that predates Bob's removal. The paper calls this the **new-enemy problem**. citeturn271573view0

---

# 6. Zanzibar's Consistency Model

Zanzibar requires two related properties:

```text
External consistency
+
Snapshot reads with bounded staleness
```

ACLs are stored in Google Spanner. Spanner provides globally meaningful timestamps reflecting causal ordering. Zanzibar evaluates a check using one consistent snapshot timestamp across its database reads. citeturn271573view1

The critical point is:

> One authorization decision must be evaluated from a coherent snapshot.

---

# 7. Zookies

A **zookie** is an opaque consistency token containing information about a globally meaningful timestamp. It is not the authorization result and is not itself a capability.

Conceptually:

```text
ACL/content change
        ↓
      zookie
        ↓
client stores zookie with content version
        ↓
later authorization check
        ↓
snapshot >= zookie freshness requirement
```

The client sends the zookie with later checks so the chosen snapshot is at least as fresh as the content version's required timestamp. This provides **at-least-as-fresh** semantics. citeturn271573view1turn271573view2

### Why this matters

Suppose:

```text
ACL removal = T1
new content  = T2
T2 > T1
```

A check for the new content must use a snapshot at least as fresh as T2, so it cannot see the new content while still seeing the pre-removal ACL state. This prevents the new-enemy problem. citeturn271573view1

---

# 8. Why Not Always Read the Latest Global State?

A naive design would force every authorization check to obtain the newest global state. That would require frequent global synchronization and high-latency cross-region round trips.

Zanzibar instead allows most checks to use already replicated data, subject to the requested freshness bound. The server can choose any snapshot newer than the zookie's timestamp.

This gives the important trade-off:

```text
causal correctness
+
bounded staleness
+
local replicated reads
=
low latency without a global round trip for every check
```

This is one of Zanzibar's most important distributed-systems ideas. citeturn271573view1

---

# 9. APIs

Zanzibar exposes APIs around relation tuples and authorization:

| API | Purpose |
|---|---|
| **Read** | Read relation tuples at a consistent snapshot |
| **Write** | Add/remove relation tuples |
| **Watch** | Stream tuple changes for downstream consumers/indexes |
| **Check** | Determine whether a user has a relation to an object |
| **Expand** | Return the effective userset after following rewrite rules |

Writes involving multiple tuples can use a read-modify-write flow with optimistic concurrency and a lock tuple to detect races. Watch streams timestamp-ordered tuple changes. Expand differs from Read because it follows indirect relationships and rewrite rules. citeturn271573view2

---

# 10. Global Architecture

A simplified mental model is:

```text
                    Spanner
                       |
        +--------------+---------------+
        |              |               |
   Tuple databases  Namespace      Changelog
                     configs          DB
        |              |               |
        +--------------+---------------+
                       |
               Zanzibar clusters
                       |
             +---------+---------+
             |         |         |
         aclserver aclserver aclserver
             |
       +-----+------+
       |            |
     Check       Read/Write
       |
   cache / internal RPC
       |
    Leopard
```

The paper describes one relation-tuple database per namespace, a database for namespace configurations, and a shared changelog database. Watch servers tail the changelog, while Leopard is used for selected large/deep set computations. citeturn271573view3

---

# 11. Global Replication and Sharding

ACL data does not lend itself to simple geographic partitioning because a check for any object can originate anywhere. Zanzibar therefore replicates ACL data across geographically distributed locations and spreads load across many servers. citeturn452768view0

Relation tuples are stored with keys including:

```text
shard ID
object ID
relation
user
commit timestamp
```

Multiple tuple versions are retained so reads/checks can evaluate historical snapshots within the garbage-collection window. Namespace sharding is configurable according to data shape. Usually the shard is based on object ID; for very large groups, object ID plus user can be used to spread membership across shards. citeturn271573view3

### Distributed-systems lesson

> Partition according to the actual access pattern, not merely according to the logical schema.

---

# 12. Scaling Nested Authorization: Leopard

Deep or wide group nesting can make recursive pointer chasing expensive:

```text
user
 ↓
group A
 ↓
group B
 ↓
group C
 ↓
object
```

For selected namespaces, Zanzibar uses **Leopard**, a specialized indexing system for set computation.

Leopard represents set relationships so that operations such as union and intersection can be performed efficiently. Its index is sharded and is usually served from memory. It combines an offline snapshot/index-build process with a real-time incremental update layer driven by Zanzibar's Watch API. citeturn223479view0

The important architectural pattern is:

```text
durable normalized source of truth
                ↓
       change stream / Watch
                ↓
 specialized derived index
                ↓
 fast graph/set evaluation
```

This is controlled denormalization used only where the workload justifies it. citeturn223479view0

---

# 13. Caching and Hot-Spot Mitigation

Authorization workloads are often bursty. Many checks can reference the same popular group or object.

Zanzibar uses distributed caches for:

```text
final check results
read results
intermediate check results
```

Cache entries are distributed using consistent hashing. Zanzibar can route related work using the object ID so that checks involving the same object's relations tend to share a server and cache. citeturn223479view1

### Cache timestamp quantization

Cache keys include snapshot information. Zanzibar can round evaluation timestamps upward to coarse boundaries such as one or ten seconds, while respecting freshness requirements. This increases cache sharing because many requests can use the same snapshot timestamp. citeturn223479view1

### Cache stampede protection

A lock table prevents many concurrent cache misses from all starting identical backend work:

```text
100 identical requests
        ↓
1 request performs backend work
        ↓
cache populated
        ↓
other requests reuse result
```

citeturn223479view1

### Hot objects

Zanzibar can dynamically identify hot objects and cache all relation tuples for a hot object rather than repeatedly reading them from the underlying database. citeturn223479view1

---

# 14. Request Hedging and Tail Latency

Distributed systems are often constrained by the slowest dependency. Zanzibar uses **request hedging** for Spanner and Leopard operations.

Conceptually:

```text
request
  |
  +----> replica A
  |
  +----> replica B  (only if A is slow)
               |
               v
       use fastest response
       cancel slower request
```

The hedge is delayed so normal requests do not automatically duplicate load. Zanzibar dynamically estimates latency percentiles to choose the delay threshold. citeturn223479view1

Important lesson:

> Hedging is a tail-latency technique, but indiscriminate duplication can increase load and make expensive workloads worse.

---

# 15. Performance Isolation

Zanzibar serves many clients, so one workload must not monopolize shared resources.

The paper describes controls including:

```text
per-client CPU limits
per-server outstanding-RPC limits
per-client outstanding-RPC limits
per-object concurrency limits
per-client database-read limits
client-specific lock-table keys
```

These mechanisms isolate noisy workloads and protect system-wide latency and availability. citeturn223479view1

---

# 16. Production Scale Reported by the Paper

For the production period described in the paper:

| Metric | Reported value |
|---|---:|
| Namespaces | >1,500 |
| Relation tuples | >2 trillion |
| Storage | close to 100 TB |
| Global replication | >30 locations |
| Client queries | >10 million QPS |
| Serving servers | >10,000 |
| Check peak | ~4.2M QPS |
| Read peak | ~8.2M QPS |
| Expand peak | ~760K QPS |
| Write peak | ~25K QPS |

The paper notes that reads/checks vastly outnumber writes, which explains the heavy emphasis on replicated reads, caching, indexing, and tail-latency optimization. These are historical production measurements from the paper's 2018 observation period, not current Google infrastructure figures. citeturn223479view2

---

# 17. Safe vs Recent Requests

Freshness has a direct effect on latency.

Conceptually:

```text
Older zookie
    ↓
regional replica is fresh enough
    ↓
local serving
    ↓
lower latency
```

versus:

```text
Very recent zookie
    ↓
region may not have sufficiently fresh data
    ↓
cross-region read may be required
    ↓
higher latency
```

The paper reports that Safe requests dominate traffic, which lets the vast majority of checks be served using locally replicated data. citeturn223479view2

---

# 18. Reported Latency

For Safe Check traffic in the paper's measured seven-day period:

```text
p50  ≈ 3.0 ms
p95  ≈ 9.46 ms
p99  ≈ 15.0 ms
```

Recent operations have much higher tail latency when fresher data requires cross-region coordination. Writes are much slower because they require distributed coordination through Spanner. citeturn223479view2

This is a useful comparison with our local benchmark:

```text
Our local engine:
~microseconds, in-process, no network

Zanzibar production system:
~milliseconds, distributed, globally replicated
```

The values should **not** be compared as though they measure the same thing. They measure fundamentally different layers of an authorization system.

---

# 19. Zanzibar vs Our Authorization Engine

Our current engine is essentially:

```text
subject
   ↓
assigned roles
   ↓
permission lookup
   ↓
ALLOW / DENY
```

Zanzibar generalizes authorization into:

```text
subject
   ↓
userset
   ↓
relation
   ↓
object
   ↓
possibly another userset
   ↓
recursive graph evaluation
   ↓
consistent snapshot
   ↓
ALLOW / DENY
```

### Current engine

```text
Alice
  ↓
developer
  ↓
reports:read
```

### Zanzibar-style relationship model

```text
user:alice
     |
     v
group:engineering#member
     |
     v
folder:finance#viewer
     |
     v
document:report.pdf#viewer
```

The second model expresses **relationships and inheritance**, not just assigned roles.

---

# 20. What Zanzibar Adds to Our Multi-Region HLD

Our current architecture already uses ideas such as:

```text
Global authoritative policy
        ↓
versioned distribution
        ↓
regional policy state
        ↓
local authorization
        ↓
decision cache
```

Zanzibar suggests additional design ideas:

```text
relationship-centric data model
        +
consistent snapshots
        +
explicit freshness tokens
        +
global replication
        +
hot-key protection
        +
graph/set indexing
        +
request coalescing
        +
tail-latency controls
```

The key insight is that Zanzibar is not merely a replicated ACL database. It is a **distributed authorization evaluation system** in which storage, consistency, caching, indexing, and request execution are designed around authorization workloads.

---

# 21. The Three Answers to Memorize

## What is Zanzibar's data model?

> A tuple-based relationship model: object + relation + user/userset, combined with namespace configuration and userset rewrite rules. It represents direct and indirect relationships such as users, groups, nested groups, and resource hierarchies.

## How does Zanzibar achieve consistency?

> It uses externally consistent storage, consistent snapshots, and zookies that impose an at-least-as-fresh snapshot requirement. This preserves causal ordering and prevents the new-enemy problem without forcing every check to perform a global round trip.

## How does Zanzibar scale?

> It globally replicates data, shards according to workload, serves most reads locally, caches final and intermediate results, coalesces duplicate work, uses specialized indexes for deep/wide relationship graphs, mitigates hot spots, hedges slow backend requests, and isolates clients from one another.

---

# 22. Key Terms to Know

Be comfortable explaining these in your own words:

```text
Relation tuple
Object
Relation
User
Userset
Namespace
Userset rewrite
Check
Read
Write
Watch
Expand
External consistency
Snapshot read
Bounded staleness
Zookie
New-enemy problem
Spanner
Sharding
Consistent hashing
Hot spot
Cache stampede
Request coalescing
Request hedging
Leopard
Performance isolation
Tail latency
```

---

# 23. EASE Interview Mental Model

Keep this picture in your head:

```text
                 AUTHORIZATION MODEL
                        |
             namespace configuration
                        |
                        v
               relation tuples
                        |
                        v
                userset / graph
                        |
                        v
                Check evaluation
                 /     |      \
                /      |       \
            cache    fan-out   Leopard
               \       |      /
                \      |     /
                 \     |    /
                  consistent
                    snapshot
                       |
                    zookie
                       |
                       v
                  ALLOW / DENY
```

And remember the distributed-systems chain:

```text
Global source of truth
        ↓
consistent version/snapshot
        ↓
replication
        ↓
local cache/index
        ↓
parallel/recursive evaluation
        ↓
tail-latency protection
        ↓
authorization decision
```

---

# 24. Study Status

- [x] Zanzibar purpose understood
- [x] Relation-tuple data model extracted
- [x] Usersets and rewrite rules understood
- [x] Check evaluation understood
- [x] New-enemy problem understood
- [x] External consistency understood
- [x] Bounded-staleness model understood
- [x] Zookies understood
- [x] Global replication and sharding extracted
- [x] Leopard indexing extracted
- [x] Caching and hot-spot handling extracted
- [x] Request hedging extracted
- [x] Performance isolation extracted
- [x] Production scale and latency figures recorded
- [x] Mapping to our authorization-engine architecture documented

---

# 25. Sources

1. Google Research — Zanzibar publication page and abstract.
2. Zanzibar paper — Sections 2.1–2.3: relation tuples, consistency, namespace configuration.
3. Zanzibar paper — Section 2.4: Read, Write, Watch, Check, Expand APIs.
4. Zanzibar paper — Section 3: storage, check evaluation, Leopard, caching, performance isolation, tail-latency mitigation.
5. Zanzibar paper — Section 4: production scale, latency, availability.

Primary paper:
**Ruoming Pang et al., “Zanzibar: Google’s Consistent, Global Authorization System,” Proceedings of the 2019 USENIX Annual Technical Conference.**

Google Research:
https://research.google/pubs/zanzibar-googles-consistent-global-authorization-system/

Paper PDF:
https://storage.googleapis.com/gweb-research2023-media/pubtools/5068.pdf
