import statistics
import time

from authorization_engine.engine import AuthorizationEngine
from authorization_engine.models import Permission, Role


WARMUP_REQUESTS = 10_000
MEASURED_REQUESTS = 100_000


def percentile(values: list[float], p: float) -> float:
    """Return percentile using linear interpolation."""
    if not values:
        raise ValueError("Cannot calculate percentile of empty data")

    values = sorted(values)

    position = (len(values) - 1) * p
    lower = int(position)
    upper = min(lower + 1, len(values) - 1)

    weight = position - lower

    return values[lower] + (values[upper] - values[lower]) * weight


def build_engine() -> AuthorizationEngine:
    engine = AuthorizationEngine()

    developer = Role(
        name="developer",
        permissions={
            Permission("reports", "read"),
            Permission("reports", "write"),
        },
    )

    engine.add_role(developer)
    engine.assign_role("alice", "developer")

    return engine


def run_benchmark(
    engine: AuthorizationEngine,
    subject: str,
    resource: str,
    action: str,
) -> tuple[float, float, float, float, int]:
    # Warm-up phase.
    for _ in range(WARMUP_REQUESTS):
        engine.authorize(subject, resource, action)

    latencies_us: list[float] = []

    # Start total wall-clock measurement.
    total_start = time.perf_counter()

    for _ in range(MEASURED_REQUESTS):
        start = time.perf_counter_ns()

        engine.authorize(subject, resource, action)

        end = time.perf_counter_ns()

        latency_us = (end - start) / 1_000.0
        latencies_us.append(latency_us)

    total_elapsed = time.perf_counter() - total_start

    p50 = percentile(latencies_us, 0.50)
    p95 = percentile(latencies_us, 0.95)
    p99 = percentile(latencies_us, 0.99)

    average = statistics.mean(latencies_us)

    throughput = MEASURED_REQUESTS / total_elapsed

    return p50, p95, p99, average, int(throughput)


def main() -> None:
    engine = build_engine()

    print("=" * 60)
    print("LOCAL AUTHORIZATION ENGINE BENCHMARK")
    print("=" * 60)

    print(f"Warmup requests:   {WARMUP_REQUESTS:,}")
    print(f"Measured requests: {MEASURED_REQUESTS:,}")
    print("Concurrency:        1")
    print()

    scenarios = [
        ("ALLOW", "alice", "reports", "read"),
        ("DENY", "alice", "reports", "delete"),
    ]

    for name, subject, resource, action in scenarios:
        p50, p95, p99, average, throughput = run_benchmark(
            engine,
            subject,
            resource,
            action,
        )

        print(f"Scenario: {name}")
        print(f"  p50 latency:  {p50:.2f} µs")
        print(f"  p95 latency:  {p95:.2f} µs")
        print(f"  p99 latency:  {p99:.2f} µs")
        print(f"  avg latency:  {average:.2f} µs")
        print(f"  throughput:    {throughput:,} requests/sec")
        print()


if __name__ == "__main__":
    main()