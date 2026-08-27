# IAM Access Analyzer — Threat Model

**Project:** IAM Access Analyzer  
**Version:** v0.3.0  
**Document type:** Security Threat Model  
**Status:** Final  
**Scope:** Local FastAPI service, IAM analysis engine, audit logging, privileged-access detection, risk scoring, and Docker containerization

---

## 1. Purpose

This document threat-models the IAM Access Analyzer and identifies the principal security threats associated with its architecture and intended use.

The analyzer evaluates an access request against configured authorization policies and produces an `AccessDecision`.

The decision includes:

- authorization effect (`allow` / `deny`)
- explanation/reason
- risk score
- privileged-action classification

The project also records audit events and can be deployed as a Docker container.

The purpose of this threat model is to demonstrate that the system has been considered from an attacker and defensive-architecture perspective rather than only from an implementation perspective.

---

# 2. Security Objectives

The analyzer should preserve the following security properties.

## 2.1 Authorization correctness

The analyzer must not incorrectly grant access when no applicable authorization policy exists.

Expected baseline:

```text
No matching policy
        |
        v
      DENY
```

---

## 2.2 Explicit deny precedence

An applicable explicit deny must take precedence over an applicable allow.

Expected behavior:

```text
Matching policies
       |
       +--> Explicit DENY exists --> DENY
       |
       +--> No explicit DENY ------> ALLOW if applicable allow exists
```

This protects against accidental privilege grants caused by an allow policy.

---

## 2.3 Contextual authorization

Policy conditions must be evaluated against the request context.

A request should not satisfy a conditional policy when the required condition is absent or does not match.

---

## 2.4 Policy expiration

Expired policies must not grant access.

The analyzer evaluates policy expiration before considering the policy applicable.

---

## 2.5 Privileged-access visibility

A request can be authorized while still being security-sensitive.

Therefore:

```text
Authorization result != Privilege classification
```

For example:

```text
iam.roles.update
        |
        +--> authorization: ALLOW
        |
        +--> privileged: TRUE
        |
        +--> elevated risk score
```

The privileged flag is intended to provide a security signal for review, monitoring, and future policy enforcement.

---

## 2.6 Risk visibility

The analyzer calculates a risk score independently from the final authorization effect.

This allows an authorized request to still be identified as high-risk.

---

## 2.7 Auditability

Important access-analysis decisions should be recordable as audit events containing:

- timestamp
- principal
- resource
- action
- effect
- reason

---

## 2.8 Container isolation and reproducibility

The application should run with its dependencies inside a reproducible container image rather than depending on the host Python environment.

The v0.3 Docker image packages:

```text
Python runtime
      +
IAM Access Analyzer package
      +
FastAPI
      +
Uvicorn
```

---

# 3. System Overview

The current architecture is:

```text
                    +----------------------+
                    |       Client         |
                    |  HTTP / REST caller  |
                    +----------+-----------+
                               |
                               | HTTP :8000
                               v
                    +----------------------+
                    |    Docker Container  |
                    |                      |
                    |       FastAPI        |
                    |          |           |
                    |          v           |
                    |   AccessAnalyzer     |
                    |          |           |
                    |    +-----+-----+     |
                    |    |     |     |     |
                    |    v     v     v     |
                    | Policy  Risk  Priv.  |
                    | Match   Score Detect  |
                    |    |     |     |     |
                    |    +-----+-----+     |
                    |          |           |
                    |          v           |
                    |     AccessDecision   |
                    |          |           |
                    |          v           |
                    |     AuditLogger      |
                    +----------------------+
```

---

# 4. Trust Boundaries

The architecture contains several important trust boundaries.

## 4.1 External client → FastAPI

```text
UNTRUSTED CLIENT
       |
       | HTTP request
       v
FASTAPI APPLICATION
```

Everything supplied by the API client must be treated as untrusted input.

This includes:

- principal ID
- principal type
- resource ID
- resource type
- action name
- request context

---

## 4.2 API layer → analyzer

The API converts external request models into internal domain models.

```text
API request
    |
    v
Pydantic validation
    |
    v
Internal domain objects
    |
    v
AccessAnalyzer
```

This boundary prevents the HTTP representation from becoming the application's internal authorization representation directly.

---

## 4.3 Analyzer → policy data

The analyzer relies on configured policy objects.

The policy set is security-sensitive because incorrect policy data can directly affect authorization decisions.

---

## 4.4 Application → audit output

Audit events contain security-relevant information.

Audit output therefore represents a separate security-sensitive data flow.

---

## 4.5 Host → Docker container

The host operating system and Docker runtime provide the execution boundary for the application.

```text
HOST
 |
 | Docker runtime
 v
CONTAINER
 |
 +--> Python
 +--> FastAPI
 +--> IAM Analyzer
```

Containerization reduces dependency on the host Python environment but does not make the application automatically secure.

---

# 5. Assets

The primary assets are:

| Asset | Security importance |
|---|---|
| Authorization decisions | Critical |
| IAM policy definitions | Critical |
| Principal identity | High |
| Resource identity | High |
| Action being requested | High |
| Request context | High |
| Risk score | High |
| Privileged classification | High |
| Audit events | High |
| Application integrity | High |
| Docker image | High |
| API availability | Medium |

---

# 6. Actors

## 6.1 Legitimate API client

A trusted internal consumer may submit access-analysis requests.

---

## 6.2 Malicious API client

An attacker may attempt to manipulate request fields to obtain an incorrect authorization decision or hide a risky action.

---

## 6.3 Malicious or compromised principal

A legitimate identity may be compromised and used to request sensitive actions.

---

## 6.4 Malicious insider

An administrator or developer with access to policies, configuration, logs, or deployment infrastructure may attempt to weaken controls.

---

## 6.5 Compromised host

A compromised Docker host could potentially affect containers, configuration, secrets, or application availability.

---

# 7. Threat-Model Method

The analysis uses a STRIDE-style threat classification combined with IAM-specific authorization threats.

Relevant categories include:

- Spoofing
- Tampering
- Repudiation
- Information Disclosure
- Denial of Service
- Elevation of Privilege

The threat analysis is focused on the actual v0.3 architecture and implementation rather than hypothetical cloud-provider capabilities that are not implemented by the project.

---

# 8. Threat Analysis

## T1 — Principal Spoofing

**Category:** Spoofing

### Threat

A malicious caller may submit another user's principal ID, for example:

```text
user:alice@example.com
```

without actually being Alice.

### Attack path

```text
Attacker
   |
   | forged principal.id
   v
FastAPI
   |
   v
AccessAnalyzer
```

If the analyzer is exposed directly without an upstream authenticated identity layer, the caller-controlled principal becomes untrusted authorization input.

### Impact

Potential unauthorized access decisions.

### Current mitigation

The analyzer is an evaluation engine, not a complete identity provider.

The API validates request structure using Pydantic, but the current application does not establish the caller's real-world identity.

### Residual risk

**High** if deployed directly as an externally reachable authorization service.

### Recommended production control

Authenticate the caller upstream and derive the principal from a trusted identity token/session rather than accepting an arbitrary principal identity from the client.

---

# T2 — Action Manipulation

**Category:** Tampering / Elevation of Privilege

### Threat

An attacker may manipulate the requested action.

For example, an attacker could replace:

```text
storage.objects.get
```

with:

```text
iam.roles.update
```

or another sensitive action.

### Impact

Incorrect authorization analysis or privileged-operation classification.

### Current mitigation

The analyzer treats the action as a first-class domain object and performs explicit policy matching.

Privileged actions are explicitly classified.

### Residual risk

**Medium**

### Recommended production control

The action should originate from a trusted service or authenticated authorization context whenever possible. The analyzer should not be treated as the authoritative source of the caller's identity or actual operation.

---

# T3 — Resource Manipulation

**Category:** Tampering

### Threat

A caller may change the resource identifier to target a more sensitive resource.

Example:

```text
bucket:dev-data
```

changed to:

```text
bucket:prod-data
```

### Impact

Potential unauthorized access if the configured policies are broader than intended.

### Current mitigation

Policy matching includes the resource as part of the match.

### Residual risk

**Medium**

### Recommended production control

Resource identity should be derived from a trusted request path or service context and policies should use least-privilege resource scopes.

---

# T4 — Condition Bypass

**Category:** Tampering / Elevation of Privilege

### Threat

An attacker attempts to satisfy or manipulate contextual conditions used by a policy.

Example condition:

```text
environment = production
```

The attacker may attempt to provide a forged context claiming:

```text
environment = production
```

### Impact

A conditional policy could incorrectly become applicable.

### Current mitigation

The analyzer explicitly evaluates policy conditions before adding policies to the matching set.

### Residual risk

**High** if request context is directly caller-controlled.

### Recommended production control

Security-sensitive context should come from trusted infrastructure signals such as:

- authenticated identity claims
- workload identity
- network identity
- device posture
- trusted service metadata

Do not treat arbitrary client-provided context as authoritative.

---

# T5 — Expired Policy Reuse

**Category:** Elevation of Privilege

### Threat

An attacker attempts to use a policy after its intended expiration time.

### Impact

Stale authorization may remain effective longer than intended.

### Current mitigation

The analyzer evaluates policy expiration and skips expired policies.

### Residual risk

**Low to Medium**

### Recommended production control

Use authoritative time sources and ensure policy stores cannot silently retain expired grants indefinitely.

---

# T6 — Explicit Deny Bypass

**Category:** Elevation of Privilege / Tampering

### Threat

A malicious or incorrectly implemented policy evaluation path could allow access despite an explicit deny.

### Impact

High because deny precedence is a core authorization security property.

### Current mitigation

The analyzer evaluates matching policies and checks for `Effect.DENY` before returning an allow decision.

### Residual risk

**Low** for the current implementation, subject to test coverage.

### Validation evidence

The project contains analyzer tests covering policy evaluation behavior.

---

# T7 — Privileged Action Misclassification

**Category:** Elevation of Privilege

### Threat

A sensitive operation may not be included in the privileged-action classification set.

Current v0.3 classification includes:

```text
iam.roles.create
iam.roles.update
iam.roles.delete
```

An action outside this explicit set can therefore return:

```text
privileged = False
```

even if a production IAM platform considers that action sensitive.

### Impact

A privileged operation may not receive the expected security signal.

### Current mitigation

Privileged actions are centralized in:

```text
src/iam_analyzer/privileged.py
```

### Residual risk

**Medium**

### Important limitation

The current privileged detector is an explicit application-level classification list.

It is not a complete cloud-provider privilege ontology.

### Recommended production control

Use a maintained, provider-specific action catalog and categorize actions according to impact, not only naming conventions.

---

# T8 — Risk Score Manipulation or Misinterpretation

**Category:** Tampering / Elevation of Privilege

### Threat

A caller or downstream consumer may treat the risk score as an authorization control rather than a security signal.

### Impact

A low score could be incorrectly interpreted as safe authorization.

### Current mitigation

The analyzer keeps authorization effect and risk score as separate decision attributes.

### Residual risk

**Medium**

### Recommended production control

Clearly define risk-score semantics and prevent downstream systems from treating the score as a substitute for authorization policy.

---

# T9 — Audit Log Tampering

**Category:** Tampering / Repudiation

### Threat

An attacker who gains access to audit output may modify or delete records to hide activity.

### Impact

Loss of forensic evidence and accountability.

### Current mitigation

The application provides an `AuditLogger` abstraction and records an `AuditEvent` when an analyzer decision is produced.

### Residual risk

**Medium to High**

### Current limitation

The project does not implement a hardened external immutable audit store.

### Recommended production control

Forward audit events to a centralized security logging platform with:

- append-only storage
- access controls
- retention policy
- integrity protection
- alerting

---

# T10 — Sensitive Information Disclosure Through Logs

**Category:** Information Disclosure

### Threat

Audit events contain security-relevant request information.

If logs are exposed to unauthorized users, they may reveal:

- principals
- resources
- actions
- authorization outcomes

### Impact

Information leakage and increased attacker reconnaissance capability.

### Current mitigation

Audit events are explicitly modeled rather than arbitrary application logging.

### Residual risk

**Medium**

### Recommended production control

Apply log access controls, retention rules, and data minimization.

---

# T11 — API Denial of Service

**Category:** Denial of Service

### Threat

An attacker sends a large volume of requests to the API.

### Impact

Resource exhaustion and service unavailability.

### Current mitigation

The application is containerized and the API is isolated as a service.

### Residual risk

**Medium**

### Recommended production control

Use:

- authentication
- rate limiting
- request size limits
- reverse proxy protection
- resource quotas
- autoscaling where appropriate

---

# T12 — Malicious Request Payload

**Category:** Tampering / Denial of Service

### Threat

An attacker submits malformed or unexpectedly large request fields.

### Impact

Application errors, resource consumption, or unexpected behavior.

### Current mitigation

FastAPI/Pydantic request models validate the API structure.

### Residual risk

**Low to Medium**

### Recommended production control

Add explicit limits for:

- string lengths
- context size
- request body size
- allowed action formats

---

# T13 — Dependency or Base Image Vulnerability

**Category:** Tampering / Elevation of Privilege

### Threat

A vulnerable Python package or vulnerable base image could introduce exploitable code into the container.

### Current implementation

The image is built from:

```text
python:3.14-slim
```

and installs pinned application dependencies from `pyproject.toml`.

### Impact

Container compromise or application compromise.

### Residual risk

**Medium**

### Recommended production controls

Use:

- dependency vulnerability scanning
- image vulnerability scanning
- regular base-image updates
- dependency review
- minimal runtime dependencies
- signed/provenance-aware image pipelines

---

# T14 — Container Escape / Host Compromise

**Category:** Elevation of Privilege

### Threat

A vulnerability in the container runtime, kernel, or application could potentially allow an attacker to affect the Docker host.

### Impact

Potential compromise beyond the application container.

### Current mitigation

Docker provides process and filesystem isolation.

The application uses a slim Linux base image.

### Residual risk

**Low to Medium** in the local development environment, but potentially severe in production.

### Recommended production controls

Use:

- non-root containers
- read-only filesystems where possible
- dropped Linux capabilities
- seccomp/AppArmor/SELinux controls
- minimal host privileges
- patched Docker/runtime/kernel

---

# T15 — Unauthorized Policy Modification

**Category:** Tampering / Elevation of Privilege

### Threat

An attacker with access to the policy configuration could modify an allow policy to grant unauthorized access.

### Impact

Critical authorization compromise.

### Current mitigation

The current educational implementation uses configured in-memory policy objects.

### Residual risk

**High** for production use because the project does not implement a hardened policy-management control plane.

### Recommended production control

Protect policy administration using:

- strong authentication
- least privilege
- separation of duties
- change review
- versioning
- audit trails
- policy-as-code controls

---

# T16 — Unauthorized Container Image Modification

**Category:** Tampering

### Threat

An attacker modifies the Docker image or build inputs to introduce malicious code.

### Impact

Compromise of every deployment using the affected image.

### Current mitigation

The project builds a deterministic application image from a Dockerfile and source tree.

### Residual risk

**Medium**

### Recommended production control

Use a trusted CI/CD pipeline, image scanning, provenance/attestation, registry access controls, and image signing.

---

# 9. Risk Register

| ID | Threat | Category | Impact | Likelihood | Risk |
|---|---|---|---|---|---|
| T1 | Principal spoofing | Spoofing | High | High | Critical |
| T2 | Action manipulation | Tampering / EoP | High | Medium | High |
| T3 | Resource manipulation | Tampering | High | Medium | High |
| T4 | Condition bypass | Tampering / EoP | High | Medium | High |
| T5 | Expired policy reuse | EoP | High | Low | Medium |
| T6 | Explicit deny bypass | EoP | Critical | Low | High |
| T7 | Privileged misclassification | EoP | High | Medium | High |
| T8 | Risk-score misuse | Tampering / EoP | Medium | Medium | Medium |
| T9 | Audit tampering | Tampering / Repudiation | High | Medium | High |
| T10 | Log disclosure | Information Disclosure | Medium | Medium | Medium |
| T11 | API DoS | DoS | Medium | Medium | Medium |
| T12 | Malicious payload | Tampering / DoS | Medium | Medium | Medium |
| T13 | Dependency/image vulnerability | Tampering / EoP | High | Medium | High |
| T14 | Container escape | EoP | Critical | Low | High |
| T15 | Policy modification | Tampering / EoP | Critical | Medium | Critical |
| T16 | Image modification | Tampering | Critical | Low | High |

---

# 10. Security Controls Implemented in v0.3

The current implementation contains the following relevant controls.

## Authorization

- Principal matching
- Resource matching
- Action matching
- Explicit deny precedence
- Default deny when no matching policy exists

## Conditional access

- Policy conditions
- Request context evaluation

## Temporary access

- Policy expiration

## Risk analysis

- Risk scoring
- Privileged action detection

## Auditability

- Structured `AuditEvent`
- `AuditLogger` integration

## API security foundation

- FastAPI request models
- Pydantic validation
- Explicit response model

## Deployment

- Docker containerization
- Slim Python base image
- Application dependencies installed inside the image
- Port `8000` exposed for the API

---

# 11. Attack Scenarios Demonstrated by the Project

## Scenario A — Normal access

```text
Alice
 |
 | storage.objects.get
 v
IAM Analyzer
 |
 +--> policy matches
 +--> privileged = False
 +--> risk score = 10
 |
 v
ALLOW
```

This demonstrates normal authorization.

---

## Scenario B — Privileged access

```text
Alice
 |
 | iam.roles.update
 v
IAM Analyzer
 |
 +--> policy matches
 +--> privileged = True
 +--> risk score = 70
 |
 v
ALLOW + HIGHER SECURITY SIGNAL
```

This demonstrates that authorization and privileged classification are separate.

---

## Scenario C — Unknown principal

```text
Bob
 |
 | storage.objects.get
 v
IAM Analyzer
 |
 +--> no matching policy
 |
 v
DENY
```

This demonstrates default-deny behavior.

---

## Scenario D — Explicit deny

Where an applicable deny policy exists:

```text
Request
  |
  v
Matching policies
  |
  +--> DENY
  |
  v
DENY
```

The explicit deny takes precedence over an allow.

---

# 12. Abuse Cases

The most important abuse cases for the analyzer are:

### AC-01 — Forge a privileged identity

Attacker supplies another principal's identifier.

**Control:** upstream authentication and trusted principal derivation.

---

### AC-02 — Request a sensitive action under a broad allow policy

Attacker requests:

```text
iam.roles.update
```

while holding an applicable policy.

**Control:** privileged classification + risk score + downstream monitoring.

---

### AC-03 — Forge security context

Attacker manipulates context values to satisfy a conditional policy.

**Control:** trusted context providers.

---

### AC-04 — Modify policy to grant access

Attacker changes an allow policy.

**Control:** protected policy administration and change auditing.

---

### AC-05 — Hide unauthorized activity

Attacker attempts to modify or delete audit evidence.

**Control:** centralized immutable audit logging.

---

### AC-06 — Exploit container dependencies

Attacker exploits a vulnerable dependency or base image.

**Control:** dependency and image scanning plus controlled CI/CD.

---

# 13. Security Boundaries and Assumptions

The threat model assumes:

1. The host running Docker is trusted for local development.
2. Docker Desktop and the WSL2 backend are correctly installed and maintained.
3. The analyzer's source code is trusted.
4. The configured policies are trusted.
5. The API is not itself an identity provider.
6. Authentication and identity establishment are outside the current project scope.
7. The current policy configuration is intentionally small and educational.
8. The privileged action catalog is intentionally limited.
9. The risk score is an analysis signal, not a replacement for authorization.
10. Production deployment would require stronger controls than the local demonstration environment.

---

# 14. Security Design Principles

The architecture follows several important security principles.

## Least privilege

Policies should grant only the minimum required principal/resource/action combination.

---

## Default deny

No matching policy results in:

```text
DENY
```

---

## Explicit deny precedence

A deny cannot be overridden by a matching allow.

---

## Separation of concerns

The system separates:

```text
Authorization
     |
     +--> Risk analysis
     |
     +--> Privilege classification
     |
     +--> Audit
```

This is preferable to combining all security signals into a single boolean decision.

---

## Defense in depth

The analyzer combines:

- policy matching
- conditions
- expiration
- explicit denies
- risk scoring
- privileged detection
- audit logging
- API validation
- container isolation

No single control is assumed to provide complete security.

---

# 15. Production Hardening Roadmap

The current project is intentionally an educational engineering implementation.

The following controls would be appropriate before production use.

## Identity

- OAuth/OIDC or equivalent authentication
- trusted principal derivation
- service-to-service authentication
- workload identity

## Authorization

- centralized policy store
- policy versioning
- policy administration RBAC
- separation of duties
- policy change approval

## Context

- trusted device/network/workload context
- signed identity claims
- server-derived security context

## Privileged access

- provider-specific privileged action catalog
- sensitive resource classification
- just-in-time elevation
- approval workflows
- privileged access alerts

## Audit

- centralized SIEM integration
- immutable/append-only storage
- retention policy
- alerting
- audit integrity controls

## API

- authentication
- authorization
- rate limiting
- request size limits
- structured error handling
- TLS termination

## Container

- run as non-root
- read-only root filesystem where possible
- drop unnecessary capabilities
- vulnerability scanning
- image signing
- provenance/attestation
- minimal runtime image

## Supply chain

- dependency pinning
- dependency vulnerability scanning
- automated image scanning
- trusted CI/CD
- protected main branch
- reproducible builds

---

# 16. Threat Model Summary

The highest-impact threats are:

```text
1. Principal spoofing
2. Unauthorized policy modification
3. Condition/context manipulation
4. Privileged-action misclassification
5. Container/image compromise
6. Audit tampering
```

The most important architectural observation is:

> The analyzer should not be treated as a complete IAM enforcement system merely because it produces an authorization decision.

It is an analysis engine. Identity establishment, trusted context, policy administration, deployment security, and production audit infrastructure must be protected independently.

---

# 17. Finisher Demo Mapping

The threat model is demonstrated by the v0.3 local Docker deployment.

## Evidence 1 — Container

```powershell
docker ps
```

Demonstrates that the analyzer runs inside Docker.

---

## Evidence 2 — Health

```powershell
Invoke-RestMethod http://localhost:8000/health
```

Expected:

```text
status
------
ok
```

Demonstrates API availability.

---

## Evidence 3 — Normal access

Action:

```text
storage.objects.get
```

Expected:

```text
allow
privileged = False
```

Demonstrates standard authorization.

---

## Evidence 4 — Privileged access

Action:

```text
iam.roles.update
```

Expected:

```text
allow
risk_score = 70
privileged = True
```

This is the primary v0.3 security demonstration.

---

## Evidence 5 — Container logs

```powershell
docker logs iam-access-analyzer
```

Demonstrates successful API execution inside the container.

---

# 18. Architecture Defense Talking Points

For a 5–10 minute architecture defense, explain the system in this order:

### 1. Problem

> "The project analyzes IAM access requests and makes authorization decisions while also exposing security-relevant signals such as risk and privileged access."

### 2. Core decision engine

> "The AccessAnalyzer evaluates principal, resource, action, policy conditions, expiration, and deny precedence."

### 3. Security signals

> "Risk scoring and privileged-access detection are deliberately separate from the authorization effect."

### 4. Privileged access

> "An action such as `iam.roles.update` can be allowed while still being flagged as privileged and assigned a higher risk score."

### 5. Audit

> "Every analyzer decision can produce a structured audit event containing the principal, resource, action, effect, reason, and timestamp."

### 6. API

> "FastAPI exposes the analyzer through a validated REST interface."

### 7. Containerization

> "Docker packages the application and dependencies into a reproducible Linux runtime."

### 8. Threat model

> "The main security risks are identity spoofing, policy tampering, context manipulation, privileged-action misclassification, audit tampering, and container supply-chain risk."

### 9. Production boundary

> "The current implementation is an analysis engine and demonstration platform. Production deployment would require trusted identity, protected policy administration, centralized immutable audit logging, stronger API controls, and container supply-chain security."

---

# 19. Final Security Assessment

The v0.3 implementation demonstrates a meaningful security-engineering progression:

```text
v0.2
 |
 +--> IAM policy evaluation
 |
 v
v0.3
 |
 +--> Risk scoring
 +--> Audit logging
 +--> Privileged access detection
 +--> FastAPI interface
 +--> Docker containerization
 |
 v
Threat-modeled security analyzer
```

The implementation demonstrates the core security principle that **authorization, risk, and privilege are distinct dimensions of an access request**.

The strongest demonstrated control is the ability to identify privileged access even when the authorization result is `ALLOW`.

The principal remaining security limitation is that identity, policy administration, trusted context, audit storage, and production deployment controls are outside the current educational analyzer boundary.

That boundary is intentional and should be explicitly stated during the final architecture demonstration.
