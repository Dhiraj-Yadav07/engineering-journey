# Multi-Region Policy Store & Policy Distribution

> **Type:** High-Level Design (HLD)
>
> **Core principle:** Keep one authoritative policy control plane, distribute versioned policy state asynchronously to regional data planes, and evaluate authorization locally for low latency and resilience.

---

## 1. Problem Statement

An enterprise authorization platform may serve users and applications from several geographic regions:

```text
                    Global Users
             /          |          \
            /           |           \
         India        Europe         US
```

Authorization checks may happen at very high volume:

```text
User / Service
      |
      v
Application
      |
      v
"Can subject S perform action A
 on resource R?"
```

If every check depends on one global policy store:

```text
India ───────┐
Europe ──────┼────> Global Policy Store
US ──────────┘
```

the design introduces WAN latency, regional dependency, central bottlenecks, and a large failure blast radius.

The proposed design separates:

- **Policy management + authoritative storage** in a global control plane
- **Policy distribution + authorization evaluation** in regional data planes

Normal authorization should be local:

```text
Application
    |
    v
Regional AuthZ Engine
    |
    v
Regional Policy
```

rather than synchronously calling a global store for every request.

---

## 2. Goals

### Primary goals

1. Maintain one logical source of truth for policy changes.
2. Distribute policies to multiple geographic regions.
3. Keep normal authorization evaluation local.
4. Minimize authorization latency.
5. Survive temporary global control-plane failures without immediately stopping regional authorization.
6. Use deterministic, immutable policy versions.
7. Provide reliable, observable policy distribution.
8. Bound regional policy staleness.
9. Isolate failures between regions.
10. Scale authorization horizontally.

### Security goals

- Protect policy administration with least privilege.
- Verify policy integrity during distribution.
- Prevent corrupt or unauthenticated policy versions from activating.
- Measure permission-revocation propagation.
- Preserve tenant isolation and auditability.

---

## 3. Non-Goals

This HLD does not define:

- A specific policy language.
- Detailed internals of OPA, Cedar, or a custom policy engine.
- Every policy schema field.
- Application authentication flows.
- Low-level Kafka, Redis, database, networking, or Kubernetes configuration.
- Detailed implementation of consensus algorithms.
- A complete disaster-recovery runbook.

Those belong in LLDs or technology-specific designs.

---

## 4. Functional Requirements

### Policy management

Support:

```text
Create policy
Update policy
Delete / disable policy
Validate policy
Publish policy
Rollback / corrective release
```

### Policy versioning

Every accepted policy change creates a new immutable revision:

```text
v101
  |
  v
v102
  |
  v
v103
  |
  v
v104
```

### Policy distribution

The system must:

- publish policy-change notifications
- distribute new versions to configured regions
- detect regional lag
- retry failed deliveries
- replay missed changes
- use snapshots for large gaps

### Authorization evaluation

Regional engines must:

- evaluate against local active policy
- expose the active policy version
- support horizontal scaling
- avoid cross-region dependency on the normal request path

### Authorization decision caching

The regional data plane may cache:

```text
subject + action + resource + relevant context
                       |
                       v
                 ALLOW / DENY
```

The cache must have explicit TTL, invalidation, or version semantics.

---

## 5. Non-Functional Requirements

### Availability

Example target:

```text
Regional authorization availability >= 99.99%
```

The authorization data path should not require synchronous cross-region calls.

### Latency

Example target:

```text
Authorization p99 < 50 ms
```

Local policy evaluation and optional decision caching are preferred.

### Consistency

Use different consistency expectations:

```text
Policy writes
    -> strongly ordered / authoritative

Policy distribution
    -> asynchronous replication

Regional policy
    -> eventually consistent with bounded staleness

Decision cache
    -> bounded by TTL / invalidation / versioning
```

### Policy propagation SLO

Example:

```text
99.99% of policy updates
become active in every healthy configured region
within 5 seconds.
```

The actual value must be derived from the application's security requirements.

### Disaster recovery

Provide:

- durable policy history
- periodic snapshots
- regional recovery
- event replay
- known-good rollback
- defined RPO/RTO

---

## 6. Architecture Overview

```text
                         ┌─────────────────────┐
                         │ IAM Admin / Portal  │
                         └──────────┬──────────┘
                                    |
                                    v
                         ┌─────────────────────┐
                         │ Policy Management    │
                         │ API                 │
                         └──────────┬──────────┘
                                    |
                                    v
                         ┌─────────────────────┐
                         │ Policy Validation    │
                         │ + Authorization      │
                         │ Checks              │
                         └──────────┬──────────┘
                                    |
                                    v
                  ┌───────────────────────────────────┐
                  │ GLOBAL POLICY STORE              │
                  │ Authoritative, versioned state   │
                  └────────────────┬──────────────────┘
                                   |
                              Outbox / CDC
                                   |
                                   v
                  ┌───────────────────────────────────┐
                  │ POLICY DISTRIBUTION LAYER        │
                  │ Durable Event Bus / Pub/Sub      │
                  └───────────────┬───────────────────┘
                                  |
              ┌───────────────────┼────────────────────┐
              |                   |                    |
              v                   v                    v
       ┌────────────┐      ┌────────────┐       ┌────────────┐
       │ INDIA      │      │ EUROPE     │       │ US         │
       │ REGION     │      │ REGION     │       │ REGION     │
       └─────┬──────┘      └─────┬──────┘       └─────┬──────┘
             |                   |                    |
             v                   v                    v
       Regional Policy     Regional Policy      Regional Policy
           Store                Store                Store
             |                   |                    |
             v                   v                    v
        Decision Cache      Decision Cache       Decision Cache
             |                   |                    |
             v                   v                    v
        Authorization      Authorization       Authorization
          Engine              Engine               Engine
             |                   |                    |
             v                   v                    v
        Applications        Applications         Applications
```

### Core architectural principle

> **Write globally, distribute asynchronously, evaluate locally.**

---

## 7. Control Plane vs Data Plane

### Control Plane

The control plane manages the policy lifecycle:

```text
Admin
  |
  v
Policy Management API
  |
  v
Validation
  |
  v
Global Policy Store
  |
  v
Distribution
```

Responsibilities:

- create/update/delete
- validation
- version creation
- audit
- publishing
- rollback
- distribution monitoring

### Data Plane

The data plane serves authorization requests:

```text
Application
    |
    v
Regional Authorization Engine
    |
    v
Regional Policy
    |
    v
ALLOW / DENY
```

This path may execute millions of times and therefore must be local and highly scalable.

---

## 8. Global Policy Store

The Global Policy Store is the authoritative source of policy state.

Conceptual record:

```text
tenant_id
policy_id
version
policy_data
status
content_hash
created_by
created_at
```

Example:

```text
tenant      = acme
policy      = payroll-access
version     = 103
hash        = sha256(...)
status      = ACTIVE
```

### Recommended properties

- strong ordering for policy changes
- transactional updates
- immutable revisions
- durable storage
- point-in-time retrieval
- auditability
- backup / snapshot support

### Why one logical authority?

Avoid independently writable regional policy stores:

```text
India DB <----> Europe DB <----> US DB
```

because concurrent writes introduce difficult conflict resolution.

Prefer:

```text
                 Global Authority
                       |
          ┌────────────┼────────────┐
          v            v            v
        India        Europe          US
       replica       replica        replica
```

---

## 9. Policy Versioning

Every accepted change produces an immutable version:

```text
v100
 |
 v
v101
 |
 v
v102
 |
 v
v103
```

Example metadata:

```text
policy_id    = payroll-access
tenant_id    = acme
version      = 103
content_hash = sha256(...)
created_by   = admin-123
created_at   = ...
```

### Why versioning matters

Versioning enables:

- deterministic distribution
- idempotency
- ordering
- rollback
- audit
- debugging
- regional lag detection

Example:

```text
Global = v103
India  = v103
Europe = v101
US     = v103
```

Europe is two versions behind.

---

## 10. Policy Distribution

Recommended flow:

```text
Global Policy Store
        |
        v
Transactional Outbox / CDC
        |
        v
Durable Event Bus
        |
        ├────────> India Distributor
        ├────────> Europe Distributor
        └────────> US Distributor
```

Example event:

```text
PolicyChanged {
    tenant_id
    policy_id
    version
    content_hash
    timestamp
}
```

A regional distributor can then fetch the corresponding policy/snapshot and activate it after verification.

### Regional distributor responsibilities

1. Consume event.
2. Check version.
3. Fetch policy.
4. Verify hash/signature.
5. Persist new policy.
6. Validate it.
7. Activate atomically.
8. Report active version.
9. Retry failures.
10. Catch up after downtime.

### Outbox / CDC

Avoid an unreliable sequence such as:

```text
1. Write policy
2. Publish event
```

where step 1 succeeds but step 2 fails.

Conceptually:

```text
Atomic transaction
      |
      +--> Policy Store
      |
      +--> Outbox Record
                 |
                 v
             Publisher
                 |
                 v
              Event Bus
```

### Idempotency

```text
Local = 103
Incoming = 102
-> ignore

Local = 103
Incoming = 103
-> already applied / ignore safely

Local = 103
Incoming = 104
-> process
```

### Out-of-order delivery

If events arrive:

```text
v105
v103
v104
```

the regional consumer must never roll the active policy backwards.

### Snapshot + incremental catch-up

For a large lag:

```text
Global = v10000
Region = v9000
```

prefer:

```text
Snapshot v10000
      +
new incremental events
```

instead of replaying all 1,000 changes.

---

## 11. Regional Policy Store

Each region maintains a durable local policy representation:

```text
             Regional Policy Store
                     |
        ┌────────────┼────────────┐
        v            v            v
      v101         v102         v103
```

The regional store is a replica, not the global source of truth.

### Characteristics

- local low-latency reads
- durable storage
- active-version tracking
- atomic activation
- snapshot restore
- high availability

### Atomic activation

Use:

```text
Receive
   |
Validate
   |
Persist
   |
Verify
   |
Activate
```

The authorization engine should observe a complete active version, not a partially written policy.

---

## 12. Authorization Evaluation

Example request:

```text
subject  = user-123
action   = READ
resource = payroll/report-456
```

Normal path:

```text
User / Service
      |
      v
Regional Application
      |
      v
Authorization Engine
      |
      v
Regional Policy
      |
      v
ALLOW / DENY
```

### Critical rule

> **Normal authorization evaluation should not require a synchronous cross-region call.**

This reduces latency and protects the regional data plane from WAN failures.

---

## 13. Authorization Decision Cache

A decision cache can sit in front of the regional authorization engine:

```text
Application
    |
    v
Authorization Decision Cache
    |
   HIT?
  /    YES     NO
 |       |
 v       v
ALLOW   AuthZ Engine
/DENY      |
            v
       Regional Policy
            |
            v
         Decision
            |
            v
          Cache
```

### Example key

```text
authz:acme:user-123:read:payroll-456
```

The exact key may also require:

- tenant
- subject
- action
- resource
- policy version
- relevant contextual attributes

### Security requirement

The cache must not reuse a decision when an input that affects the decision has changed.

### Revocation problem

```text
09:00
User has admin access
      |
      v
Cached decision = ALLOW

09:05
Admin revokes access
      |
      v
Current policy = DENY

Cache still says ALLOW
```

This creates a security-sensitive stale-decision window.

Define:

```text
Permission revoked
      |
      v
Old ALLOW becomes unusable
within X seconds
```

Possible techniques:

- short TTL
- targeted invalidation
- policy/version validation
- event-driven invalidation

---

## 14. Failure Handling

| Failure | Expected behavior |
|---|---|
| Global policy store unavailable | Existing valid regional policy continues |
| Event bus unavailable | Region stays on last valid version and catches up later |
| Regional distributor down | Existing policy remains active; distributor catches up |
| WAN connectivity lost | Local authorization continues subject to freshness limits |
| Duplicate event | Idempotent processing |
| Out-of-order event | Older version ignored |
| Corrupt/tampered policy | Verification fails; do not activate |
| Region far behind | Fetch latest snapshot |
| Bad policy release | Roll back or publish corrected version |

### Global control-plane failure

A healthy regional data plane should continue with the last known valid policy rather than immediately failing every authorization check.

### Too-stale policy

Conceptually:

```text
Fresh
  |
  v
Normal operation

Stale but within allowed window
  |
  v
Continue with monitoring

Beyond security threshold
  |
  v
Restricted behavior / deny sensitive operations
```

The exact threshold is a business/security requirement.

---

## 15. Consistency Model

The architecture intentionally uses different consistency characteristics:

```text
                    POLICY WRITE
                         |
                         v
                 Strong ordering
                         |
                         v
                  Global authority
                         |
                         v
               Async distribution
                         |
                         v
                  Regional replica
                         |
                         v
                Local authorization
```

### Global policy writes

Prefer strong ordering because policy updates need deterministic revision history.

### Regional distribution

Use asynchronous replication so authorization requests do not depend on WAN coordination.

### Regional state

Eventually consistent with the global policy state, but with an explicit propagation SLO and staleness policy.

### Decision cache

The cache is a performance layer and must not silently become the authoritative policy source.

---

## 16. Security

### Administrative access

Use least privilege for:

```text
Create
Modify
Publish
Rollback
```

### Policy integrity

Protect policies with:

```text
Authenticated transport
Hash/checksum
Digital signature where required
```

A regional node should not activate a policy it cannot verify.

### Encryption

Use encryption in transit and at rest according to policy/data sensitivity.

### Tenant isolation

Use explicit tenant scoping in:

- policy storage
- policy distribution
- regional policy replicas
- decision caches
- authorization requests

### Service identities

Only trusted services should:

```text
publish policy
consume policy events
activate policy
```

---

## 17. Audit & Observability

### Audit trail

Capture:

```text
actor
tenant
policy
old version
new version
change
timestamp
reason / ticket
```

Example:

```text
actor       = admin-123
tenant      = acme
policy      = payroll-access
old_version = 102
new_version = 103
change      = removed payroll.read
```

### Distribution metrics

Track:

```text
policy publication rate
distribution success/failure
regional active version
regional version lag
propagation p50/p95/p99
activation failures
snapshot recovery time
```

### Authorization metrics

Track:

```text
authorization latency
decision-cache hit ratio
decision-cache miss rate
policy evaluation errors
stale-policy usage
revocation propagation time
```

### Traceability

Authorization decisions should be attributable to:

```text
request
region
policy version
decision
```

Example:

```text
Decision = DENY
Region   = Europe
Policy   = v103
```

This is valuable for troubleshooting and audits.

---

## 18. Disaster Recovery

### Policy snapshots

Create periodic authoritative snapshots:

```text
Snapshot v10000
Snapshot v11000
Snapshot v12000
```

Store them durably.

### Regional recovery

```text
Region lost
   |
   v
Rebuild infrastructure
   |
   v
Load latest policy snapshot
   |
   v
Validate
   |
   v
Replay newer policy changes
   |
   v
Activate
   |
   v
Resume authorization
```

### RPO / RTO

Define:

```text
RPO = acceptable policy state loss
RTO = acceptable regional recovery time
```

For authorization policy, authoritative policy history should generally target very low data loss.

---

## 19. Capacity / Scaling

### Control plane

Scale based on:

```text
tenants
number of policies
policy size
policy-change rate
distribution fan-out
```

Policy changes are normally far less frequent than authorization checks.

### Authorization data plane

Scale horizontally:

```text
             Load Balancer
                  |
       ┌──────────┼──────────┐
       v          v          v
    AuthZ-1     AuthZ-2    AuthZ-3
       |          |          |
       +----------+----------+
                  |
            Regional Policy
```

### Decision cache

Capacity depends on:

```text
requests/sec
unique cache keys
entry size
TTL
hit ratio
tenant distribution
```

### Event bus

Capacity depends on:

```text
policy changes/sec
regions
event size
retention
replay requirements
```

---

## 20. Trade-offs & Alternatives

### Alternative 1: Central store for every authorization request

```text
Regional App
     |
     v
Global Policy Store
```

**Pros**

- simple source-of-truth model
- easier consistency reasoning

**Cons**

- higher latency
- WAN dependency
- regional outage sensitivity
- central bottleneck

**Decision:** Reject for the normal authorization request path.

---

### Alternative 2: Independent writable policy store per region

```text
India DB <----> Europe DB <----> US DB
```

**Pros**

- regional write availability
- lower local write latency

**Cons**

- conflict resolution
- difficult deterministic ordering
- harder audit semantics
- more complex reconciliation

**Decision:** Reject unless multi-master policy writes are an explicit requirement.

---

### Alternative 3: Global authority + async regional replicas

```text
Global Policy Store
        |
        v
   Event / CDC
        |
   ┌────┼────┐
   v    v    v
  IN   EU    US
```

**Pros**

- clear source of truth
- deterministic ordering
- local authorization
- regional isolation
- scalable data plane

**Cons**

- temporary regional staleness
- distribution complexity
- catch-up/replay logic

**Decision:** Recommended.

---

### Alternative 4: No authorization decision cache

**Pros**

- less cache-staleness complexity
- fewer invalidation concerns

**Cons**

- more policy evaluations
- higher engine load
- potentially higher authorization latency

**Decision:** Use where required by workload/security requirements; otherwise use bounded, carefully designed caching.

---

## 21. Architecture Decision Record

### ADR-001: Single logical global policy authority

**Decision**

Use one authoritative global policy store for policy writes.

**Reason**

- deterministic policy ordering
- simpler conflict model
- clear audit trail
- easier rollback

**Trade-off**

The control plane has global dependencies, but regional data planes continue with last-known-valid policy.

---

### ADR-002: Asynchronous policy distribution

**Decision**

Distribute policy changes through a durable event mechanism.

**Reason**

- avoids cross-region latency on authorization
- decouples control plane from regional availability
- supports retry and replay
- scales to multiple regions

**Trade-off**

Regional policies can temporarily lag.

Mitigations:

```text
versioning
+
propagation SLO
+
lag monitoring
+
snapshot catch-up
```

---

### ADR-003: Immutable policy versions

**Decision**

Every policy change creates a new immutable version.

**Reason**

- auditability
- rollback
- deterministic distribution
- idempotency
- debugging

---

### ADR-004: Local authorization evaluation

**Decision**

Regional authorization engines evaluate against local regional policy.

**Reason**

- lower latency
- regional resilience
- independent horizontal scaling

**Trade-off**

Requires a reliable policy-distribution mechanism and explicit stale-policy controls.

---

### ADR-005: Authorization cache freshness is a security property

**Decision**

Authorization decision caching must have explicit TTL, invalidation, versioning, or a combination of these controls.

**Reason**

A stale product price is usually a correctness issue.

A stale authorization decision can become a security issue.

The design must explicitly define:

```text
Maximum stale-ALLOW window
Revocation propagation SLO
Cache failure behavior
```

---

# Final Architecture Principle

```text
                    CONTROL PLANE
                         |
               Authoritative Policy
                         |
                     Versioning
                         |
                  Async Distribution
                         |
        ┌────────────────┼────────────────┐
        v                v                v
      INDIA            EUROPE             US
        |                |                |
   Local Policy      Local Policy      Local Policy
        |                |                |
   Decision Cache    Decision Cache    Decision Cache
        |                |                |
      AuthZ             AuthZ             AuthZ
        |                |                |
    Applications     Applications      Applications
```

> **Global control plane for authoritative policy changes.**
>
> **Asynchronous, versioned distribution to regional policy replicas.**
>
> **Local authorization evaluation for low latency and regional resilience.**
>
> **Explicit policy freshness, invalidation, and failure semantics for security-sensitive authorization.**
