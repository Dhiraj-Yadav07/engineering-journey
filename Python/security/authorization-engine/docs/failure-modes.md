# Failure-Mode Security Test Report

## 1. Objective

This lab evaluates authorization behavior when the policy source is unavailable and when the authorization layer is operating with a stale policy version.

The objective is to demonstrate:

- the security difference between fail-open and fail-closed authorization;
- how stale policy state can produce an authorization decision that differs from the current policy;
- how stale-policy detection can prevent authorization using obsolete policy state;
- that stale or unavailable policy conditions are handled with a deny-by-default security posture.

---

## 2. Scope

This lab adds isolated failure-mode test infrastructure without modifying the existing RBAC, ABAC, ReBAC, policy-store, policy-manager, or audit-store implementations.

### Lab components

- `src/authorization_engine/failure_modes.py`
- `tests/test_failure_modes.py`
- `src/authorization_engine/stale_policy.py`
- `tests/test_stale_policy.py`

The existing authorization functionality remains covered by the project's regression test suite.

---

## 3. Fail-Open vs Fail-Closed

### 3.1 Policy unavailable

A custom `PolicyUnavailableError` represents an infrastructure failure where the policy source cannot be reached.

This is intentionally different from a normal policy DENY.

- **Policy DENY:** the policy was successfully evaluated and rejected the request.
- **Policy unavailable:** the system cannot safely establish the correct authorization state.

### 3.2 Fail-open behavior

The fail-open implementation returns `True` when the policy source is unavailable.

```text
Policy unavailable
       |
       v
   FAIL OPEN
       |
       v
     ALLOW
```

This behavior is security-sensitive because an infrastructure failure can result in access being granted without a successful policy evaluation.

The test suite verifies:

- an explicit policy ALLOW remains ALLOW;
- an explicit policy DENY remains DENY;
- policy unavailability results in ALLOW under fail-open semantics.

### 3.3 Fail-closed behavior

The fail-closed implementation returns `False` when the policy source is unavailable.

```text
Policy unavailable
       |
       v
  FAIL CLOSED
       |
       v
      DENY
```

This provides a safer default for an authorization control because access is not granted when the system cannot establish the applicable policy.

The test suite verifies:

- an explicit policy ALLOW remains ALLOW;
- an explicit policy DENY remains DENY;
- policy unavailability results in DENY under fail-closed semantics.

---

## 4. Stale Policy Scenario

### 4.1 Scenario

The lab models two versions of a simple authorization policy:

```text
Policy v1:
    alice -> ALLOW
    bob   -> ALLOW

Policy v2:
    alice -> ALLOW
    bob   -> DENY
```

Version 2 represents the current policy after Bob's access has been removed.

### 4.2 Security problem

If an authorization request uses cached policy version 1 after version 2 has become current, Bob can still receive an ALLOW decision.

```text
Current policy: v2
Bob should be:  DENY

Cached policy:  v1
Bob receives:   ALLOW
```

Therefore, stale authorization state can create an authorization bypass relative to the current policy.

### 4.3 Observed behavior

The tests explicitly demonstrate that:

```text
v1 + bob -> True
v2 + bob -> False
```

This confirms that the same authorization request can produce different results depending on the policy version used.

---

## 5. Stale Policy Detection

The lab tracks a policy version using:

```python
@dataclass(frozen=True)
class SimplePolicy:
    version: int
    allowed_users: set[str]
```

A policy is considered stale when:

```text
cached_policy.version < current_version
```

For example:

```text
Cached version:  1
Current version: 2
                 |
                 v
              STALE
```

The test suite verifies both conditions:

- version 1 is detected as stale when version 2 is current;
- version 2 is not considered stale when version 2 is current.

---

## 6. Stale-Policy Protection

Detecting stale state is not sufficient by itself. The authorization layer must also define what happens after staleness is detected.

The lab implements:

```text
             Check policy version
                     |
              +------+------+
              |             |
            STALE        CURRENT
              |             |
              v             v
            DENY       Evaluate policy
                            |
                       +----+----+
                       |         |
                     ALLOW      DENY
```

When the supplied policy is stale, authorization immediately returns `False`.

This means that even if the stale policy would have allowed the user, the stale-policy protection layer prevents that authorization decision from being used.

### Security property

```text
Stale policy
     +
Potentially permissive cached decision
     |
     v
   DENY
```

This establishes a deny-by-default response to stale authorization state.

---

## 7. Test Evidence

### Fail-open / fail-closed tests

Command:

```powershell
pytest tests/test_failure_modes.py
```

Result:

```text
6 passed in 0.05s
```

The six tests cover:

1. fail-open preserves ALLOW;
2. fail-open preserves DENY;
3. fail-open allows when policy is unavailable;
4. fail-closed preserves ALLOW;
5. fail-closed preserves DENY;
6. fail-closed denies when policy is unavailable.

### Stale-policy tests

Command:

```powershell
pytest tests/test_stale_policy.py
```

Result:

```text
9 passed in 0.06s
```

The nine tests cover:

- current policy behavior;
- stale policy behavior;
- different decisions between stale and current policy;
- stale-version detection;
- current-version validation;
- stale-policy protection;
- authorization with a current policy;
- authorization denial with a current policy;
- protection against an otherwise-permissive stale policy.

---

## 8. Full Regression Evidence

After adding the failure-mode lab, the complete project test suite was executed.

Command:

```powershell
pytest
```

Result:

```text
collected 68 items

68 passed in 0.16s
```

The complete test suite covered:

| Area | Tests |
|---|---:|
| RBAC | 9 |
| ABAC | 7 |
| ReBAC | 13 |
| Policy Store | 11 |
| Policy Manager | 8 |
| Audit Store | 5 |
| Fail-open / Fail-closed | 6 |
| Stale Policy | 9 |
| **Total** | **68** |

This confirms that the failure-mode lab was added without causing regressions in the existing authorization-engine functionality.

---

## 9. Security Findings

### Finding 1 — Fail-open authorization is unsafe during policy-source failure

If policy retrieval fails and the authorization system defaults to ALLOW, an infrastructure failure can become an access-control failure.

**Risk:** Unauthorized access may be granted when the policy cannot be evaluated.

**Preferred security posture:** Fail closed.

---

### Finding 2 — Stale policy can result in obsolete authorization decisions

A cached policy can continue granting access after a newer policy version has revoked that access.

**Risk:** Revoked permissions may remain effective until the stale policy is refreshed or invalidated.

**Preferred security posture:** Detect policy-version mismatch and reject authorization using stale state.

---

### Finding 3 — Policy state and authorization decision must be version-aware

Authorization correctness depends not only on evaluating the policy but also on evaluating the correct policy version.

**Security implication:** Policy freshness is part of authorization correctness.

---

## 10. Recommended Controls

A production authorization system should consider the following controls:

1. **Fail closed when policy evaluation cannot be trusted.**
2. **Track policy versions or revisions.**
3. **Detect cached-policy version mismatches.**
4. **Reject authorization requests when required policy state is stale.**
5. **Invalidate or refresh authorization caches after policy changes.**
6. **Record policy version information in authorization/audit events where appropriate.**
7. **Monitor policy-store availability and cache freshness.**
8. **Define explicit operational behavior for policy-store outages rather than relying on implicit defaults.**

The exact implementation should depend on the consistency, availability, and latency requirements of the production authorization architecture.

---

## 11. Architecture Implication

The lab demonstrates that authorization security is not limited to the policy decision itself.

A more complete authorization path is:

```text
                Policy Store
                     |
                     v
              Policy Version
                     |
                     v
               Policy Cache
                     |
              freshness check
                     |
          +----------+----------+
          |                     |
        STALE                 CURRENT
          |                     |
          v                     v
        DENY              Policy evaluation
                                |
                         +------+------+
                         |             |
                         v             v
                       ALLOW          DENY
```

Policy availability and policy freshness therefore become security properties of the authorization system.

---

## 12. Conclusion

This lab demonstrates three important authorization failure modes and controls:

- **Fail-open:** policy unavailability can result in ALLOW and creates a security risk.
- **Fail-closed:** policy unavailability results in DENY and provides a safer security default.
- **Stale policy:** obsolete policy state can produce an incorrect ALLOW decision even after access has been revoked.
- **Stale-policy protection:** detecting stale state and denying the request prevents use of an obsolete authorization policy.

The final regression result is:

```text
68 / 68 tests passed
```

The authorization engine therefore has test evidence covering not only normal RBAC, ABAC, and ReBAC behavior, but also policy versioning, audit behavior, policy unavailability, and stale-policy failure modes.
