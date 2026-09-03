# Quorum

> **Beginner idea:** A quorum is a rule that says **how many members of a group need to participate or agree for an operation to be accepted**.

---

# 1. Start with a simple voting example

Imagine 5 people are deciding something:

```text
A   B   C   D   E
```

Suppose the rule is:

> At least 3 votes are required.

Then:

```text
A ✅
B ✅
C ✅
D ❌
E ❌
```

There are 3 votes.

The decision can pass.

That is the basic idea of a **quorum**:

> **Enough members must participate to form an acceptable group.**

Distributed systems use a similar idea with replicas.

---

# 2. Quorum with databases

Suppose we have 3 replicas:

```text
A
B
C
```

We define:

```text
N = 3
```

where N means:

> **Number of replicas holding the data.**

We might require 2 replicas to acknowledge a write:

```text
A ✅
B ✅
C
```

That is a write quorum of:

```text
W = 2
```

---

# 3. Why not require only one?

Suppose:

```text
A
B
C
```

A write only needs one replica:

```text
A ✅
B
C
```

This is fast.

But now imagine A contains the newest value and B/C do not.

A failure could make the system lose access to the only replica that has the latest update.

So requiring more replicas can improve durability/consistency properties, depending on the system.

---

# 4. Read quorum

Now suppose we want to read.

We could require:

```text
A ✅
B ✅
C
```

So:

```text
R = 2
```

where R means:

> **Number of replicas participating in a read.**

Now we have:

```text
N = 3
R = 2
W = 2
```

---

# 5. The important formula

A common quorum relationship is:

\[
R + W > N
\]

For example:

```text
N = 3
R = 2
W = 2
```

Calculate:

```text
2 + 2 = 4
4 > 3
```

So:

```text
R + W > N
```

is satisfied.

---

# 6. Why does this matter?

Because the read group and write group must overlap.

Imagine:

```text
Replicas:

A   B   C
```

The write reaches:

```text
A   B
```

The read checks:

```text
B   C
```

The two groups overlap at:

```text
B
```

That overlapping replica can contain the new value.

Conceptually:

```text
WRITE QUORUM
   A   B
       ↑
       |
     overlap
       |
       ↓
READ QUORUM
   B   C
```

This is the intuition behind the quorum formula.

---

# 7. A real-world analogy

Imagine 3 offices maintain the same document:

```text
Office A
Office B
Office C
```

The rule says:

> "At least 2 offices must receive an update before it is considered accepted."

You update the document:

```text
A ✅
B ✅
C ❌
```

Later, you ask two offices for the current document:

```text
B ✅
C ✅
```

Because B was involved in the earlier write, the read has a chance to discover the new version.

Again, the exact guarantees depend on the database's consistency protocol, conflict handling, and failure assumptions. The quorum equation is a useful foundation, not a complete consistency proof by itself.

---

# 8. What happens if R + W is NOT greater than N?

Suppose:

```text
N = 3
R = 1
W = 1
```

Then:

```text
R + W = 2
```

and:

```text
2 > 3 ❌
```

There is no guaranteed overlap.

Example:

```text
Write → A

Read → B
```

The read may never contact the replica that received the latest write.

So a stale value could be returned.

---

# 9. Common configurations

For:

```text
N = 3
```

### R = 1, W = 1

```text
R + W = 2
2 > 3 ❌
```

Advantages:

- lower latency
- higher availability

Potential downside:

- weaker read freshness/intersection guarantees

---

### R = 2, W = 2

```text
R + W = 4
4 > 3 ✅
```

Advantages:

- stronger quorum intersection

Costs:

- more replicas must respond
- potentially higher latency
- potentially lower availability when failures occur

---

### R = 3, W = 3

```text
R + W = 6
6 > 3 ✅
```

Very strict.

Every replica must participate.

That means one unavailable replica could prevent the operation.

---

# 10. Majority quorum

For 3 replicas:

```text
A
B
C
```

a majority is:

```text
2
```

For 5 replicas:

```text
A
B
C
D
E
```

a majority is:

```text
3
```

For 7 replicas:

```text
A
B
C
D
E
F
G
```

a majority is:

```text
4
```

General idea:

```text
Majority = floor(N / 2) + 1
```

Examples:

```text
N = 3 → 2
N = 5 → 3
N = 7 → 4
```

---

# 11. Why majority matters

Suppose 5 replicas exist:

```text
A B C D E
```

A network partition creates:

```text
A B | C D E
```

Left side:

```text
2 replicas
```

Right side:

```text
3 replicas
```

Only the side with the majority can satisfy:

```text
3 / 5
```

This helps prevent **two disconnected groups from both believing they have the majority**.

That idea is very important in distributed coordination.

---

# 12. Quorum and failures

Suppose:

```text
N = 3
W = 2
```

One replica fails:

```text
A ✅
B ✅
C ❌
```

We still have 2 available replicas.

The write can potentially succeed.

But if two replicas fail:

```text
A ✅
B ❌
C ❌
```

only one remains.

We cannot satisfy:

```text
W = 2
```

So the write may fail.

This shows the trade-off:

> **A higher quorum gives stronger guarantees but makes the system more sensitive to replica failures.**

---

# 13. Quorum and latency

Suppose replicas are:

```text
A → 10 ms away
B → 15 ms away
C → 200 ms away
```

If your configuration requires only the fastest 2 replicas:

```text
A + B
```

the operation can finish around the slower of those required responses.

If your configuration requires all 3:

```text
A + B + C
```

you may have to wait for C.

So higher participation can increase latency.

This becomes especially important when replicas are in different regions.

---

# 14. Quorum and availability

Imagine:

```text
N = 3
```

If you require:

```text
W = 3
```

then all three need to be available.

If one goes down:

```text
A ✅
B ✅
C ❌
```

the write may fail.

With:

```text
W = 2
```

it can potentially continue.

So:

```text
Higher W
  ↓
More coordination
  ↓
Potentially stronger guarantee
  ↓
Potentially lower availability
```

---

# 15. Read quorum example

Suppose:

```text
N = 3
R = 2
```

The replicas contain:

```text
A → 200
B → 200
C → 100
```

A read contacts:

```text
A + C
```

The system sees:

```text
200
100
```

It can compare versions and choose the newer value according to the database's conflict/versioning rules.

This is why quorum reads are more than just "ask two servers."

The system needs some mechanism to determine which value/version wins.

---

# 16. Versioning matters

Suppose the responses are:

```text
A → value 200, version 8
B → value 100, version 7
```

The application/database can identify:

```text
version 8 > version 7
```

and therefore know that 200 is the newer version.

Distributed systems often use some form of:

- version numbers
- timestamps
- logical clocks
- vector clocks
- consensus/log positions

The exact mechanism depends on the system.

You don't need to learn those deeply yet.

---

# 17. Quorum does NOT magically guarantee everything

This is an important advanced point.

Do not think:

> "R + W > N means the database is always strongly consistent."

Not necessarily.

Actual behavior also depends on:

- how replicas detect newer versions
- conflict resolution
- concurrent writes
- read repair
- hinted handoff
- failure detection
- network partitions
- implementation details
- the database's consistency guarantees

So the formula should be treated as:

> **A fundamental quorum intersection rule, not a complete distributed-consistency theorem for every database.**

---

# 18. Quorum with 5 replicas

Suppose:

```text
N = 5
```

Choose:

```text
R = 3
W = 3
```

Then:

```text
R + W = 6
6 > 5 ✅
```

Possible write quorum:

```text
A B C
```

Possible read quorum:

```text
C D E
```

Overlap:

```text
        C
        ↑
Write → A B C
Read  → C D E
```

Again, the read and write groups cannot be completely disjoint.

---

# 19. Quorum vs replication

These are different concepts.

### Replication

Answers:

> **How many copies of the data do we maintain?**

Example:

```text
N = 3
```

### Quorum

Answers:

> **How many copies need to participate in this particular operation?**

Example:

```text
W = 2
R = 2
```

So:

```text
Replication → How many copies?

Quorum → How many copies participate?
```

This distinction is worth remembering.

---

# 20. Quorum vs CAP

These also solve different problems.

### CAP

Helps us reason about:

> **What trade-off happens during a network partition?**

### Quorum

Helps us reason about:

> **How many replicas should participate in reads/writes?**

Relationship:

```text
           Distributed System
                   |
          ┌────────┴────────┐
          |                 |
         CAP             Quorum
          |                 |
  Partition trade-off   Replica participation
```

They are related, but they are not the same concept.

---

# 21. Putting everything together

This is the mental model you should now have:

```text
                 Distributed System
                         |
                         v
                 Multiple machines
                         |
                         v
                     Replication
                         |
                         v
                   Multiple copies
                         |
                         v
               Copies can disagree
                         |
              ┌──────────┴──────────┐
              |                     |
         Consistency              Quorum
              |                     |
      What users can see     How many replicas
                             participate
              |
              v
             CAP
              |
      What happens during
      network partition?
```

This is the big picture.

---

# 22. One-minute explanation

> "A quorum is the minimum number of replicas that must participate in an operation. If there are N replicas, R is the read quorum and W is the write quorum. A common quorum condition is R + W > N, which ensures that read and write quorums overlap. For example, with N=3, R=2 and W=2, every read quorum intersects every write quorum. Larger quorum requirements can provide stronger intersection guarantees, but they can also increase latency and reduce availability when replicas are unavailable."

---

# 23. Cheat sheet

```text
N = total number of replicas
R = read quorum
W = write quorum

Common quorum condition:

R + W > N
```

Example:

```text
N = 3
R = 2
W = 2

2 + 2 > 3 ✅
```

---

# 24. Key terms

**Quorum**  
Enough replicas participating to satisfy an operation's rule.

**N**  
Number of replicas.

**R**  
Number of replicas required for a read.

**W**  
Number of replicas required for a write.

**Majority**  
More than half of the replicas.

**Quorum intersection**  
The read and write groups share at least one replica when the quorum condition is satisfied.

**Replication**  
Maintaining multiple copies.

---

# 25. What you should now be able to explain

You should be comfortable explaining these relationships:

```text
Replication
= multiple copies

Quorum
= how many copies participate

Consistency model
= what users are allowed to observe

CAP
= what trade-off matters during partition
```

Those four ideas form a strong beginner foundation for distributed systems.
