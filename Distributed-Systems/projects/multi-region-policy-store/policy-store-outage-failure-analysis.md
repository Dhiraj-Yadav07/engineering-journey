# Policy Store Outage — Failure Analysis

> **Architecture:** Multi-Region Policy Store & Policy Distribution  
> **Focus:** Failure recovery for policy-store outage  
> **Deliverable:** Failure analysis

## 1. Scenario

The architecture separates the **global policy control plane** from the **regional authorization data plane**:

```text
                 GLOBAL CONTROL PLANE
                        |
                Global Policy Store
                        |
                 Policy Distribution
                        |
        ┌───────────────┼───────────────┐
        v               v               v
      India           Europe            US
        |               |               |
   Regional         Regional        Regional
    Policy           Policy          Policy
        |               |               |
      AuthZ            AuthZ           AuthZ
```

The failure being analyzed is:

```text
Global Policy Store
        |
        X
   UNAVAILABLE
```

Possible causes include a database outage, network failure, connection exhaustion, software defect, maintenance, storage failure, or credential/dependency failure.

---

## 2. Expected System Behavior

> **A global policy-store outage should not automatically become a global authorization outage.**

Healthy regions should continue using their **last known valid policy** while it remains inside the allowed freshness window.

```text
Global Policy Store ❌
        |
        v
Regional Policy = last known valid version
        |
        v
Regional Authorization Engine
        |
        v
     ALLOW / DENY
```

However, new authoritative policy changes cannot be considered committed until the global policy store successfully persists them.

---

## 3. Failure Boundary

```text
CONTROL PLANE
--------------------------
Policy Management
Global Policy Store
Policy Publication
Policy Distribution

DATA PLANE
--------------------------
Regional Policy Store
Authorization Engine
Decision Cache
Applications
```

The control plane may fail temporarily while the data plane continues operating from existing valid state.

This is the key resilience property of the architecture.

---

## 4. Failure Mode 1 — Global Policy Store Unavailable

### Condition

```text
Global Policy Store ❌
```

### Impact

- Policy writes fail.
- New policy reads from the authority fail.
- Policy publication may stop.
- Regions cannot fetch missing versions.
- Existing regional policy can continue to serve authorization.

### Expected behavior

```text
Regional Policy Store
       |
       v
Last valid policy
       |
       v
Authorization continues
```

### Recovery

```text
Global Store recovers
        |
        v
Determine latest authoritative version
        |
        v
Resume distribution
        |
        v
Regions catch up
```

### Main risk

Regional policy becomes increasingly stale.

Therefore monitor:

```text
policy_age
policy_version_lag
```

---

## 5. Failure Mode 2 — Policy Store Write Failure

Suppose an administrator attempts:

```text
Remove Alice from Admin role
```

but the authoritative store cannot commit the change.

Correct behavior:

```text
Admin
  |
  v
Policy Management API
  |
  v
Global Store ❌
  |
  v
WRITE FAILED
```

The API must **not** claim success unless the authoritative write was durably committed.

This prevents dangerous states such as:

```text
UI says: Alice is no longer admin
Actual policy: Alice is still admin
```

---

## 6. Failure Mode 3 — Policy Update During Outage

Current state:

```text
Current policy = v103
Global store   = unavailable
```

An administrator requests `v104`.

### Recommended behavior

Do not let individual regions independently become authoritative:

```text
India  → v104
Europe → v105
US     → v104
```

That creates multi-master conflict and audit ambiguity.

Instead:

```text
Global store unavailable
        |
        v
Authoritative policy write rejected / not committed
        |
        v
Global store recovers
        |
        v
v104 committed
        |
        v
v104 distributed
```

---

## 7. Failure Mode 4 — Event Distribution Also Fails

Possible state:

```text
Global Store = v104
Regions      = v103
Event Bus    = unavailable
```

Regional authorization continues using the last valid local policy while the distribution path recovers.

A durable outbox/CDC mechanism should preserve the publication intent associated with the committed policy change.

After recovery:

```text
v104 event
   |
   v
Regional Distributor
   |
   v
Regional Policy Store
   |
   v
Activate v104
```

---

## 8. Failure Mode 5 — Regional Policy Store Failure

Example:

```text
India Regional Policy Store ❌
Europe                     ✅
US                         ✅
```

The regional design should use a highly available regional store or a documented degraded-mode mechanism.

Do not automatically fail open simply because a regional policy dependency is unavailable.

For sensitive authorization, failing closed or restricting sensitive operations may be safer.

---

## 9. Failure Mode 6 — Region Loses WAN Connectivity

```text
              GLOBAL CONTROL PLANE
                      X
                      |
                  WAN outage
                      |
                  India Region
```

India may continue with:

```text
last active policy = v103
```

until the configured freshness limit is reached.

When connectivity returns:

```text
Compare local version vs global version
        |
        v
Replay missing events OR fetch snapshot
        |
        v
Verify
        |
        v
Activate
```

---

## 10. Failure Mode 7 — Region Becomes Too Stale

This is a critical security failure mode.

Example:

```text
Global = v104
India  = v103
```

If v104 revokes a privileged permission, continuing to authorize indefinitely with v103 may create an authorization gap.

Use explicit policy freshness states:

```text
FRESH
  |
  v
Normal operation

STALE BUT WITHIN LIMIT
  |
  v
Continue + alert/monitor

TOO STALE
  |
  v
Restrict or deny sensitive operations
```

The thresholds must be set from the application's risk requirements.

---

## 11. Failure Mode 8 — Decision Cache During Outage

A region may have both stale policy and stale authorization decisions:

```text
Regional Policy = old
Decision Cache  = older
```

Example:

```text
ALLOW decision cached for Alice
        |
        v
Permission revoked globally
        |
        v
Region has not received new policy yet
        |
        v
Cached ALLOW may remain usable
```

Controls should include:

- bounded decision TTL
- policy/version-aware cache entries
- event-driven invalidation where practical
- explicit stale-policy monitoring

The cache must not silently bypass policy-freshness rules.

---

## 12. Failure Mode 9 — Corrupt or Tampered Policy

```text
Receive v104
     |
     v
Verify hash/signature
     |
     X
Verification failed
     |
     v
DO NOT ACTIVATE
     |
     v
Keep previous valid policy
```

Policy integrity verification should happen before activation.

---

## 13. Failure Mode 10 — Duplicate Events

The distribution system may deliver:

```text
PolicyChanged v104
PolicyChanged v104
```

Consumers must be idempotent:

```text
Local = v104
Incoming = v104
        |
        v
Already applied → ignore safely
```

---

## 14. Failure Mode 11 — Out-of-Order Events

Events may arrive as:

```text
v105
v103
v104
```

The region must never move backward.

Rule:

```text
incoming_version <= active_version
             |
             v
           ignore
```

---

## 15. Failure Mode 12 — Region Falls Far Behind

Example:

```text
Global = v10000
Region = v9000
```

Replaying every change may be inefficient.

Use:

```text
Latest verified snapshot = v10000
             +
Future incremental events
```

Recovery:

```text
Detect large lag
       |
       v
Fetch snapshot
       |
       v
Verify
       |
       v
Activate atomically
       |
       v
Resume incremental distribution
```

---

## 16. Failure Mode 13 — Bad Policy Release

Suppose:

```text
v103 = known good
v104 = bad
```

Because versions are immutable, preserve the bad version in history and publish a corrected revision:

```text
v103 → v104 → v105
             ^
        corrected state
```

This preserves auditability and allows incident reconstruction.

---

## 17. Failure Matrix

| Failure | Control Plane | Regional AuthZ | Policy Freshness | Recovery |
|---|---|---|---|---|
| Global store down | Writes/read fail | Continue locally | Degrades over time | Restore store, distribute latest |
| Global write failure | New update rejected | Existing policy | Unchanged | Retry after recovery |
| Event bus down | Policy may still commit | Continue locally | Regions lag | Replay/catch up |
| Regional distributor down | Global works | Continue with local policy | Region lags | Distributor recovers |
| Regional policy store down | Global unaffected | Local HA/degraded mode | Depends on local copy | Restore/fail over |
| WAN partition | Control path isolated | Local authorization continues | Region may become stale | Reconnect/catch up |
| Policy verification failure | Event rejected | Previous valid policy | No activation | Investigate/reissue |
| Bad policy release | Bad version exists in history | Depends on rollout controls | Version known | Corrective release |
| Decision cache stale | N/A | Potential stale ALLOW/DENY | Cache bounded | TTL/invalidation/version check |
| Region far behind | Global healthy | Last valid policy | High lag | Snapshot + incremental catch-up |

---

## 18. Recovery Sequence

```text
             GLOBAL POLICY STORE
                     |
                 RECOVERY
                     |
                     v
          Verify authoritative state
                     |
                     v
              Find latest version
                     |
                     v
            Resume event publishing
                     |
                     v
        Regional distributors reconnect
                     |
                     v
       Compare regional vs global version
                     |
          ┌──────────┴──────────┐
          |                     |
       Small gap             Large gap
          |                     |
          v                     v
     Replay events          Snapshot restore
          |                     |
          └──────────┬──────────┘
                     v
                Verify policy
                     |
                     v
              Activate atomically
                     |
                     v
              Report new version
```

---

## 19. Recovery Invariants

### Invariant 1 — Never activate an unverified policy

```text
VERIFY → ACTIVATE
```

not:

```text
RECEIVE → ACTIVATE
```

### Invariant 2 — Never move policy version backward

```text
103 → 104 → 105
```

never:

```text
105 → 103
```

### Invariant 3 — Never report an uncommitted policy change as successful

```text
Authoritative commit
        |
        v
      Success
```

### Invariant 4 — Control-plane failure must not automatically take down the data plane

Existing regional policy may continue until the freshness boundary is reached.

### Invariant 5 — Security-sensitive stale state must be bounded

The system must know:

```text
How old is the active policy?
```

and:

```text
What happens when it becomes too old?
```

---

## 20. Regional Recovery State Machine

```text
             +---------+
             |  FRESH  |
             +----+----+
                  |
            distribution lag
                  |
                  v
          +---------------+
          | STALE_ALLOWED |
          +-------+-------+
                  |
             stale threshold
                  |
                  v
          +---------------+
          | TOO_STALE     |
          +-------+-------+
                  |
               recovery
                  |
                  v
             +---------+
             | CATCHUP |
             +----+----+
                  |
             verified policy
                  |
                  v
             +---------+
             |  FRESH  |
             +---------+
```

---

## 21. Observability Required for Recovery

### Global store

```text
availability
read/write latency
error rate
connection failures
```

### Distribution

```text
event lag
publish failures
consumer lag
retry count
dead-letter events
```

### Regional policy

```text
active policy version
global policy version
version lag
policy age
activation failures
snapshot age
```

### Authorization

```text
authorization latency
decision-cache hit ratio
decision-cache miss rate
stale-policy decisions
authorization errors
```

### Security

Most important:

```text
revocation propagation time
maximum stale-ALLOW age
requests evaluated with stale policy
regions beyond freshness threshold
```

---

## 22. Recovery SLOs

Example targets:

```text
Policy propagation:
99.99% < 5 seconds

Regional catch-up:
99% < 30 seconds after control-plane recovery

Maximum stale policy:
Defined per risk class

RTO:
Region recovery within defined target

RPO:
Near-zero for authoritative policy history
```

These are example targets, not universal defaults; the actual numbers should be derived from business and security requirements.

---

## 23. Recommended Failure Policy

For this architecture:

```text
Global Policy Store outage
        |
        v
Regional authorization continues
using last known valid policy
        |
        v
Monitor age/version lag
        |
        v
Within freshness limit
        |
        v
NORMAL
```

When the limit is exceeded:

```text
Policy too stale
        |
        +--> Allow only approved low-risk operations
        |
        +--> Restrict/deny sensitive operations
        |
        +--> Alert security/operations
```

This avoids both extremes:

```text
Always fail closed
```

and:

```text
Always trust stale policy
```

---

## 24. Architecture Conclusion

> **A policy-store outage should be isolated to the control plane whenever possible. Regional authorization should continue from the last known valid policy, but only within an explicit freshness boundary. Recovery should use durable distribution, version comparison, idempotent replay, integrity verification, and snapshot-based catch-up.**

The core failure model is:

```text
                  GLOBAL POLICY STORE
                          |
                    ┌─────X─────┐
                    |  OUTAGE   |
                    └─────┬─────┘
                          |
                          v
                Regional Policy Copies
                          |
             ┌────────────┼────────────┐
             v            v            v
           India        Europe         US
             |            |            |
          v103         v103         v103
             |            |            |
             v            v            v
           AuthZ        AuthZ        AuthZ
             |            |            |
          continue     continue     continue
             |            |            |
             └────── bounded freshness ──────┘
                          |
                          v
                 Global Store Recovers
                          |
                          v
                     Catch-up / replay
                          |
                          v
                    Verify + activate
                          |
                          v
                     All regions converge
```
