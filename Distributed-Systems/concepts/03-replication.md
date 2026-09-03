# Replication

> **Beginner idea:** Replication means keeping **multiple copies of the same data** on different computers.

---

# 1. Why do we replicate data?

Suppose your application has one database:

```text
Users
  |
  v
[ Database ]
```

If the database fails:

```text
[ Database ] ❌
```

your application may stop working.

Now create copies:

```text
               ┌── Database A
Application ───┼── Database B
               └── Database C
```

If A fails:

```text
A ❌
B ✅
C ✅
```

the system can potentially continue.

Replication gives us:

- fault tolerance
- higher availability
- read scaling
- geographic copies
- protection against a single database failure

---

# 2. What is a replica?

A **replica** is another copy of data.

Suppose we have:

```text
Customer balance = ₹10,000
```

The database cluster might contain:

```text
Replica A → ₹10,000
Replica B → ₹10,000
Replica C → ₹10,000
```

All three are replicas of the same logical data.

---

# 3. The benefit: failure tolerance

Without replication:

```text
Database
   |
   X
Crash
   |
   v
Application unavailable
```

With replication:

```text
        ┌── A ✅
Client ─┼── B ✅
        └── C ❌
```

Two replicas remain available.

This is the main reason replication exists.

---

# 4. The hidden problem

Replication sounds perfect.

But now imagine:

```text
A → ₹100
B → ₹100
C → ₹100
```

A user updates the balance to:

```text
₹70
```

But the update reaches replicas at different times:

```text
A → ₹70
B → ₹100
C → ₹100
```

Now the replicas disagree.

This creates questions such as:

- Which replica should answer a read?
- How quickly must updates reach the other replicas?
- What happens if a replica is offline?
- What happens if two replicas receive different writes?

So:

> **Replication improves reliability but creates distributed-consistency problems.**

---

# 5. Primary-replica architecture

One common design is:

```text
              WRITE
                |
                v
          ┌───────────┐
          │  Primary  │
          └─────┬─────┘
                |
        ┌───────┴───────┐
        ▼               ▼
    Replica B        Replica C
```

The primary receives writes and sends them to replicas.

This is commonly called:

- leader/follower
- primary/replica
- primary/secondary

Different technologies use different terminology.

---

# 6. Why use a primary?

A primary gives the system a simple place to decide:

> "What is the order of writes?"

For example:

```text
Write 1: balance = ₹90
Write 2: balance = ₹70
Write 3: balance = ₹50
```

The primary can establish:

```text
1 → 2 → 3
```

and replicas follow that sequence.

This reduces write conflicts compared with allowing every replica to independently accept writes.

---

# 7. Read scaling

Replication can also help with reads.

Suppose the application receives:

```text
1 million read requests
```

Instead of sending every read to one database:

```text
                    ┌── A
Users → App → Load ─┼── B
                    └── C
```

reads can potentially be spread across replicas.

This can increase read capacity.

But there is a catch:

> **A replica may be behind the primary.**

That is replication lag.

---

# 8. Replication lag

Suppose the primary has:

```text
Balance = ₹70
```

but a replica has not received the update yet:

```text
Primary → ₹70
Replica  → ₹100
```

The replica is lagging.

A read routed there could return:

```text
₹100
```

even though the current value is:

```text
₹70
```

That is one reason consistency models matter.

---

# 9. Synchronous replication

In a simplified synchronous design:

```text
Client
  |
  v
Primary
  |
  +----> Replica B
  |
  +----> Replica C

Wait for required acknowledgements
  |
  v
Return success
```

The primary waits for replicas to confirm the update before declaring the operation successful, depending on the configured policy.

### Benefits

- replicas are more up-to-date
- stronger consistency can be achieved

### Costs

- more network communication
- higher latency
- a slow/unavailable replica can delay the write

---

# 10. Asynchronous replication

In asynchronous replication:

```text
Client
  |
  v
Primary
  |
  v
"Success"
  |
  +----> Replica B   (later)
  |
  +----> Replica C   (later)
```

The primary can acknowledge the write before every replica has received it.

### Benefits

- lower write latency
- better tolerance of slow replicas
- higher availability

### Cost

A replica can temporarily lag behind.

If the primary fails before an update reaches a replica, recovery becomes more complicated and data-loss scenarios may be possible depending on the architecture.

---

# 11. Synchronous vs asynchronous

| | Synchronous | Asynchronous |
|---|---|---|
| Replica freshness | Higher | Can lag |
| Write latency | Usually higher | Usually lower |
| Failure sensitivity | Higher | Lower |
| Complexity | Higher coordination | More lag/recovery concerns |
| Typical idea | "Confirm before success" | "Acknowledge now, replicate later" |

---

# 12. Multi-leader replication

What if several locations need to accept writes?

Example:

```text
India           Europe
  |               |
Leader A  <----> Leader B
```

Both leaders can accept writes.

This can be useful for geographically distributed systems.

But now imagine:

```text
Leader A:
balance = 100 → 80

Leader B:
balance = 100 → 70
```

Which one is correct?

Now the system needs **conflict resolution**.

That is the major cost of multi-leader designs.

---

# 13. Leaderless replication

Another design allows multiple replicas to accept reads/writes without one permanent leader in the same way.

Conceptually:

```text
             ┌── A
WRITE ───────┼── B
             └── C
```

The system can decide how many replicas must participate.

This leads naturally to the concept of:

> **Quorum**

You will study quorum separately.

---

# 14. Geographic replication

Replication can also be used across regions.

```text
            Global application

       India        Europe       US
         |             |          |
        DB            DB         DB
```

Why?

- lower user latency
- regional fault tolerance
- disaster recovery
- data locality requirements

But geographically distant replicas usually have higher network latency.

This creates another trade-off:

```text
More geographic distance
        ↓
More network delay
        ↓
Harder/faster? to keep replicas tightly synchronized
```

---

# 15. Real-world example: online shopping

Suppose an online store has:

```text
Product:
Laptop X
Stock = 100
```

You may have:

```text
Primary → Stock 100
Replica B → Stock 100
Replica C → Stock 100
```

One customer buys a laptop.

Primary changes:

```text
100 → 99
```

Replicas eventually receive:

```text
99
```

For product browsing, a brief stale value may be acceptable.

But during checkout, you need stronger protection against selling the same item to too many customers.

This is why a system may use different consistency approaches for:

```text
Browsing catalog
        vs.
Inventory reservation
```

---

# 16. Replication is not backup

This distinction is very important.

### Replication

The system keeps copies so it can continue serving data.

```text
A
B
C
```

### Backup

A separate recovery copy is kept so data can be restored after problems such as:

- accidental deletion
- corruption
- ransomware
- operator mistakes

Replication does **not** automatically protect against every kind of data corruption.

If bad data is replicated:

```text
Bad update
   |
   +--> A ❌
   +--> B ❌
   +--> C ❌
```

the replicas may all contain the bad state.

So:

> **Replication improves availability; backup supports recovery from destructive mistakes and historical state loss.**

---

# 17. Replication and consistency

The overall relationship is:

```text
Replication
     |
     v
Multiple copies
     |
     v
Copies can temporarily differ
     |
     v
Replication lag / conflicts
     |
     v
Consistency decisions
```

Therefore replication and consistency cannot be studied independently.

---

# 18. Questions architects ask about replication

When designing a system, ask:

### How many replicas?

Example:

```text
N = 3
```

versus:

```text
N = 5
```

More replicas can improve fault tolerance but add:

- storage
- network traffic
- coordination
- operational complexity

### Where are replicas?

```text
Same region?
Different regions?
Different availability zones?
```

### How quickly must replicas converge?

```text
Milliseconds?
Seconds?
Minutes?
```

### Which replicas can accept writes?

```text
Only primary?
Multiple leaders?
Any replica?
```

### What happens if a replica is unavailable?

Should the system:

```text
wait
```

or:

```text
continue without it
```

That decision connects directly to quorum and availability.

---

# 19. A simple mental model

Think of replication as making photocopies of an important document.

```text
Original
   |
   +---- Copy A
   +---- Copy B
   +---- Copy C
```

Benefits:

- losing one copy does not necessarily lose the document
- multiple people can use copies

Problems:

- copies can become outdated
- someone must distribute updates
- two people may edit different copies
- eventually the copies may need reconciliation

That is replication in one simple analogy.

---

# 20. One-minute explanation

> "Replication means keeping multiple copies of data on different machines so the system can survive failures and scale reads or geography. A common design uses a primary that accepts writes and replicas that follow those writes. Synchronous replication provides fresher replicas but requires more coordination and can increase latency. Asynchronous replication reduces write latency but creates replication lag. Multi-leader and leaderless designs allow more distributed writes but make conflict resolution and consistency more complex."

---

# 21. Key terms

**Replica**  
A copy of data.

**Primary/Leader**  
The node that usually coordinates writes in a leader-based design.

**Follower/Replica**  
A node that receives replicated data.

**Replication lag**  
The delay before a replica catches up with the latest update.

**Synchronous replication**  
Wait for required replica acknowledgements before success.

**Asynchronous replication**  
Acknowledge the write before all replicas have caught up.

**Multi-leader**  
More than one node can accept writes.

**Leaderless**  
No single leader is required to coordinate every operation.

---

# 22. What to learn next

You now know:

```text
Why multiple copies exist
        ↓
How replicas are maintained
        ↓
Why replicas can disagree
        ↓
Why consistency becomes important
```

Next, learn **quorum** to understand how a distributed system decides:

> **"How many replicas need to participate before I accept a read or write?"**
