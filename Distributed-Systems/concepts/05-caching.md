# Caching, Cache Invalidation & Authorization-Decision Caching

> **Beginner idea:** A cache is a fast temporary place where we keep information that is expensive or slow to fetch again.
>
> This note explains caching from first principles, then moves into cache invalidation and finally into the security-sensitive problem of **authorization-decision caching**.

---

## 1. Why do we need a cache?

Start with a simple application:

```text
User
  |
  v
Application Server
  |
  v
Database
```

Suppose the database takes 100 ms to answer a request.

If 10,000 users repeatedly ask for the same popular data, the database keeps doing the same work.

A cache gives us:

```text
User
  |
  v
Application
  |
  v
+---------+
|  Cache  |   <-- very fast
+---------+
     |
     | cache miss
     v
+-----------+
| Database  | <-- slower
+-----------+
```

The application first checks the cache.

If the data is already there, it can avoid a database call.

---

# 2. Cache hit vs cache miss

## Cache hit

The requested data is already in the cache.

```text
Application
     |
     v
   Cache
     |
     | FOUND
     v
   Return data
```

This is fast.

## Cache miss

The requested data is not in the cache.

```text
Application
     |
     v
   Cache
     |
     | NOT FOUND
     v
 Database
     |
     v
 Return data
     |
     v
 Store in cache
```

The first request is slower, but later requests can be faster.

---

# 3. Real-world analogy

Imagine a student studying for an exam.

You need a definition from a textbook.

Without a cache:

```text
Question
   |
   v
Walk to library
   |
   v
Find book
   |
   v
Find page
   |
   v
Read answer
```

With a cache:

```text
Question
   |
   v
Check your notes
   |
   v
Answer immediately
```

Your notes are the **cache**.

The textbook is the **database/source of truth**.

The important catch is:

> What happens if your notes are old?

That is the cache invalidation problem.

---

# 4. What makes caching useful?

A cache is useful when:

- the same data is requested repeatedly
- the original source is relatively expensive or slow
- the cached value does not need to be perfectly fresh every millisecond
- reducing latency is valuable
- reducing load on the source system is valuable

A cache is **not automatically good for every piece of data**.

Caching has a cost:

- memory/storage
- cache management
- stale data
- invalidation complexity
- operational complexity
- possible consistency problems

---

# 5. Where can a cache exist?

Caching is not only "Redis between application and database."

There can be several cache layers:

```text
User
  |
  v
Browser Cache
  |
  v
CDN / Edge Cache
  |
  v
Application / Server Cache
  |
  v
Distributed Cache (e.g. Redis)
  |
  v
Database
  |
  v
Database internal cache
```

Different layers solve different problems.

### Example

A browser may cache:

```text
logo.png
CSS
JavaScript
```

A CDN may cache:

```text
images
videos
public web pages
```

A distributed cache may store:

```text
user profiles
session information
expensive query results
authorization decisions
```

---

# 6. The most common pattern: Cache-Aside

For system design, one of the most important patterns is **Cache-Aside**.

```text
              ┌──────────────┐
              │ Application  │
              └──────┬───────┘
                     |
                     v
                ┌────────┐
                │ Cache  │
                └───┬────┘
                    |
              hit?  |  miss?
               /    \
             YES     NO
              |       |
              v       v
           Return   Database
                    |
                    v
                  Cache
                    |
                    v
                  Return
```

### Step-by-step

1. Application asks the cache.
2. If the key exists, return it.
3. If it does not exist, query the database.
4. Put the result in the cache.
5. Return the result.

### Example

Request:

```text
GET /users/123
```

Cache key:

```text
user:123
```

If found:

```text
Cache → user:123 → return user
```

If missing:

```text
Cache MISS
     |
     v
Database → user 123
     |
     v
Cache SET user:123
     |
     v
Return user
```

---

# 7. Other common cache write strategies

## Write-Through

Application writes through the cache.

```text
Application
     |
     v
  Cache
     |
     v
 Database
```

The cache is updated as part of the write path.

### Benefit

Cache and database can be kept more closely aligned.

### Cost

Writes may require more work before the operation completes.

---

## Write-Behind / Write-Back

Application writes to the cache first.

The cache writes to the database later.

```text
Application
     |
     v
  Cache
     |
     | later
     v
 Database
```

### Benefit

Very fast writes can be possible.

### Risk

If the cache fails before data is safely persisted, data can be lost depending on the design.

---

## Write-Around

Application writes directly to the database, while cache is populated later when data is read.

```text
Application
    |
    +-------> Database
    |
    +-------> Cache (later, on read)
```

This can avoid filling the cache with data that is written once and never read.

---

# 8. Why can't we just cache everything?

Because cache is usually a limited resource.

Imagine:

```text
Database:
10 TB

Cache:
100 GB
```

We cannot store everything in cache.

So the system needs **eviction**.

Eviction means:

> Which cached item should we remove when the cache is full?

---

# 9. Common eviction policies

## LRU — Least Recently Used

Remove data that has not been used recently.

```text
Recently used  <---------------->  Not used recently

   A      B      C      D      E
                       ↑
                     evict
```

Good when recent usage predicts future usage.

---

## LFU — Least Frequently Used

Remove data that has been requested the fewest times.

```text
A → 1 use
B → 500 uses
C → 20 uses

Evict A
```

---

## FIFO — First In, First Out

Remove the oldest cached entry first.

---

# 10. TTL — Time To Live

A cache entry can have an expiry time.

For example:

```text
user:123 → profile data
TTL = 5 minutes
```

After 5 minutes:

```text
ENTRY EXPIRED
```

The application fetches fresh data again.

TTL is a very common way to limit how long stale data can live in a cache.

---

# 11. The biggest caching problem: stale data

Suppose the database contains:

```text
User status = ACTIVE
```

Cache also contains:

```text
User status = ACTIVE
```

Now an administrator changes the database:

```text
Database:
User status = DISABLED
```

But cache still contains:

```text
Cache:
User status = ACTIVE
```

Now we have:

```text
Application → Cache → ACTIVE
                  ^
                  |
               STALE
                  |
                  v
             Database
             DISABLED
```

This is called **stale data**.

---

# 12. What is cache invalidation?

Cache invalidation means:

> **Making cached information unusable when the underlying data changes.**

Example:

```text
Database
User role = ADMIN
     |
     | cached
     v
Cache
User role = ADMIN
```

Administrator removes the role:

```text
Database
User role = USER
```

The old cached value must no longer be trusted.

---

# 13. Three important invalidation approaches

## A. TTL-based invalidation

Let the cache entry expire automatically.

```text
Cache value
    |
    v
TTL countdown
    |
    v
Expired
    |
    v
Fetch fresh value
```

### Advantage

Simple.

### Disadvantage

The data can remain stale until the TTL expires.

Example:

```text
TTL = 10 minutes
Permission removed at minute 1

Old decision could remain cached
for up to ~9 more minutes.
```

That delay can be unacceptable for security-sensitive authorization.

---

## B. Explicit invalidation

When data changes, explicitly delete the cache entry.

```text
               DATA CHANGE
                    |
          ┌─────────┴─────────┐
          v                   v
      Database             Cache
      update              DELETE key
```

Example:

```text
UPDATE user 123
     |
     +--> Database updated
     |
     +--> cache.delete("user:123")
```

### Advantage

Can remove stale data quickly.

### Disadvantage

The application must reliably perform both actions.

A failure between them can create inconsistency.

---

## C. Event-driven invalidation

Publish an event when data changes.

```text
Database / Service
        |
        | "permission changed"
        v
   Event / Message
        |
   ┌────┴─────┐
   v          v
Cache A     Cache B
DELETE      DELETE
```

Possible technologies:

- Kafka
- Pub/Sub
- messaging systems
- event buses

The important idea is the event, not the product.

### Advantage

Useful when many application instances have caches.

### Disadvantage

You now have asynchronous delivery and must handle:

- delayed events
- duplicated events
- lost events
- ordering issues
- consumers being offline

---

# 14. Why invalidation is hard

The question is:

```text
Source of truth changes
        |
        v
How do all cached copies learn
that the old value is no longer valid?
```

With one cache, this can be manageable.

With many application instances:

```text
             Application
            /     |     \
           v      v      v
        Cache1  Cache2  Cache3
```

the problem becomes harder.

---

# 15. Distributed cache

When many application instances share one cache:

```text
                    ┌── App 1
Users ── Load ──────┼── App 2
        Balancer    └── App 3
                         |
                         v
                  ┌────────────┐
                  │   Redis    │
                  │ Distributed│
                  │   Cache    │
                  └─────┬──────┘
                        |
                        v
                     Database
```

This avoids every application instance having a completely independent cache.

But the distributed cache itself becomes an important infrastructure dependency.

---

# 16. Cache stampede / thundering herd

Suppose a very popular cache entry expires.

Before expiry:

```text
1,000 users
     |
     v
   Cache HIT
```

Now it expires.

All 1,000 requests miss at nearly the same time:

```text
1,000 requests
      |
      v
Cache MISS
      |
      v
   Database
   Database
   Database
   ...
```

The database can suddenly receive a huge burst.

This is called a **cache stampede** or **thundering herd**.

### Common mitigations

**Request coalescing / single-flight**

```text
100 requests
     |
     v
  Cache miss
     |
     v
One request → Database
     |
     v
Cache populated
     |
     v
Remaining requests → Cache
```

**Jittered TTL**

Instead of all keys expiring at exactly the same instant:

```text
TTL = 300 seconds ± small random jitter
```

This spreads expirations.

**Background refresh**

Refresh important entries before they expire.

---

# 17. Hot keys

A **hot key** is one cache key receiving unusually high traffic.

Example:

```text
product:123
```

might be a viral product.

Then:

```text
1 hot key
     |
     v
Millions of requests
```

Possible approaches:

- local caching
- replication
- key splitting
- request coalescing
- precomputation
- rate limiting

The right solution depends on the workload.

---

# 18. Authorization-decision caching

Now move from ordinary data caching to **authorization caching**.

A normal application asks:

```text
"Give me user 123's profile."
```

An authorization system asks:

```text
"Is user 123 allowed to perform action X on resource Y?"
```

That answer is an **authorization decision**.

Example:

```text
Subject:  user-123
Action:   READ
Resource: payroll/report-456

Decision:
ALLOW
```

---

# 19. Authorization flow without caching

Without a cache:

```text
                   API Request
                       |
                       v
                Authorization
                   Service
                       |
                       v
                Policy / Rules
                       |
                       v
                Decision
               /        \
            ALLOW       DENY
```

At high scale, repeatedly evaluating the same or similar requests can increase authorization-service and policy-store load.

---

# 20. Authorization-decision caching

Instead of calculating the same answer repeatedly:

```text
"Can user-123 READ resource-456?"
```

we can cache the decision.

```text
                     Request
                        |
                        v
              +------------------+
              | AuthZ Decision    |
              | Cache             |
              +--------+---------+
                       |
                    HIT?
                  /       \
                YES        NO
                |           |
                v           v
            ALLOW/DENY   AuthZ Engine
                              |
                              v
                           Decision
                              |
                              v
                             Cache
```

This can reduce:

- authorization-service load
- policy-store load
- latency

---

# 21. Authorization cache key

The cache key must include the information that can affect the decision.

Simplified example:

```text
subject = user-123
action = read
resource = report-456
```

Possible key:

```text
authz:user-123:read:report-456
```

Real systems may also need context such as:

```text
tenant
resource version
policy version
device
location
time
security context
```

The rule is:

> **If a value can change the authorization decision, the cache key or validation strategy must account for it.**

Otherwise, a decision for one situation could be incorrectly reused for another.

---

# 22. Why authorization caching is more dangerous

Normal cache staleness can be inconvenient:

```text
Cache says:
₹999

Database says:
₹1,049
```

Authorization staleness can be a security problem:

```text
Cache says:
ALLOW

Latest policy says:
DENY
```

Example:

```text
09:00
User has admin access
        |
        v
Cache:
ALLOW

09:05
Admin removes admin access
        |
        v
Policy:
DENY

Cache:
still ALLOW
```

A request at 09:06 could incorrectly be authorized if the application trusts the stale cached decision.

Therefore:

> **Authorization caching must treat freshness as a security requirement, not merely a performance preference.**

---

# 23. Authorization cache TTL

Suppose:

```text
ALLOW decision
TTL = 30 seconds
```

After 30 seconds, it expires and the next request re-checks authorization.

### Pros

- simple
- predictable
- bounds how long an old decision can live

### Cons

- stale ALLOW is still possible during the TTL
- short TTL increases cache misses
- increased load on the authorization engine

The correct TTL should come from the application's security requirement.

---

# 24. Explicit invalidation for authorization

When permissions change:

```text
Permission changed
       |
       +----> Update policy store
       |
       +----> Invalidate related cache entries
```

Example:

```text
User 123 removed from Admin role

        |
        +--> policy updated
        |
        +--> invalidate
             authz:user-123:*
```

### The challenge

One permission change can affect many possible decisions:

```text
User
  |
  +-- action A → resource 1
  +-- action A → resource 2
  +-- action B → resource 1
  +-- action B → resource 2
  ...
```

Invalidating every affected decision can become difficult at scale.

---

# 25. Versioned authorization data

Instead of finding and deleting every cached decision, associate a decision with a policy version.

Example:

```text
Current policy version = 42

Cached decision:
ALLOW
policy_version = 42
```

Permission changes:

```text
Current policy version = 43
```

Cached entry still says:

```text
42
```

So:

```text
42 != 43
   |
   v
Cached decision is stale
   |
   v
Re-check authorization
```

This can be an effective approach when policy changes are frequent or fan-out invalidation is expensive.

---

# 26. Event-driven authorization invalidation

A permission change can publish an event:

```text
Administrator changes access
        |
        v
Policy Service
        |
        v
"USER_123_PERMISSIONS_CHANGED"
        |
        v
Event Bus
        |
   ┌────┴─────┐
   v          v
AuthZ Cache  AuthZ Nodes
invalidate   refresh state
```

This can work well for distributed authorization services.

But it is normally asynchronous, so measure:

> **How long can a revoked permission continue to produce an old ALLOW?**

That interval is important.

---

# 27. Fail-open vs fail-closed

Suppose the authorization cache is unavailable:

```text
Authorization Cache
       |
       X
   unavailable
```

What should happen?

## Fail-open

Allow access if authorization cannot be checked.

```text
AuthZ unavailable
       |
       v
ALLOW
```

Availability is better, but security risk increases.

## Fail-closed

Deny access if authorization cannot be verified.

```text
AuthZ unavailable
       |
       v
DENY
```

Security is stronger, but availability can decrease.

For high-risk operations, fail-closed is often the safer default.

The final choice should be explicit and risk-based.

---

# 28. Safer authorization architecture

```text
                         ┌─────────────┐
                         │    Client   │
                         └──────┬──────┘
                                |
                                v
                         ┌─────────────┐
                         │ API / App   │
                         └──────┬──────┘
                                |
                                v
                    ┌────────────────────────┐
                    │ Authorization Decision │
                    │ Cache                  │
                    └────────────┬───────────┘
                              HIT?
                           /        \
                         YES         NO
                         |            |
                         v            v
                    ALLOW/DENY     AuthZ Engine
                                      |
                       ┌──────────────┴─────────────┐
                       v                            v
                Policy / Role Store        Relationship Store
                       |
                       v
                    Decision
                       |
                       v
                 Cache decision
```

Policy-change path:

```text
Admin changes permission
        |
        v
Policy Store
        |
        v
Policy-change event
        |
        v
Invalidate / bump version
        |
        v
Authorization cache
        |
        v
Old decision is no longer trusted
```

---

# 29. Security scenario: employee access revoked

Imagine:

```text
User: Alice
Permission: READ payroll
```

Authorization request:

```text
Alice + READ + payroll
```

Decision:

```text
ALLOW
```

Cached as:

```text
authz:alice:read:payroll → ALLOW
```

Now an administrator revokes access:

```text
Alice
  |
  X
READ payroll removed
```

Policy store:

```text
DENY
```

Cache:

```text
still ALLOW
```

This is the stale-authorization window.

A good design needs a clear mechanism to close that window:

```text
permission change
       |
       v
policy update
       |
       v
invalidate / version bump
       |
       v
old ALLOW cannot be reused
```

---

# 30. The key metric: revocation propagation time

For authorization caching, don't measure only cache hit ratio.

Also measure:

```text
Permission revoked
        |
        v
How long until old ALLOW
can no longer be used?
```

For example:

```text
10:00:00  permission revoked
10:00:02  old cached decision invalid
```

Then:

```text
Revocation propagation time = 2 seconds
```

Whether 2 seconds is acceptable depends on the business and security requirement.

---

# 31. Cache design checklist

When designing any cache, ask:

### What are we caching?

```text
User data?
Query result?
Session?
Authorization decision?
```

### Why are we caching it?

```text
Reduce latency?
Reduce database load?
Reduce authorization load?
```

### What is the cache key?

Can two different requests accidentally share the same key?

### How long can it safely be stale?

```text
1 second?
30 seconds?
5 minutes?
```

### How is invalidation done?

```text
TTL?
Explicit delete?
Event-driven?
Versioning?
```

### What happens on cache miss?

```text
Fetch source?
Retry?
Fail?
```

### What happens if the cache is unavailable?

```text
Fall back?
Fail closed?
Fail open?
```

### What happens during traffic spikes?

```text
Stampede?
Hot key?
Memory pressure?
```

---

# 32. Authorization-specific checklist

For authorization-decision caching, add:

```text
1. What exactly is the decision?
2. What inputs can change the decision?
3. What must be in the cache key?
4. What is the maximum acceptable stale period?
5. How quickly must revocations take effect?
6. How are policy changes signaled?
7. What happens if the cache is unavailable?
8. Is fail-open acceptable?
9. Is fail-closed required?
10. How are tenant boundaries enforced?
11. How do we prevent old ALLOW decisions from surviving a revocation?
12. How is cache correctness monitored?
```

---

# 33. Common mistakes

## Mistake 1: Using a long TTL for authorization

```text
Long TTL
   ↓
Long stale window
   ↓
Old ALLOW survives longer
```

That may violate the security requirement.

---

## Mistake 2: Invalidating everything

A broad invalidation can create:

```text
Cache purge
    |
    v
Huge cache miss spike
    |
    v
Authorization engine overloaded
```

Targeted invalidation or versioning may be more appropriate.

---

## Mistake 3: Ignoring cache failure

Always define:

```text
Cache unavailable
       |
       +--> Re-check authorization?
       |
       +--> Deny?
       |
       +--> Allow?
```

Do not leave this behavior implicit.

---

## Mistake 4: Making the cache key too small

Bad:

```text
authz:user-123 → ALLOW
```

That may accidentally reuse the same decision for:

```text
different action
different resource
different tenant
different context
```

The key or validation mechanism must reflect decision inputs.

---

# 34. Putting everything together

```text
                        USER REQUEST
                             |
                             v
                       Application
                             |
                             v
                   Authorization Cache
                             |
                          HIT?
                       /         \
                    YES           NO
                    |              |
                    v              v
               ALLOW/DENY     Authorization Engine
                                   |
                           ┌───────┴────────┐
                           v                v
                       Policies        Relationships
                           |
                           v
                        Decision
                           |
                           v
                    Cache with TTL /
                    version / invalidation
```

Meanwhile:

```text
             ADMINISTRATOR CHANGES ACCESS
                         |
                         v
                    Policy Store
                         |
                         v
                Change Event / Version
                         |
                         v
                 Cache invalidation
                         |
                         v
                Old decision unusable
```

This gives you the complete mental model:

```text
CACHE
  ↓
Improve performance
  ↓
But cached data can become stale
  ↓
Therefore invalidation is required
  ↓
Authorization decisions can also be cached
  ↓
But stale ALLOW decisions are security-sensitive
  ↓
Therefore TTL + invalidation/versioning +
failure behavior must be designed explicitly
```

---

# 35. Interview / architecture questions to practice

Try answering these without looking at the note:

1. Why do we use a cache?
2. What is a cache hit vs cache miss?
3. Why is Cache-Aside so common?
4. What is stale data?
5. Why is cache invalidation difficult?
6. What is TTL?
7. What is cache stampede?
8. What is a hot key?
9. Why might a distributed cache be used?
10. Why is authorization-decision caching different from caching product data?
11. What happens when a user loses a permission but an old ALLOW is still cached?
12. How would you invalidate an authorization decision?
13. Why might policy versioning help?
14. What should happen if the authorization cache is unavailable?
15. What metric tells you how quickly a revoked permission takes effect?

---

# 36. One-minute explanation

> "Caching stores frequently used information in a faster layer so requests can be served with lower latency and less load on the underlying source. Cache-Aside is a common pattern where the application checks the cache first and loads from the source on a miss. The main challenge is stale data, so systems use techniques such as TTL, explicit invalidation, events, and versioning. Authorization-decision caching applies the same idea to ALLOW/DENY results, but stale decisions are security-sensitive: if a user's permission is revoked while an old ALLOW is cached, the system could incorrectly grant access. Therefore authorization caching must explicitly design the cache key, maximum stale period, revocation/invalidation mechanism, and fail-open/fail-closed behavior."

---

# 37. Source video used for the caching portion

**Hello Interview — "Caching in System Design Interviews w/ Meta Staff Engineer"**

YouTube:
https://www.youtube.com/watch?v=1NngTUYPdpI

The video covers:

```text
00:49   What is caching
01:52   Where to cache
07:57   Guided practice
09:59   Cache architectures
14:58   Cache eviction policies
17:21   Common issues / Deep dives
25:33   Caching in system design interviews
29:43   Conclusion
```

The caching sections above are organized around these topics and extended with additional material on **authorization-decision caching**, which is specifically relevant to IAM/security architecture.

---

# 38. Final cheat sheet

```text
CACHE
= fast temporary copy

CACHE HIT
= data found in cache

CACHE MISS
= data not found in cache

TTL
= automatic expiry after a period

INVALIDATION
= make old cached data unusable

CACHE-ASIDE
= read cache → on miss read source → populate cache

STAMPede
= many requests miss together and overload source

HOT KEY
= one cache key gets huge traffic

AUTHORIZATION CACHE
= cache ALLOW/DENY decisions

SECURITY QUESTION
= how quickly must a revoked permission stop producing ALLOW?

COMMON CONTROLS
= TTL
+ explicit invalidation
+ event-driven invalidation
+ versioning
+ fail-closed where appropriate
```
