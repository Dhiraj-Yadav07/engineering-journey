# Consistency Models

> **Beginner idea:** A consistency model is a set of rules describing **what users are allowed to see when data is stored on multiple computers**.

---

# 1. Why do we need consistency models?

Suppose an application has three database servers:

```text
             Application
                  |
          ┌───────┼───────┐
          ▼       ▼       ▼
        DB-A    DB-B    DB-C
```

All three contain copies of the same data.

Initially:

```text
A → 100
B → 100
C → 100
```

Now a user changes the value:

```text
WRITE = 200
```

The update may reach the servers at slightly different times:

```text
A → 200
B → 100
C → 100
```

For a short period, different servers disagree.

The question becomes:

> **What should a user see if they read the data right now?**

That is what consistency models help define.

---

# 2. Think of consistency as a rulebook

A consistency model tells us things like:

- Can a user see an old value?
- Do all users see updates in the same order?
- Must related updates appear in the same order?
- How quickly must replicas agree?

It is useful to think of consistency as a **spectrum**, not just "consistent" vs "inconsistent."

---

# 3. Strong consistency

At a beginner level, think:

> **Once an update is successfully accepted, later reads should see that update rather than an older value.**

Example:

```text
WRITE:
balance = ₹700
       |
       v
"Success"
       |
       v
READ:
balance = ₹700
```

A user should not immediately receive:

```text
balance = ₹1,000
```

from another replica.

### Real-world examples

Strong consistency is valuable for:

- bank balances
- inventory reservation
- critical authorization state
- unique resource allocation

---

# 4. Linearizability

Linearizability is a very strong consistency guarantee.

A useful beginner mental model is:

> **The distributed system should behave as if there is one correct copy of the data, and operations take effect at one point in time between their start and completion.**

Example:

```text
10:00:00  WRITE x = 20 succeeds
10:00:01  READ x
```

The read should observe:

```text
x = 20
```

rather than an older value.

### Important

Linearizability is stronger and more precise than simply saying:

> "The database is strongly consistent."

---

# 5. Sequential consistency

Sequential consistency says:

> **All operations should appear to happen in one global order, while preserving the order of operations from each individual client.**

Imagine Client A performs:

```text
1. WRITE X = 10
2. WRITE X = 20
```

The system must not make Client A's actions appear as:

```text
20 → 10
```

But the exact global timing can be less strict than linearizability.

### Beginner takeaway

```text
Linearizability
      ↓
Very strong real-time guarantee

Sequential consistency
      ↓
One common ordering, but weaker real-time requirement
```

For your first pass, you do not need to master the formal proof definitions.

---

# 6. Causal consistency

Causal consistency deals with **cause and effect**.

Imagine:

```text
Alice creates post
       |
       v
Bob comments on post
```

There is a causal relationship:

```text
Post created → Comment created
```

It would be strange for another user to observe:

```text
Bob's comment
       ↓
Alice's post
```

because the comment logically depends on the post.

Causal consistency says:

> **If operation B depends on operation A, everyone should observe A before B.**

But two unrelated operations may not have to appear in the same order everywhere.

---

# 7. Eventual consistency

Eventual consistency says:

> **If updates stop, all replicas will eventually converge to the same value.**

Example:

```text
At time T1:

A → 101
B → 100
C → 100
```

Later:

```text
A → 101
B → 101
C → 101
```

The system allowed temporary differences.

### This can be useful for:

- likes
- view counters
- social feeds
- product recommendations
- distributed caches
- some content systems

---

# 8. Real-world analogy: notice boards

Imagine three offices:

```text
Office A   Office B   Office C
   |          |          |
 notice      notice     notice
 board       board      board
```

A new announcement is published.

### Strong consistency

Nobody displays it until every office has received it.

```text
A ✅
B ✅
C ✅
```

Advantage:

- Everyone sees the same information.

Cost:

- You may have to wait.

### Eventual consistency

Office A posts it immediately.

B and C receive it slightly later:

```text
A ✅
B ⏳
C ⏳
```

A few seconds later:

```text
A ✅
B ✅
C ✅
```

Advantage:

- Faster response.
- Better availability.

Cost:

- Temporary disagreement.

---

# 9. Why not always use the strongest consistency?

Because stronger guarantees often require more coordination.

Imagine three servers:

```text
A
B
C
```

To guarantee a very strong result, the system may need communication such as:

```text
A → B → "Did you receive it?"
A → C → "Did you receive it?"
B/C → A → "Yes"
```

More communication can mean:

- higher latency
- more network dependency
- more failure sensitivity
- lower availability during outages

So the architectural question becomes:

> **How much consistency does this business operation actually need?**

---

# 10. Example: bank balance

Suppose:

```text
Balance = ₹10,000
```

Customer withdraws:

```text
₹8,000
```

A system that allows one replica to continue reporting:

```text
₹10,000
```

after the withdrawal has successfully completed can create serious problems.

So strong consistency is usually much more important here.

---

# 11. Example: social-media likes

Suppose:

```text
Like count = 10,000
```

After a user clicks Like:

```text
Server A → 10,001
Server B → 10,000
```

for a brief time.

Most users will not care.

Eventually:

```text
A → 10,001
B → 10,001
C → 10,001
```

Eventual consistency can therefore be a reasonable trade-off.

---

# 12. Example: inventory

Suppose an online store has:

```text
1 laptop remaining
```

Two customers try to buy it simultaneously.

You do not want:

```text
Customer A → purchased ✅
Customer B → purchased ✅
```

when only one item exists.

This is a case where the **reservation/stock decrement operation** may need a stronger consistency guarantee.

---

# 13. A simple consistency spectrum

You can visualize consistency roughly like this:

```text
Stronger guarantees
        |
        v
+----------------------+
| Linearizable         |
+----------------------+
| Sequential           |
+----------------------+
| Causal               |
+----------------------+
| Eventual / weaker    |
+----------------------+
        |
        v
More freedom for replicas to temporarily disagree
```

This diagram is a learning aid, not a complete formal classification. Real consistency models have more nuance and some do not form one simple straight line.

---

# 14. Stale reads

One of the most important practical ideas is the **stale read**.

Suppose:

```text
A → 200
B → 100
```

Your application reads from B.

It receives:

```text
100
```

even though the latest update was:

```text
200
```

That's a stale read.

A system with stronger consistency guarantees works harder to prevent or bound this behavior.

---

# 15. Read-after-write consistency

Another useful concept is:

> **After I successfully write something, I should be able to read that change.**

Example:

```text
You update your profile:

Name = "Dhiraj"
        |
        v
Save successful
        |
        v
Open profile
        |
        v
Name = "Dhiraj"
```

If the next read shows the old name because it went to a lagging replica, the user experience is confusing.

Read-after-write consistency is often an important application-level requirement.

---

# 16. Consistency is a business decision

The correct question is not:

> "Which consistency model is best?"

The better question is:

> **"What consistency guarantee does this particular piece of data require?"**

Example:

| Data | Typical requirement |
|---|---|
| Bank transaction | Very strong |
| Stock reservation | Strong |
| User profile | Moderate / often session-aware |
| Social feed | Can often tolerate eventual consistency |
| Like counter | Can often tolerate eventual consistency |
| Product description | Temporary staleness may be acceptable |

The same application can use **different consistency guarantees for different operations**.

---

# 17. Consistency vs latency

A common trade-off looks like:

```text
More coordination
       |
       v
Stronger consistency
       |
       v
Potentially higher latency
       |
       v
Potentially lower availability during failures
```

Whereas:

```text
Less coordination
       |
       v
Weaker consistency
       |
       v
Potentially lower latency
       |
       v
Potentially higher availability
```

This is a trade-off, not an absolute law.

---

# 18. Quick comparison

| Model | Beginner description | Typical use |
|---|---|---|
| Linearizability | Behave like one current copy of the data | Critical operations |
| Sequential | One common operation order, preserving each client's order | Distributed coordination scenarios |
| Causal | Cause must be seen before its effect | Social/collaborative systems |
| Eventual | Replicas may differ temporarily but eventually converge | Feeds, counters, some content |

---

# 19. One-minute explanation

> "Consistency models define what users are allowed to observe when data is replicated across multiple computers. Strong models such as linearizability provide very strong guarantees that reads reflect completed writes, while weaker models such as eventual consistency allow temporary differences between replicas as long as they eventually converge. Stronger guarantees usually require more coordination, which can increase latency and reduce availability during failures. The right consistency model depends on the business requirement."

---

# 20. Key terms

**Replica**  
A copy of the data.

**Stale read**  
Reading an older value when a newer value exists.

**Strong consistency**  
A strong guarantee that reads reflect the appropriate latest state.

**Linearizability**  
A strong model in which operations behave like operations on one authoritative copy in real-time order.

**Causal consistency**  
Cause-and-effect relationships are preserved.

**Eventual consistency**  
Replicas eventually converge if updates stop.

**Read-after-write**  
A successful write should be observable by a subsequent read according to the model's guarantee.

---

# 21. What to understand before moving on

You should be able to explain:

```text
Multiple replicas
       ↓
Replicas can temporarily differ
       ↓
Consistency model defines what users can observe
       ↓
Stronger guarantees usually need more coordination
       ↓
More coordination can cost latency/availability
```

Next, study **replication** to understand how those multiple copies are actually maintained.
