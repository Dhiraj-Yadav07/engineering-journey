# GCP 15 — Enterprise GCP Landing Zone with Identity Controls

## Objective

Design a secure enterprise Google Cloud landing zone that establishes strong identity controls, administrative boundaries, preventive guardrails, workload isolation, and centralized security visibility.

This is an **architecture gate**, not a deployment lab. The primary deliverables are:

- High-Level Design (HLD)
- Threat model
- Supporting architecture evidence

The design focuses on identity as the primary security control plane and uses the GCP resource hierarchy to create explicit trust and administrative boundaries.

---

## Architecture Goals

```text
Centralized identity
        +
Least-privilege authorization
        +
Environment isolation
        +
Preventive governance
        +
Workload identity
        +
Privileged-access isolation
        +
Centralized logging and detection
        =
Secure enterprise GCP foundation
```

The design should reduce the blast radius of:

- compromised user identities
- compromised workloads
- service-account compromise
- excessive IAM permissions
- privilege escalation
- malicious insiders
- CI/CD identity compromise
- data exfiltration
- project misconfiguration
- security-control bypass

---

## Target GCP Resource Hierarchy

```text
GCP Organization
│
├── Security
│   ├── sec-scc
│   ├── sec-logging
│   └── sec-forensics
│
├── Platform
│   ├── net-host
│   ├── shared-services
│   └── cicd
│
├── Production
│   ├── app-a
│   ├── app-b
│   └── data
│
├── Non-Production
│   ├── app-a-dev
│   ├── app-a-test
│   └── app-b-dev
│
└── Sandbox
    └── developer-sandbox
```

The hierarchy is part of the security model.

Organization-level controls establish enterprise-wide guardrails, folders create administrative and environmental boundaries, and projects represent workload trust boundaries.

---

## Identity Architecture

Human and workload identities are deliberately separated.

```text
                    Corporate IdP
                         |
                         v
                 Cloud Identity /
                Workforce Federation
                         |
                         v
                       Groups
                         |
          +--------------+--------------+
          |              |              |
          v              v              v
     Developers       Security       Platform
          |              |              |
          +--------------+--------------+
                         |
                         v
                        IAM
                         |
          +--------------+--------------+
          |              |              |
          v              v              v
       Folders        Projects       Resources
```

### Human Identity

Users authenticate using the enterprise workforce identity plane.

Authorization is primarily granted through groups rather than direct user-by-user IAM bindings.

Example groups:

```text
grp-gcp-org-admin
grp-gcp-security-admin
grp-gcp-network-admin
grp-gcp-platform-admin

grp-gcp-prod-developers
grp-gcp-prod-operators

grp-gcp-nonprod-developers
grp-gcp-sandbox-users

grp-gcp-security-readers
grp-gcp-auditors
```

The goal is to separate roles and responsibilities rather than allowing a single identity to accumulate unrelated administrative privileges.

---

## Privileged Access Model

Normal engineering identities should not be the same identities used for high-impact administrative operations.

```text
Normal workforce identity
        |
        v
Day-to-day engineering access
        |
        v
Least-privilege IAM


Dedicated privileged identity
        |
        v
Strong authentication / MFA
        |
        v
Privileged administrative access
```

High-risk administrative roles should be isolated from normal developer access.

A dedicated break-glass capability should exist for emergencies and should be tightly controlled and audited.

---

## Workload Identity

Workloads receive identities independently from human users.

```text
Application / Workload
        |
        v
Workload Identity
        |
        v
Dedicated service identity
        |
        v
Least-privilege IAM
        |
        v
Specific GCP resources
```

For external CI/CD systems:

```text
External CI/CD
       |
       v
Workload Identity Federation
       |
       v
Federated workload identity
       |
       v
Scoped GCP permissions
```

Long-lived service-account keys should not be the normal mechanism for workload authentication.

Each significant workload or trust boundary should have a dedicated service identity rather than sharing a single highly privileged service account.

---

## IAM Design Principles

### 1. Least privilege

Grant only the permissions required for the intended operation.

```text
Organization-wide broad role
          X

Project-scoped role
          |
          v
Resource-specific role where practical
```

### 2. Group-based authorization

Prefer:

```text
User
  -> Group
      -> IAM role
```

over:

```text
User
  -> Direct IAM role
```

### 3. Separation of duties

Security administrators, network administrators, platform administrators, developers, and auditors should have distinct responsibilities.

### 4. Minimize inheritance risk

IAM inheritance is powerful but can unintentionally broaden access.

Therefore:

- place identities at the appropriate folder boundary
- use project-level roles where possible
- use resource-level permissions for sensitive resources
- avoid granting broad organization-level roles without a strong business justification

---

## Organization Guardrails

The organization acts as the preventive governance layer.

Representative controls include:

```text
Organization Policies
        |
        +-- Restrict service-account key creation
        |
        +-- Prevent broad default service-account grants
        |
        +-- Restrict allowed resource locations
        |
        +-- Restrict external identity / sharing patterns
        |
        +-- Enforce enterprise security requirements
```

These controls establish minimum security standards that individual application teams should not be able to bypass casually.

---

## Environment Isolation

The landing zone separates:

```text
Production
Non-Production
Sandbox
```

The objective is to prevent lower-trust environments from inheriting production-level access.

Example:

```text
Developer
   |
   +----> Non-Production
   |          |
   |          +----> broad engineering permissions
   |
   X----> Production administration
```

Production access should require explicit authorization.

Sandbox environments should be treated as the lowest-trust environment and should not be allowed to become a path into production resources.

---

## Network and Data Security Foundation

The landing zone also establishes centralized network and data security controls.

```text
                     Organization
                          |
                    Shared Network
                          |
        +-----------------+-----------------+
        |                 |                 |
        v                 v                 v
   Production         Non-Production     Sandbox
        |                 |                 |
        +-----------------+-----------------+
                          |
                    Data boundaries
                          |
                    VPC Service Controls
```

Representative controls include:

- Shared VPC for centralized network governance
- network segmentation
- centralized DNS
- private access patterns
- controlled egress
- VPC Service Controls for sensitive data boundaries

Network controls complement IAM; IAM determines who can access a resource, while network/data boundaries help constrain where protected resources and data can be reached or moved.

---

## Central Security and Detection Plane

Security visibility should be centralized.

```text
Projects
   |
   +---- IAM activity
   +---- Administrative activity
   +---- Data-access activity
   |
   v
Cloud Audit Logs
   |
   v
Centralized Logging
   |
   +-------------------+
   |                   |
   v                   v
Security Command    Monitoring /
Center              SIEM / Alerting
   |
   v
Findings
   |
   v
Investigation / Response
```

The security organization should have visibility across production, non-production, and sandbox environments without granting application developers unrestricted security-administration privileges.

---

## Security Trust Boundaries

The design uses multiple trust boundaries:

```text
Organization
    |
    +-- Enterprise-wide governance boundary
    |
    +-- Security / Platform folders
    |
    +-- Production / Non-Production / Sandbox boundaries
    |
    +-- Project workload boundaries
    |
    +-- Resource boundaries
```

A compromise should ideally remain inside the smallest practical boundary.

For example:

```text
Compromised application identity
        |
        v
Application project
        |
        X
Other application projects
        |
        X
Security administration
        |
        X
Organization administration
```

---

## Threat Model

The associated threat model evaluates the architecture against common enterprise cloud attack paths.

### Primary threats

```text
1. Workforce identity compromise
2. Privilege escalation
3. Service-account compromise
4. Credential theft
5. CI/CD identity compromise
6. Malicious insider
7. Cross-project unauthorized access
8. Data exfiltration
9. Project misconfiguration
10. Logging / detection bypass
```

Each threat is analyzed using:

```text
Threat
   ->
Attack path
   ->
Preventive control
   ->
Detective control
   ->
Blast-radius reduction
   ->
Residual risk
```

See [`threat-model.md`](./threat-model.md).

---

## Example Threat: Compromised Developer

```text
Attacker obtains developer credentials
                |
                v
         Developer account
                |
                v
      Non-Production access
                |
                X
      Production administration
                |
                X
      Organization administration
```

Controls:

```text
Workforce identity
        +
MFA
        +
Group-based IAM
        +
Production separation
        +
Least privilege
        +
Audit logging
        =
Reduced blast radius
```

---

## Example Threat: Compromised Workload

```text
Application vulnerability
        |
        v
Compromised workload
        |
        v
Workload identity
        |
        v
Scoped permissions
        |
        +----> Required resources
        |
        X----> Security administration
        |
        X----> Other workloads
        |
        X----> Organization administration
```

The architecture limits the attacker's effective privilege to the permissions assigned to the compromised workload identity.

---

## Security Properties

| Property | Architectural mechanism |
|---|---|
| Central identity | Cloud Identity / workforce federation |
| Group-based access | IAM groups |
| Least privilege | Scoped IAM roles |
| Human/workload separation | Workforce identity vs workload identity |
| Credential-risk reduction | Federation / short-lived credentials |
| Privileged-access isolation | Dedicated admin identities |
| Blast-radius reduction | Folder and project trust boundaries |
| Preventive governance | Organization Policy |
| Environment isolation | Production / Non-Production / Sandbox |
| Data-boundary protection | VPC Service Controls |
| Central visibility | Cloud Audit Logs |
| Threat detection | Security Command Center |
| Investigation | Central security findings and logging |

---

## HLD Deliverable

The detailed HLD is documented in:

```text
architecture.md
```

It covers:

```text
Organization hierarchy
        |
        v
Folder model
        |
        v
Identity architecture
        |
        v
IAM trust boundaries
        |
        v
Workload identity
        |
        v
Organization guardrails
        |
        v
Network / data boundaries
        |
        v
Centralized logging and detection
```

---

## Evidence

Architecture evidence is stored under:

```text
evidence/
├── identity-controls.txt
├── organization-controls.txt
└── threat-analysis.txt
```

These files capture the key security decisions and supporting analysis for the architecture gate.

---

## Repository Structure

```text
15-gcp-enterprise-landing-zone/
├── README.md
├── architecture.md
├── threat-model.md
└── evidence/
    ├── identity-controls.txt
    ├── organization-controls.txt
    └── threat-analysis.txt
```

---

## Expected Security Outcome

The landing zone should establish the following security model:

```text
                 Enterprise Identity
                         |
                         v
                       Groups
                         |
                         v
                        IAM
                         |
       +-----------------+-----------------+
       |                 |                 |
       v                 v                 v
  Production        Non-Production      Sandbox
       |                 |                 |
       +-----------------+-----------------+
                         |
                         v
                 Workload identities
                         |
                         v
                Least-privilege access
                         |
                         v
               Organization guardrails
                         |
                         v
              Audit + Detection + SCC
```

The desired property is:

> **Compromising one identity, workload, or project should not automatically provide organization-wide administrative access or unrestricted access to enterprise data.**

---

## Gate Status

**Architecture gate: In progress**

Primary deliverables:

```text
HLD
+
Threat Model
```

Target outcome:

**Secure enterprise GCP landing zone with strong identity controls, explicit trust boundaries, preventive governance, and centralized security visibility.**
