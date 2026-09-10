# GCP 15 — Enterprise GCP Landing Zone — High-Level Architecture

## 1. Architecture Objective

Design a secure enterprise Google Cloud landing zone that establishes:

- strong workforce and workload identity controls
- least-privilege authorization
- clear administrative and trust boundaries
- production and non-production isolation
- organization-wide preventive guardrails
- centralized security logging and detection
- controlled privileged access
- reduced blast radius for compromised identities and workloads

The architecture is intentionally designed as a reusable enterprise foundation,
not as a single application deployment.

---

## 2. Design Principles

### Identity first

Identity is the primary authorization plane.

```text
Human -> Workforce Identity -> Group -> IAM -> GCP Resource

Workload -> Workload Identity -> Service Identity -> IAM -> GCP Resource
```

### Least privilege

Grant the smallest practical permission scope.

```text
Organization
    X  Broad application access

Folder
    X  Unless shared by multiple projects

Project
    OK  Common workload boundary

Resource
    Preferred when practical for sensitive access
```

### Trust boundaries

Use the GCP resource hierarchy to create explicit security boundaries.

```text
Organization
    |
    +-- Security
    +-- Platform
    +-- Production
    +-- Non-Production
    +-- Sandbox
```

### Defense in depth

IAM is necessary but is not the only control.

```text
Identity
   +
IAM
   +
Organization Policy
   +
Network / Data Boundaries
   +
Audit Logging
   +
Security Detection
```

---

## 3. Target Resource Hierarchy

```text
GCP Organization
|
+-- Security
|   +-- sec-scc
|   +-- sec-logging
|   +-- sec-forensics
|
+-- Platform
|   +-- net-host
|   +-- shared-services
|   +-- cicd
|
+-- Production
|   +-- app-a
|   +-- app-b
|   +-- data
|
+-- Non-Production
|   +-- app-a-dev
|   +-- app-a-test
|   +-- app-b-dev
|
+-- Sandbox
    +-- developer-sandbox
```

### Rationale

**Security** provides an administrative boundary for security tooling,
audit data, and investigation capabilities.

**Platform** contains shared infrastructure such as networking, DNS, CI/CD,
and common services.

**Production** contains high-value workloads and should have the strongest
access restrictions.

**Non-Production** allows engineering activity without automatically
granting equivalent production privileges.

**Sandbox** is treated as the lowest-trust environment and should not become
a path into production.

---

## 4. Identity Architecture

```text
                       Corporate IdP
                            |
                            v
                 Cloud Identity / Federation
                            |
                            v
                          Groups
                            |
            +---------------+---------------+
            |               |               |
            v               v               v
       Developers        Security        Platform
            |               |               |
            +---------------+---------------+
                            |
                            v
                           IAM
                            |
             +--------------+--------------+
             |              |              |
             v              v              v
          Folder         Project        Resource
           access         access         access
```

The preferred authorization path is:

```text
User
  -> Group
      -> IAM role
          -> Resource
```

rather than granting broad roles directly to individual users.

---

## 5. Human Identity Model

Representative enterprise groups:

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

### Separation of duties

| Function | Primary responsibility |
|---|---|
| Organization admin | Organization-wide governance |
| Security admin | Security tooling, posture, investigation |
| Network admin | Shared network and connectivity |
| Platform admin | Shared platform services |
| Production developer | Application development/deployment |
| Production operator | Operational support |
| Auditor | Read-only audit and compliance access |
| Security reader | Read-only security visibility |

No single everyday engineering group should automatically receive all
administrative capabilities.

---

## 6. Privileged Access Architecture

Normal and privileged identities are separated.

```text
Normal workforce identity
        |
        v
Day-to-day engineering
        |
        v
Least-privilege roles


Dedicated privileged identity
        |
        v
Strong authentication / MFA
        |
        v
High-impact administrative roles
```

### Break-glass

A separate emergency access mechanism should exist for organization-level
recovery.

Requirements:

- separate from normal user credentials
- protected by strong authentication
- very limited membership
- used only for emergency recovery
- fully audited
- periodically tested

---

## 7. Workload Identity Architecture

Workloads must not depend on human credentials.

```text
Application
    |
    v
Workload Identity / Attached Service Identity
    |
    v
Dedicated Service Identity
    |
    v
Scoped IAM permissions
    |
    v
Required GCP resources only
```

### External CI/CD

```text
GitHub / External CI/CD
        |
        v
Workload Identity Federation
        |
        v
Federated workload principal
        |
        v
Scoped IAM permissions
```

Long-lived service-account keys should not be the normal authentication
mechanism for workloads.

---

## 8. Service Account Model

Avoid shared, highly privileged service identities.

### Anti-pattern

```text
100 workloads
      |
      v
one service account
      |
      v
roles/editor
```

### Preferred model

```text
Application A -> sa-app-a -> minimum required permissions

Application B -> sa-app-b -> minimum required permissions

CI/CD        -> sa-cicd  -> deployment permissions only
```

This limits the blast radius when a workload identity is compromised.

---

## 9. IAM Scope Strategy

Authorization should be granted at the lowest practical level.

```text
Organization
    |
    +-- Enterprise-wide administrative controls

Folder
    |
    +-- Shared environment/function permissions

Project
    |
    +-- Workload trust boundary

Resource
    |
    +-- Sensitive resource-specific access
```

Examples:

```text
Developer group
    -> non-production application project

Production operator group
    -> production operational roles

Application service identity
    -> specific data or API resources

Security reader group
    -> security visibility without production modification
```

---

## 10. Organization Policy Layer

The organization is the preventive governance plane.

```text
                 Organization Policies
                         |
       +-----------------+-----------------+
       |                 |                 |
       v                 v                 v
 Identity controls   Resource controls  Data controls
       |                 |                 |
       v                 v                 v
 SA key restrictions  Location rules    External sharing
 Default SA rules     Service limits    Data boundaries
```

Representative guardrails:

- restrict service-account key creation
- prevent automatic broad IAM grants to default service accounts
- restrict resource locations
- constrain external identity and resource-sharing patterns
- enforce enterprise-required security configurations

Policies can be applied at organization, folder, or project boundaries
depending on the control requirement.

---

## 11. Environment Isolation

The trust relationship is intentionally asymmetric.

```text
Developer
   |
   +----> Non-Production
   |
   X----> Production administration


Sandbox workload
   |
   +----> Sandbox resources
   |
   X----> Production resources
```

Production access should require explicit authorization.

Non-production permissions should not be assumed to imply production access.

---

## 12. Network and Data Security Foundation

The landing zone complements IAM with network and data boundaries.

```text
                    Organization
                         |
                    Shared Network
                         |
        +----------------+----------------+
        |                |                |
        v                v                v
   Production       Non-Production     Sandbox
        |                |                |
        +----------------+----------------+
                         |
                  Data boundaries
                         |
                  VPC Service Controls
```

Representative controls:

- Shared VPC for centralized network governance
- subnet and workload segmentation
- centralized DNS
- private access patterns
- controlled egress
- VPC Service Controls around sensitive services and data

IAM answers **who can access**.

Network and service-perimeter controls help constrain **where protected
resources can be reached or where data can move**.

---

## 13. Centralized Logging and Detection

Security visibility should span all workload projects.

```text
Production ----+
               |
Non-Production +--> Cloud Audit Logs --> Central Logging
               |                              |
Sandbox -------+                              +--> SCC
                                              |
                                              +--> Monitoring / SIEM
```

Important telemetry classes include:

```text
IAM activity
Administrative activity
Data access
Service activity
Security findings
```

The security team receives centralized visibility without granting application
developers unrestricted security-administration permissions.

---

## 14. Security Control Plane

```text
                    GCP Organization
                           |
           +---------------+---------------+
           |               |               |
           v               v               v
          IAM       Organization Policy   Network/Data
           |               |               |
           +---------------+---------------+
                           |
                           v
                    Cloud Audit Logs
                           |
                           v
                 Central Security Services
                           |
                           +--> Security Command Center
                           |
                           +--> Monitoring / SIEM
                           |
                           v
                      Investigation
```

This creates a layered control plane:

```text
Prevent
  -> Detect
      -> Investigate
          -> Respond
```

---

## 15. End-to-End HLD

```text
                           ENTERPRISE
                              |
                       Corporate Identity
                              |
                    +---------+---------+
                    |                   |
                    v                   v
                 Humans              Workloads
                    |                   |
              Workforce IAM     Workload Identity
                    |                   |
                    +---------+---------+
                              |
                             IAM
                              |
       +----------------------+----------------------+
       |                      |                      |
       v                      v                      v
   Security                Platform               Workloads
       |                      |                      |
       |                      |          +-----------+-----------+
       |                      |          |           |           |
       |                      |          v           v           v
       |                      |      Production  Non-Prod    Sandbox
       |                      |
       +----------------------+----------------------+
                              |
                     Organization Policy
                              |
                              v
                    Enterprise Guardrails
                              |
                              v
                     Network / Data Controls
                              |
                              v
                      Cloud Audit Logs
                              |
                              v
                 Detection / Security Analytics
                              |
                              v
                   Security Command Center
                              |
                              v
                     Investigation / Response
```

---

## 16. Security Properties

| Property | Architecture mechanism |
|---|---|
| Central identity | Corporate IdP / Cloud Identity / federation |
| Group-based authorization | IAM groups |
| Least privilege | Scoped roles |
| Human/workload separation | Workforce vs workload identity |
| Reduced credential exposure | Federation / short-lived credentials |
| Privileged isolation | Dedicated privileged identities |
| Blast-radius reduction | Folder and project boundaries |
| Preventive governance | Organization Policy |
| Environment isolation | Production / Non-Production / Sandbox |
| Data-boundary protection | VPC Service Controls |
| Central visibility | Cloud Audit Logs |
| Threat detection | Security Command Center |
| Investigation | Centralized findings and logs |

---

## 17. Architecture Decision Summary

1. **The organization hierarchy is a security mechanism**, not merely an
   organizational convenience.

2. **Projects represent workload trust boundaries** and should be used to
   separate applications, environments, and sensitive data domains.

3. **Human and workload identities are separate security domains.**

4. **Group-based IAM is preferred** over direct user grants.

5. **Privileged administration is separated from day-to-day engineering.**

6. **Long-lived workload credentials are avoided** in favor of workload
   identity and federation.

7. **Organization Policy provides preventive guardrails** that individual
   project teams should not casually bypass.

8. **Centralized audit telemetry enables enterprise detection and
   investigation.**

9. **Network and data-perimeter controls complement IAM** by limiting
   movement and reachability.

10. **The architecture is designed around blast-radius reduction** so that
    one compromised identity or workload does not become an automatic
    organization-wide compromise.
