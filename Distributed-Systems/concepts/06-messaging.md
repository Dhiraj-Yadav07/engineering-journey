# Messaging Design Notes — Queues, Pub/Sub, Retries, Idempotency & Backpressure

> **Distributed Systems — Study Notes**
>
> **Beginner goal:** Understand how distributed services communicate asynchronously, what happens when consumers fail or become slow, and how to prevent duplicate work and overload.

---

## 1. Why do we need messaging?

Start with a synchronous system:

```text
User
  |
  v
Service A
  |
  v
Service B
  |
  v
Database
```

Service A waits for Service B. If B is slow or unavailable, A can also become slow or fail.

Messaging inserts a buffer:

```text
Service A
    |
    v
+-----------+
|   Queue   |
+-----------+
    |
    v
Service B
```

Now A can hand off work and continue while B processes the message later.

### Why this helps

- Decouples services.
- Buffers temporary traffic spikes.
- Lets producers and consumers scale independently.
- Allows asynchronous/background processing.

### Important limitation

A queue **buys time; it does not create infinite capacity**.

If producers permanently generate work faster than consumers can process it, the queue keeps growing.

---

# 2. Queue: the basic idea

Think about a restaurant:

```text
Customers → Waiting Line → Kitchen
```

The line is a queue. Orders can arrive faster than the kitchen can process them, so the queue temporarily stores pending work.

In software:

```text
Producer → Queue → Consumer
```

### Producer

Creates messages or work.

### Queue

Stores messages until a consumer can process them.

### Consumer

Reads and processes messages.

---

# 3. Why a queue helps

Suppose:

```text
Producer = 10,000 messages/sec
Consumer = 2,000 messages/sec
```

Without a queue, the consumer is directly exposed to the spike:

```text
Producer ─────────> Consumer
                     |
                     X
                 overloaded
```

With a queue:

```text
Producer
   |
   v
Queue
|||||||||||||||||||||
   |
   v
Consumer
2,000/sec
```

The queue absorbs a temporary burst.

But if the difference continues for a long time, backlog grows:

```text
Incoming rate > Processing rate
              |
              v
        Queue depth grows
              |
              v
      Message age increases
              |
              v
        System under stress
```

---

# 4. Queue vs synchronous API

### Synchronous

```text
A ───── request ─────> B
A <──── response ───── B
```

A waits for B.

### Asynchronous messaging

```text
A ───── message ─────> Queue

A continues

Queue ───── message ─────> B
```

The key benefit is **decoupling**.

---

# 5. Work queue

A work queue distributes jobs among workers.

```text
                +-----------+
                |   Queue   |
                +-----+-----+
                      |
             +--------+--------+
             |        |        |
             v        v        v
          Worker 1  Worker 2  Worker 3
```

A job is normally processed by one worker in a consumer group.

Examples:

- image processing
- report generation
- email sending
- background provisioning
- batch jobs

---

# 6. Pub/Sub: one event, many consumers

Pub/Sub is useful when several independent systems need to know that something happened.

```text
                 UserCreated
                      |
                      v
                   Topic
                 /   |   \
                v    v    v
             Email  Audit Analytics
```

Example:

```text
UserCreated
    |
    +----> Welcome Email Service
    |
    +----> Audit Service
    |
    +----> Analytics
    |
    +----> CRM
```

### Queue vs Pub/Sub

| Queue / Work Queue | Pub/Sub |
|---|---|
| Distributes work | Broadcasts events |
| Workers usually compete for jobs | Multiple subscribers can receive the same event |
| Good for background tasks | Good for event-driven systems |
| Example: resize image | Example: `UserCreated` |

Mental model:

```text
QUEUE
A → [Job] → Worker

PUB/SUB
A → [Event]
         ├──> B
         ├──> C
         └──> D
```

---

# 7. Command vs event

### Command

> "Please do this."

Example:

```text
CreateInvoice
```

### Event

> "This already happened."

Example:

```text
InvoiceCreated
```

A command usually has one intended handler. An event can have many subscribers.

---

# 8. Message delivery semantics

The system needs to answer:

> **How many times can a message be delivered?**

## At-most-once

```text
0 or 1 delivery
```

A message can be lost, but duplicate delivery is avoided.

## At-least-once

```text
1 or more deliveries
```

Messages are retried so they are less likely to be lost, but duplicates can happen.

## Exactly-once

This is much harder than "the broker delivered it once." The business operation itself must not be accidentally repeated.

A practical pattern is:

```text
At-least-once delivery
        +
Idempotent processing
        =
Safe duplicate handling
```

---

# 9. Why duplicates happen

Consider:

```text
1. Consumer receives message
2. Consumer updates database
3. Database update succeeds
4. Consumer crashes
5. ACK never reaches broker
```

The broker cannot know that the business operation already succeeded, so it may redeliver:

```text
Message 123
    |
    v
Consumer
    |
   crash
    |
    v
Message 123 again
```

This is normal distributed-system behavior.

---

# 10. Idempotency

> **Idempotency means processing the same operation multiple times produces the same final business result as processing it once.**

### Idempotent example

```text
Set order status = SHIPPED
```

Doing it twice still gives:

```text
SHIPPED
```

### Non-idempotent example

```text
Increase balance by ₹100
```

Starting at ₹1,000:

```text
Once  → ₹1,100
Twice → ₹1,200
```

If the duplicate was accidental, money was created incorrectly.

---

# 11. Idempotency key

A common pattern is a unique operation/message ID:

```text
message_id = abc-123
```

The consumer tracks processed IDs:

```text
Processed:
abc-123
xyz-456
pqr-789
```

On receipt:

```text
             Message abc-123
                    |
                    v
            Already processed?
                 /       \
               YES        NO
                |          |
                v          v
              Ignore     Process
                            |
                            v
                     Record message ID
```

Where possible, make the business update and idempotency record part of the same database transaction:

```text
DB transaction
   |
   +--> business update
   |
   +--> processed_message_id
```

---

# 12. Retries

Distributed systems experience temporary failures:

```text
Database timeout
Network timeout
HTTP 503
Throttling
Temporary dependency outage
```

A consumer may retry:

```text
Attempt 1 ❌
    |
Attempt 2 ❌
    |
Attempt 3 ✅
```

But retries must be controlled.

---

# 13. Exponential backoff

Avoid:

```text
retry
retry
retry
retry
```

Use increasing delays:

```text
Attempt 1
wait 1 sec
Attempt 2
wait 2 sec
Attempt 3
wait 4 sec
Attempt 4
```

Conceptually:

```text
delay = base × 2^attempt
```

Usually cap the delay at a maximum.

---

# 14. Jitter

Suppose thousands of consumers fail simultaneously.

If every consumer retries at exactly the same instant:

```text
10,000 retries
      |
      v
same moment
      |
      v
dependency overloaded again
```

Add randomness:

```text
retry delay = exponential backoff + random jitter
```

This spreads load over time.

Common pattern:

```text
Retry + exponential backoff + jitter
```

---

# 15. Retry only appropriate failures

Often retryable:

```text
timeout
temporary network failure
503 Service Unavailable
throttling
```

Often not retryable:

```text
invalid request
malformed message
schema validation failure
permission denied
```

Otherwise permanent failures can become infinite retry loops.

---

# 16. Dead Letter Queue (DLQ)

After repeated failure, move the message out of the normal retry path:

```text
Message
  |
  v
Retry 1
  |
  v
Retry 2
  |
  v
Retry 3
  |
  v
DLQ
```

A Dead Letter Queue is used to isolate messages that need inspection or special handling.

Possible next actions:

- inspect the message
- fix the underlying problem
- correct the message if appropriate
- replay it safely

---

# 17. Poison messages

A poison message is a message that repeatedly causes processing to fail.

```text
Message 123
    |
    v
Consumer ❌
    |
    v
Retry ❌
    |
    v
Retry ❌
    |
    v
DLQ
```

A retry limit prevents one bad message from consuming resources forever.

---

# 18. Retry storm

If a downstream dependency is already unhealthy:

```text
Consumer 1 ─┐
Consumer 2 ─┤
Consumer 3 ─┤──> Database ❌
Consumer 4 ─┤
Consumer 5 ─┘
       ↑
    retries
```

Aggressive retries can make the outage worse.

Mitigations:

- exponential backoff
- jitter
- maximum retries
- rate limiting
- circuit breakers
- consumer throttling

---

# 19. Backpressure

Suppose:

```text
Producer = 10,000 messages/sec
Consumer = 2,000 messages/sec
```

Then approximately:

```text
Backlog growth = 8,000 messages/sec
```

Backpressure means the system has a mechanism to slow or constrain upstream work when downstream capacity is insufficient.

```text
Producer
   |
   v
Rate limit / flow control
   |
   v
Queue
   |
   v
Consumers
```

---

# 20. Why backpressure matters

Without backpressure:

```text
Producer
   |
10,000/s
   |
   v
 Queue
   |
   v
2,000/s
Consumer

Queue keeps growing
      |
      v
Storage/memory pressure
      |
      v
Latency increases
      |
      v
System may fail
```

The goal is graceful overload rather than total collapse.

---

# 21. Ways to apply backpressure

### Rate limiting

Slow the producer:

```text
Producer → Rate Limiter → Queue
```

### Consumer scaling

Add workers when the real bottleneck permits it:

```text
Queue
 |
 +--> Worker 1
 +--> Worker 2
 +--> Worker 3
 +--> Worker 4
```

### Bounded queues

Define a maximum backlog.

When full, the system may:

```text
throttle
reject
shed load
defer lower-priority work
```

### Load shedding

Protect critical work by dropping or postponing non-critical work.

Example:

```text
Analytics event    → lower priority
Payment transaction → critical
```

---

# 22. Do not blindly add consumers

Suppose:

```text
Queue
 |
 +--> Worker 1
 +--> Worker 2
 +--> Worker 3
 +--> Worker 4
```

But every worker uses the same database:

```text
Workers
  | | | |
  v v v v
Database
   |
   X
 overloaded
```

Adding more workers can make the problem worse.

Always ask:

> **What is the actual bottleneck?**

---

# 23. Queue depth, lag and message age

Useful operational signals:

### Queue depth

How much work is waiting?

```text
100,000 messages
```

### Consumer lag

How far behind the consumer is from available work.

### Oldest message age

How long the oldest unprocessed message has been waiting.

Example:

```text
Oldest message = 2 seconds old → healthy
Oldest message = 45 minutes old → serious backlog
```

Track all three where useful.

---

# 24. Ordering

Sometimes message order matters.

Example:

```text
1. Create user
2. Grant admin role
3. Disable user
```

If processed as:

```text
3 → 1 → 2
```

the result can be incorrect.

Ask:

> **Does this workflow require ordering?**

If yes, related messages can be routed using a consistent key such as:

```text
user_id
account_id
order_id
```

---

# 25. Ordering vs parallelism

Strict ordering reduces parallelism:

```text
Message 1
   ↓
Message 2
   ↓
Message 3
   ↓
Message 4
```

Independent messages can run in parallel:

```text
Message 1 ──> Worker A
Message 2 ──> Worker B
Message 3 ──> Worker C
Message 4 ──> Worker D
```

Therefore:

> **Only enforce ordering where the business logic actually requires it.**

---

# 26. Partitions

Large messaging systems often divide a topic into partitions:

```text
Topic
 |
 +-- Partition 0
 +-- Partition 1
 +-- Partition 2
 +-- Partition 3
```

This allows parallel consumption.

Example:

```text
user_id = 123 → Partition 2
user_id = 456 → Partition 0
user_id = 789 → Partition 1
```

A consistent partition key can preserve ordering for one entity while allowing different entities to process in parallel.

---

# 27. Real example: order processing

```text
                    Order API
                       |
                       v
                  OrderCreated
                       |
                       v
                   Event Bus
                       |
          +------------+------------+
          |            |            |
          v            v            v
       Payment      Inventory     Email
       Service       Service      Service
```

### Payment service temporarily unavailable

```text
Payment → 503
   |
   v
Retry + backoff + jitter
```

### Consumer crashes after charging but before ACK

The message may be redelivered.

Therefore use an idempotency key such as:

```text
payment_operation_id
```

so the same payment is not charged twice.

### Payment service remains down

After the retry limit:

```text
DLQ
```

### Traffic spike

If orders arrive faster than payment processing capacity:

```text
Queue grows
     |
     v
Backpressure / scaling / prioritization
```

---

# 28. Real example: policy distribution

This connects directly to the multi-region policy architecture.

```text
Global Policy Store
       |
       v
PolicyChanged v104
       |
       v
Policy Event Bus
       |
   +---+---+
   |   |   |
   v   v   v
  IN  EU  US
```

If Europe is temporarily unavailable:

```text
Europe consumer ❌
```

The messaging layer should retain/retry the event according to its delivery and retention configuration.

After recovery:

```text
Europe
  |
  v
consume missing events
  |
  v
v104
  |
  v
validate
  |
  v
activate
```

If v104 arrives twice:

```text
Current version = v104
Incoming version = v104
        |
        v
ignore safely
```

If regional consumers fall behind, monitor:

```text
consumer lag
policy propagation latency
oldest policy event age
```

This connects messaging reliability directly to your policy-distribution SLO.

---

# 29. Messaging failure matrix

| Problem | Typical response |
|---|---|
| Consumer crashes | Redelivery / retry |
| Temporary dependency failure | Retry with backoff |
| Permanent invalid message | DLQ |
| Duplicate delivery | Idempotent consumer |
| Consumer too slow | Scale / throttle / backpressure |
| Traffic spike | Queue buffers temporary burst |
| Retry storm | Backoff + jitter + rate controls |
| Ordering required | Key/partition related events |
| Consumer lag grows | Investigate capacity and bottleneck |
| Poison message | Bounded retries → DLQ |

---

# 30. The core mental model

```text
                         MESSAGING
                             |
              +--------------+--------------+
              |              |              |
            Queue         Pub/Sub        Events
              |              |              |
          Buffer work    Broadcast      "Something happened"
              |              |              |
              +--------------+--------------+
                             |
                        Failure happens
                             |
          +------------------+------------------+
          |                  |                  |
        Retry            Idempotency       Backpressure
          |                  |                  |
     Temporary          Handle duplicate      Control
      failures             safely             overload
          |                  |                  |
          +------------------+------------------+
                             |
                            DLQ
                             |
                        inspect / replay
```

---

# 31. Study checklist

Be able to explain, without notes:

1. Why use a queue instead of a synchronous API call?
2. What is the difference between a queue and Pub/Sub?
3. What is an event vs a command?
4. What are at-most-once and at-least-once delivery?
5. Why do duplicate messages happen?
6. What is idempotency?
7. How would you make a payment operation idempotent?
8. Why use exponential backoff?
9. Why add jitter?
10. Which failures should be retried?
11. What is a DLQ?
12. What is a poison message?
13. What is backpressure?
14. What happens when producers are faster than consumers?
15. Why shouldn't you blindly add consumers?
16. When does ordering matter?
17. What is a partition key?
18. How does messaging apply to multi-region policy distribution?

---

# 32. Cheat sheet

```text
QUEUE
= buffer work between producer and consumer

PUB/SUB
= one event → multiple independent subscribers

RETRY
= try temporary failures again

EXPONENTIAL BACKOFF
= increase retry delay after failures

JITTER
= randomize retry timing to avoid synchronized retries

IDEMPOTENCY
= repeated processing produces the same final business result

DLQ
= isolate messages that repeatedly fail

BACKPRESSURE
= constrain upstream work when downstream capacity is insufficient

CONSUMER LAG
= how far a consumer is behind available work

POISON MESSAGE
= message that repeatedly fails processing

PARTITION KEY
= key used to route related messages to a partition, often preserving order
```

---

# 33. Connection to the rest of Distributed Systems

These concepts form a larger architecture chain:

```text
CAP
 |
 +-- What happens during network partition?
 |
Consistency
 |
 +-- What data can users observe?
 |
Replication
 |
 +-- Where are copies of data/policy?
 |
Quorum
 |
 +-- How many replicas participate?
 |
Caching
 |
 +-- How do we avoid repeated expensive work?
 |
Messaging
 |
 +-- How do we distribute changes reliably?
 +-- How do we handle duplicate delivery?
 +-- How do we retry failures?
 +-- How do we control overload?
```

For the **multi-region policy store** project:

```text
Global Policy Store
       |
       v
Policy Change
       |
       v
Event Bus
       |
 +-----+-----+
 |     |     |
 v     v     v
 IN    EU    US
 |     |     |
Policy Distributors
 |     |     |
Regional Policy Stores
```

Reliability controls:

```text
Event delivery
     ↓
Retry
     ↓
Idempotent consumer
     ↓
Policy version check
     ↓
DLQ for persistent failures
     ↓
Backpressure when distributors lag
     ↓
Monitor consumer lag / propagation SLO
```

---

# 34. One-minute explanation

> "Queues provide asynchronous buffering between producers and consumers, while Pub/Sub allows one event to be consumed independently by multiple subscribers. At-least-once delivery is common because failures can happen between business processing and acknowledgement, so duplicates are possible and consumers should be idempotent. Temporary failures are handled with bounded retries, exponential backoff and jitter, while persistently failing messages go to a dead-letter queue. Backpressure prevents an overloaded consumer or dependency from being overwhelmed when producers generate work faster than the system can process it."

---

# 35. Recommended learning order

```text
1. Queue
      ↓
2. Producer / Consumer
      ↓
3. Pub/Sub
      ↓
4. Delivery semantics
      ↓
5. Retry
      ↓
6. Exponential backoff + jitter
      ↓
7. Idempotency
      ↓
8. DLQ
      ↓
9. Backpressure
      ↓
10. Ordering / partitioning
```

Do not start with Kafka internals. First understand **the problem each messaging primitive solves**.

---

# 36. Suggested repo location

Because this is a study concept rather than an architecture deliverable:

```text
Distributed-Systems/
└── concepts/
    ├── 01-cap.md
    ├── 02-consistency-models.md
    ├── 03-replication.md
    ├── 04-quorum.md
    ├── 04-caching.md
    └── 05-messaging.md
```

The project-specific application of these concepts belongs under:

```text
Distributed-Systems/projects/multi-region-policy-store/
```

where the HLD and failure analysis live.

---

# 37. Final takeaway

The five ideas to remember are:

```text
QUEUE
"Hold this work until a consumer can process it."

PUB/SUB
"Tell multiple interested systems that this happened."

RETRY
"This failure may be temporary; try again safely."

IDEMPOTENCY
"If I receive it twice, don't accidentally do the business action twice."

BACKPRESSURE
"The downstream system is overloaded; slow things down."
```

And the safety valve:

```text
DLQ
"This message keeps failing; isolate it."
```

---

## Resource direction

For your next study session, use a beginner-friendly distributed-systems course/video for the conceptual primitives first, then study Kafka/RabbitMQ/Pub/Sub documentation only after the above mental model is clear. The objective is to understand **queues, delivery guarantees, failure handling and overload control**, not to memorize one vendor's API.
