# CAP Theorem

> **Beginner idea:** CAP helps us understand what a distributed system should do when computers cannot communicate with each other.

---

## 1. First: Why do we need distributed systems?

Imagine one computer running an application:

```text
User
  |
  v
[ One Server ]
  |
  v
[ Database ]
```

This is simple, but the server can become a bottleneck or a single point of failure.

So we may use several computers:

```text
                 ┌── Server A
Users ───────────┼── Server B
                 └── Server C
```

Now the computers have to communicate over a network.

That creates a new problem:

> **What happens when the computers cannot communicate?**

That is where CAP becomes useful.

---

# 2. What does CAP mean?

CAP stands for:

| Letter | Meaning | Beginner-friendly meaning |
|---|---|---|
| C | Consistency | Different computers should agree on the data |
| A | Availability | The system should keep responding |
| P | Partition Tolerance | The system should keep working even when communication between computers breaks |

The important point is:

> **CAP is mainly about what happens when a network partition occurs.**

A network partition means the computers may still be running, but they cannot talk to each other.

---

# 3. What is a network partition?

Imagine three database servers:

```text
          Database cluster

       ┌─────┐
       │  A  │
       └─────┘
          |
       ┌──┴──┐
       │network
       └──┬──┘
      ┌───┼───┐
      ▼   ▼   ▼
     A   B   C
```

Now the network connection breaks between A and B/C:

```text
        Network failure

             X
             |
        ┌────┴────┐
        │         │
       A        B   C
```

A is alive.

B is alive.

C is alive.

But A cannot communicate with B and C.

That is a **partition**.

---

# 4. Consistency (C)

Think of consistency as:

> **"Do I get the correct/latest agreed-upon answer?"**

Suppose all three servers contain:

```text
A = ₹100
B = ₹100
C = ₹100
```

A customer spends ₹30.

A strongly consistent system wants the successful operation to produce:

```text
A = ₹70
B = ₹70
C = ₹70
```

It does not want a user to immediately read:

```text
₹100
```

from another replica after the system has already confirmed the change.

### Simple analogy

Three people are keeping the same bank balance in notebooks.

Consistency means:

> "The notebooks should not disagree about the official balance."

---

# 5. Availability (A)

Availability means:

> **"Can the system still answer my request?"**

Suppose server A fails:

```text
A ❌
B ✅
C ✅
```

An available system may still answer the user using B or C.

A less available design might return:

```text
Service unavailable.
Please try again later.
```

So:

```text
Availability = The system keeps responding.
```

---

# 6. Partition Tolerance (P)

Partition tolerance means:

> **"The system can tolerate a communication failure between parts of the system."**

Example:

```text
             network
               X
               |
        ┌──────┴──────┐
        │             │
        A            B C
```

A and B/C cannot communicate.

In a real distributed system, network failures can happen, so architects usually have to design for this situation.

That means the important choice becomes:

> **During the partition, should we prefer consistency or availability?**

---

# 7. CP vs AP

## CP: Consistency + Partition Tolerance

A CP-oriented system says:

> "I would rather reject or delay some requests than return data that may be wrong or conflicting."

Example:

```text
A | B C
```

If A cannot coordinate with the required replicas, it may refuse a write.

Trade-off:

```text
Consistency   ✅
Partition tolerance ✅
Availability  ❌ (during some failures)
```

### When can this make sense?

- Bank transactions
- Distributed locks
- Critical inventory allocation
- Systems where incorrect state is dangerous

---

## AP: Availability + Partition Tolerance

An AP-oriented system says:

> "I want to keep serving requests even when replicas cannot communicate."

It may accept a change on one side:

```text
A = ₹70
```

while the other side temporarily has:

```text
B = ₹100
C = ₹100
```

The system later reconciles the data.

Trade-off:

```text
Availability  ✅
Partition tolerance ✅
Immediate consistency ❌
```

### When can this make sense?

- Social feeds
- Some shopping-cart systems
- Likes/views/counters
- Applications where temporary differences are acceptable

---

# 8. A simple real-world example

Imagine two bank branches:

```text
Mumbai branch  <----network---->  Delhi branch
```

Both know that an account contains:

```text
₹10,000
```

Now their network connection breaks:

```text
Mumbai branch   X   Delhi branch
```

A customer at Mumbai wants to withdraw ₹8,000.

### CP-style decision

Mumbai says:

> "I cannot verify what Delhi knows. I will not approve the transaction."

This protects consistency.

### AP-style decision

Mumbai says:

> "I will approve the transaction using the information I have."

This keeps the service available, but could create conflicting state if Delhi also processes another transaction.

---

# 9. The CAP statement you should remember

Do **not** memorize only:

> "You can have only two of CAP."

A better mental model is:

```text
                 Network partition
                        |
              ┌─────────┴─────────┐
              |                   |
      Protect consistency    Keep serving users
              |                   |
             CP                  AP
```

The trade-off matters **during the partition**.

---

# 10. CAP is not a database label forever

Avoid statements like:

> "Database X is CP."

That is often too simplistic.

Actual behavior depends on:

- configuration
- replication design
- consistency settings
- quorum settings
- failure scenario
- transaction semantics

A better statement is:

> "Under this configuration and failure scenario, the system chooses this consistency/availability trade-off."

---

# 11. CAP vs normal failures

There is an important distinction:

### Server failure

```text
A ❌
B ✅
C ✅
```

This is a node failure.

### Network partition

```text
A  X  B C
```

The nodes may all be healthy but cannot communicate.

CAP is specifically concerned with the second case.

---

# 12. Where replication fits

CAP becomes relevant because distributed systems often **replicate** data.

```text
             Data
               |
       ┌───────┼───────┐
       ▼       ▼       ▼
       A       B       C
```

Now the system has multiple copies.

If one copy changes before the others, the replicas can temporarily disagree.

So:

```text
Replication
     ↓
Multiple copies
     ↓
Copies can diverge
     ↓
Consistency becomes a problem
     ↓
Network partitions make the problem harder
     ↓
CAP trade-off
```

---

# 13. Example: social media

Suppose a post has:

```text
100 likes
```

A user clicks Like.

For a short time:

```text
Server A → 101
Server B → 100
Server C → 100
```

This may be acceptable.

A little later:

```text
Server A → 101
Server B → 101
Server C → 101
```

For a like counter, temporary inconsistency is often acceptable.

For a bank balance, it may not be.

This is why:

> **CAP is a business decision as well as a technical decision.**

---

# 14. Quick decision guide

| Requirement | Usually favor |
|---|---|
| Incorrect state is dangerous | Stronger consistency / CP-style behavior |
| System must keep serving during partitions | Availability / AP-style behavior |
| Temporary stale values are acceptable | Eventual consistency can be appropriate |
| Financial correctness is critical | Stronger consistency |
| Feed/like/count can be slightly stale | Weaker consistency can be acceptable |

---

# 15. One-minute explanation

If someone asks:

> "What is CAP theorem?"

You can answer:

> "CAP describes the trade-off a distributed system faces when a network partition prevents parts of the system from communicating. Consistency means users see an agreed-upon view of the data, availability means the system continues responding, and partition tolerance means the system tolerates the communication failure. Because network partitions must be considered in distributed systems, the practical choice during a partition is often between protecting consistency (CP) and continuing to serve requests (AP)."

---

# 16. Key terms

**Distributed system**  
Multiple computers working together as one system.

**Replica**  
Another copy of data.

**Consistency**  
How strongly the system guarantees that reads see the correct/agreed state.

**Availability**  
Whether the system continues responding.

**Network partition**  
A communication failure that separates parts of the distributed system.

**CP**  
Prefer consistency during a partition.

**AP**  
Prefer availability during a partition.

---

# 17. What to learn next

CAP becomes much easier after you understand:

1. Consistency models
2. Replication
3. Quorum

Those concepts explain *how* real distributed systems implement the trade-offs discussed by CAP.
