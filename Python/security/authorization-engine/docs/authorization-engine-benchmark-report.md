# Local Authorization Engine Benchmark Report

## 1. Benchmark Task

**Focus:** Distributed Systems  
**Task:** Benchmark local authorization engine: p50/p95/p99 latency and throughput  
**Type:** Benchmark  
**Deliverable:** Benchmark report

### Objective

Measure the performance of the local authorization engine under an in-process workload and report:

- p50 latency
- p95 latency
- p99 latency
- throughput (requests/sec)

The benchmark is intended to establish a reproducible baseline before adding distributed-system features such as remote policy stores, policy distribution, and authorization-decision caching.

---

## 2. Current Engine Under Test

The current project exposes an `AuthorizationEngine` responsible for:

- registering roles
- assigning roles to subjects
- evaluating authorization requests
- returning ALLOW / DENY decisions

The documented usage is:

```python
engine = AuthorizationEngine()

engine.add_role(developer)
engine.assign_role("alice", "developer")

engine.authorize("alice", "reports", "read")
```

The current implementation is a learning/portfolio authorization engine rather than production-scale authorization infrastructure.

The project documentation also indicates that the in-memory relationship store is suitable for demonstrating the authorization model, not for production-scale infrastructure.

---

## 3. What We Are Measuring

### Latency

For each authorization request:

```text
start timer
    |
    v
engine.authorize(...)
    |
    v
stop timer
```

Latency is:

```text
elapsed time per authorization decision
```

Report:

```text
p50 = median latency
p95 = 95th-percentile latency
p99 = 99th-percentile latency
```

### Throughput

Throughput is:

```text
completed authorization decisions
---------------------------------
elapsed benchmark time
```

Report as:

```text
requests/sec
```

### Why p50/p95/p99?

Average latency alone can hide tail latency.

Example:

```text
p50 = "normal request"
p95 = "slow tail"
p99 = "very slow tail"
```

For an authorization service, tail latency matters because a slow authorization decision can add latency to every protected application request.

---

## 4. Benchmark Scope

This benchmark should first measure the **local in-process engine**, not:

```text
HTTP
Docker
Redis
Database
Network
```

The first baseline is:

```text
Benchmark process
      |
      v
AuthorizationEngine
      |
      v
In-memory policy / role state
```

This isolates policy-evaluation cost.

A separate benchmark can later measure the HTTP API and full distributed architecture.

---

## 5. Benchmark Scenarios

Run at least these scenarios.

### Scenario A — ALLOW

A request that matches an assigned permission.

```text
alice
  |
  v
developer
  |
  +---- reports:read
```

Request:

```text
alice -> reports:read
```

Expected:

```text
ALLOW
```

### Scenario B — DENY

A request for a permission the assigned role does not have.

```text
alice
  |
  v
developer
  |
  +---- reports:read
  +---- reports:write

Request:
alice -> reports:delete
```

Expected:

```text
DENY
```

The documented engine follows a default-deny model and does not infer ungranted permissions.

### Scenario C — Multiple roles

Assign multiple roles and benchmark a request that requires checking multiple role assignments.

```text
Alice
 /   \
v     v
Developer Auditor
```

This shows how evaluation cost changes as role-assignment complexity grows.

### Scenario D — ReBAC / advanced evaluation

If the current benchmark target includes the ReBAC engine, benchmark it separately from the basic RBAC path rather than mixing results.

This is important because relationship evaluation may have materially different computational cost from direct role lookup.

---

## 6. Benchmark Protocol

### Warm-up

Do not measure the first few calls as representative production latency.

Run a warm-up phase:

```text
Warm-up = 10,000 requests
```

Then discard those timings.

### Measurement

Example:

```text
Measured requests = 100,000
```

Store each individual latency sample in nanoseconds or microseconds.

### Repetitions

Run the benchmark at least 3 times.

Example:

```text
Run 1
Run 2
Run 3
```

Report the result for each run and the final representative result.

### Environment

Record:

```text
OS
Python version
CPU
logical CPU count
memory
git commit
engine version
benchmark parameters
```

Do not compare results across machines without recording these details.

---

## 7. Recommended Benchmark Parameters

Initial baseline:

```text
Warm-up:       10,000 requests
Measurement:  100,000 requests
Runs:                  3
Concurrency:           1
```

Start with concurrency = 1 because this isolates the raw local evaluation cost.

Then run a second benchmark with multiple worker threads/processes if you want to study scaling.

---

## 8. Suggested Benchmark Harness

Create:

```text
benchmarks/
└── benchmark_authorization.py
```

Example implementation:

```python
from __future__ import annotations

import statistics
import time
from dataclasses import dataclass

from authorization_engine.engine import AuthorizationEngine
from authorization_engine.models import Permission, Role


@dataclass
class BenchmarkResult:
    scenario: str
    requests: int
    elapsed_seconds: float
    throughput_rps: float
    p50_us: float
    p95_us: float
    p99_us: float


def percentile(values: list[float], p: float) -> float:
    values = sorted(values)
    if not values:
        raise ValueError("No latency samples")

    index = (len(values) - 1) * p
    lower = int(index)
    upper = min(lower + 1, len(values) - 1)
    fraction = index - lower

    return values[lower] + (values[upper] - values[lower]) * fraction


def build_engine() -> AuthorizationEngine:
    engine = AuthorizationEngine()

    role = Role(
        "developer",
        {
            Permission("reports", "read"),
            Permission("reports", "write"),
        },
    )

    engine.add_role(role)
    engine.assign_role("alice", "developer")

    return engine


def run_scenario(
    engine: AuthorizationEngine,
    scenario: str,
    subject: str,
    resource: str,
    action: str,
    warmup: int,
    requests: int,
) -> BenchmarkResult:

    for _ in range(warmup):
        engine.authorize(subject, resource, action)

    latencies_us: list[float] = []

    wall_start = time.perf_counter()

    for _ in range(requests):
        start = time.perf_counter_ns()
        engine.authorize(subject, resource, action)
        end = time.perf_counter_ns()

        latencies_us.append((end - start) / 1_000.0)

    elapsed = time.perf_counter() - wall_start

    return BenchmarkResult(
        scenario=scenario,
        requests=requests,
        elapsed_seconds=elapsed,
        throughput_rps=requests / elapsed,
        p50_us=percentile(latencies_us, 0.50),
        p95_us=percentile(latencies_us, 0.95),
        p99_us=percentile(latencies_us, 0.99),
    )


def main() -> None:
    engine = build_engine()

    scenarios = [
        ("ALLOW", "alice", "reports", "read"),
        ("DENY", "alice", "reports", "delete"),
    ]

    warmup = 10_000
    requests = 100_000

    results: list[BenchmarkResult] = []

    for scenario, subject, resource, action in scenarios:
        results.append(
            run_scenario(
                engine,
                scenario,
                subject,
                resource,
                action,
                warmup,
                requests,
            )
        )

    print(
        f"{'Scenario':<10} "
        f"{'Throughput (req/s)':>20} "
        f"{'p50 (us)':>12} "
        f"{'p95 (us)':>12} "
        f"{'p99 (us)':>12}"
    )

    for result in results:
        print(
            f"{result.scenario:<10} "
            f"{result.throughput_rps:>20.2f} "
            f"{result.p50_us:>12.2f} "
            f"{result.p95_us:>12.2f} "
            f"{result.p99_us:>12.2f}"
        )


if __name__ == "__main__":
    main()
```

> Adapt the imports or setup only if your current engine API has changed from the documented interface.

---

## 9. Running the Benchmark

From the authorization-engine project root:

```powershell
python benchmarks\benchmark_authorization.py
```

If your project is installed as a package:

```powershell
python -m benchmarks.benchmark_authorization
```

Use the exact command that matches your repository layout.

---

## 10. Expected Output Format

Do not invent results.

Capture the actual output in this table:

| Scenario | Throughput (req/s) | p50 (µs) | p95 (µs) | p99 (µs) |
|---|---:|---:|---:|---:|
| ALLOW | TBD | TBD | TBD | TBD |
| DENY | TBD | TBD | TBD | TBD |
| Multiple Roles | TBD | TBD | TBD | TBD |
| ReBAC | TBD | TBD | TBD | TBD |

### Run metadata

```text
Date:
Git commit:
OS:
Python:
CPU:
Memory:
Warm-up:
Measured requests:
Runs:
Concurrency:
```

---

## 11. Result Interpretation

### Example interpretation pattern

Do not write:

> "The engine is production ready because p99 is low."

Instead write:

> "The benchmark measures the cost of local in-process authorization evaluation under the selected workload. It does not include network, serialization, policy-store access, cache misses, or distributed coordination."

This keeps the claim precise.

### What to look for

#### p50 close to p95/p99

```text
p50 ≈ p95 ≈ p99
```

This usually indicates relatively stable latency under the test conditions.

#### Large p99 tail

```text
p50 = low
p99 = much higher
```

Investigate:

- garbage collection
- scheduler effects
- logging
- allocation
- lock contention
- CPU contention
- benchmark noise

---

## 12. Throughput vs latency

Do not optimize only one number.

A design can have:

```text
very high throughput
+
unacceptable p99 latency
```

or:

```text
excellent latency
+
poor throughput
```

The useful benchmark reports both.

---

## 13. Benchmark Limitations

This benchmark is a **local engine baseline**, not a production-scale authorization benchmark.

It does not prove:

- multi-region performance
- HTTP/API latency
- distributed cache performance
- policy-store performance
- event-distribution performance
- behavior under network failures
- multi-process scalability
- 100K+ requests/sec production capacity

The existing project documentation describes the engine as a learning/portfolio implementation and identifies limitations such as in-memory state and lack of persistent policy management.

Therefore:

> **Use this benchmark to establish a local computational baseline, not as evidence that the complete authorization platform can sustain a specific production traffic target.**

---

## 14. Next-Level Benchmark

After the local baseline, expand the benchmark into:

```text
Level 1
In-process engine
        |
        v
policy evaluation cost


Level 2
HTTP API
        |
        v
serialization + network + server overhead


Level 3
Decision cache
        |
        +--> cache hit
        |
        +--> cache miss


Level 4
Regional policy store
        |
        v
policy lookup cost


Level 5
Distributed architecture
        |
        v
multi-region + policy distribution +
cache + authorization evaluation
```

This progression makes performance evidence much more useful.

---

## 15. Benchmark Matrix for the Authorization Platform

| Test | What it measures |
|---|---|
| Local ALLOW | Fast-path policy evaluation |
| Local DENY | Negative authorization path |
| Multiple roles | Increasing evaluation complexity |
| ReBAC | Relationship-based evaluation |
| HTTP ALLOW | API overhead |
| HTTP DENY | API negative path |
| Cache HIT | Decision-cache performance |
| Cache MISS | Full authorization path |
| Policy-store lookup | Local policy retrieval |
| Cold start | Startup/warm-up effect |
| Concurrent load | Horizontal/concurrency scaling |
| Sustained load | Stability over time |

---

## 16. How This Connects to the Distributed-Systems Architecture

The benchmark establishes the cost of:

```text
Application
    |
    v
Local Authorization Engine
    |
    v
ALLOW / DENY
```

The multi-region architecture adds:

```text
Policy Distribution
        |
        v
Regional Policy Store
        |
        v
Authorization Engine
        |
        v
Decision Cache
```

The benchmark should therefore answer:

> **How much authorization capacity do we get from one local engine before distributed infrastructure is introduced?**

That becomes the baseline against which later improvements are compared.

---

## 17. Performance Questions for the Architecture Review

Be prepared to answer:

1. What is your p50 authorization latency?
2. What is your p95?
3. What is your p99?
4. What throughput did you achieve?
5. Was the benchmark in-process or over HTTP?
6. Was the policy already in memory?
7. Did the test include cache hits?
8. What happened at higher concurrency?
9. What is the bottleneck?
10. How would policy-store access change the result?
11. How would a decision cache change the result?
12. How would you validate the 100K+ requests/sec architecture target?

---

## 18. Evidence Checklist

Before marking this task complete, capture:

```text
[ ] Benchmark script committed
[ ] Exact benchmark command
[ ] Git commit SHA
[ ] Hardware / runtime information
[ ] Warm-up configuration
[ ] Measurement configuration
[ ] ALLOW results
[ ] DENY results
[ ] p50
[ ] p95
[ ] p99
[ ] Throughput
[ ] At least 3 benchmark runs
[ ] Result table
[ ] Interpretation
[ ] Limitations
```

---

## 19. Current Evidence Status

At the time this report was prepared, the available project documentation establishes the authorization engine's interface and current architecture, but it does **not** provide measured p50/p95/p99 latency or throughput results.

Therefore the numeric benchmark fields in this report are intentionally:

```text
TBD
```

They must be populated from an actual benchmark execution.

Do **not** replace these values with estimates.

---

## 20. Recommended Repository Location

Because this is benchmark evidence rather than a distributed-systems concept note, keep it with the authorization-engine project:

```text
authorization-engine/
├── benchmarks/
│   └── benchmark_authorization.py
├── docs/
│   └── benchmark-report.md
└── ...
```

For the broader Distributed-Systems portfolio, reference the benchmark from the relevant project or gate documentation.

---

## 21. Final Conclusion

The benchmark should establish a reproducible baseline for the local authorization engine by measuring:

```text
Latency
 ├── p50
 ├── p95
 └── p99

Throughput
 └── requests/sec
```

The correct engineering approach is:

```text
Measure first
    |
    v
Record environment + workload
    |
    v
Capture p50/p95/p99 + throughput
    |
    v
Understand bottleneck
    |
    v
Add cache / distributed policy store
    |
    v
Benchmark again
    |
    v
Compare against baseline
```

The benchmark becomes meaningful when every later architecture change can be compared against this baseline.
