# GCP 15 — Enterprise GCP Landing Zone — Threat Model

## 1. Purpose

This threat model evaluates the proposed enterprise GCP landing zone against
realistic cloud attack paths, with particular emphasis on identity compromise,
privilege escalation, workload compromise, and data exfiltration.

The analysis uses:

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

---

## 2. Assets

### Identity assets

```text
Human user identities
Privileged administrator identities
Workload identities
Service accounts
Federated CI/CD identities
Break-glass identities
```

### Control-plane assets

```text
Organization
Folders
Projects
IAM policies
Organization Policies
Security Command Center
Central logging
Audit logs
Network configuration
Service perimeters
```

### Data assets

```text
Production application data
Sensitive datasets
Secrets / keys
Audit records
Security findings
CI/CD configuration
```

---

## 3. Trust Boundaries

```text
                    ORGANIZATION
                         |
          +--------------+--------------+
          |              |              |
       Security       Platform       Workloads
                                      |
                         +------------+------------+
                         |            |            |
                    Production    Non-Prod      Sandbox
```

Additional boundaries exist at:

```text
Folder
Project
Resource
Identity
Network / Service Perimeter
```

The threat model assumes that an attacker may eventually compromise a lower
trust boundary and evaluates whether the architecture prevents lateral
movement into higher-trust boundaries.

---

## 4. Threat Categories

```text
T1  Workforce identity compromise
T2  Privilege escalation
T3  Service-account compromise
T4  CI/CD identity compromise
T5  Credential theft / long-lived credentials
T6  Malicious insider
T7  Cross-project unauthorized access
T8  Data exfiltration
T9  Project / IAM misconfiguration
T10 Logging or detection bypass
T11 Break-glass identity compromise
T12 Sandbox-to-production pivot
```

---

# 5. T1 — Workforce Identity Compromise

## Attack path

```text
Phishing / credential theft
        |
        v
Compromised developer identity
        |
        v
Authenticate to GCP
        |
        v
Attempt unauthorized resource access
```

## Preventive controls

- enterprise workforce identity
- MFA / strong authentication
- group-based authorization
- least-privilege roles
- separation of production and non-production access
- dedicated privileged identities

## Detective controls

- Cloud Audit Logs
- IAM activity monitoring
- Security Command Center
- centralized security analytics

## Blast-radius controls

```text
Compromised developer
       |
       +--> Non-Production
       |
       X--> Production administration
       |
       X--> Organization administration
```

## Residual risk

A compromised user's legitimate permissions remain usable until the identity
is disabled or access is otherwise revoked. Detection latency and insufficient
IAM scoping can therefore still create exposure.

---

# 6. T2 — Privilege Escalation

## Attack path

```text
Low-privilege identity
        |
        v
Find overly broad IAM permission
        |
        v
Modify IAM / service identity / policy
        |
        v
Higher privilege
```

## Preventive controls

- least privilege
- separation of duties
- deny policies where justified
- restricted administrative groups
- resource-scoped permissions
- organization policy guardrails

## Detective controls

```text
IAM policy change
      |
      v
Cloud Audit Logs
      |
      v
Central detection
```

## Blast-radius controls

Administrative authority is distributed across security, network, platform,
and workload functions instead of being concentrated in a single broad
developer role.

## Residual risk

A highly privileged identity that is successfully compromised can still
cause significant enterprise impact. Privileged-access governance therefore
remains a high-risk control area.

---

# 7. T3 — Service-Account Compromise

## Attack path

```text
Application vulnerability
        |
        v
Compromise workload
        |
        v
Obtain workload identity
        |
        v
Use service-account permissions
```

## Preventive controls

- dedicated service identity per workload
- least-privilege IAM
- workload identity
- no shared highly privileged service accounts
- restricted service-account key creation
- resource-scoped access

## Detective controls

- Cloud Audit Logs
- unusual API activity detection
- SCC findings
- centralized security monitoring

## Blast-radius controls

```text
Compromised workload
       |
       v
Its dedicated service identity
       |
       +--> Required resources
       |
       X--> Other application projects
       |
       X--> Security administration
       |
       X--> Organization administration
```

## Residual risk

Any permission legitimately assigned to the compromised service identity can
be abused.

---

# 8. T4 — CI/CD Identity Compromise

## Attack path

```text
Compromise CI/CD system
        |
        v
Steal / impersonate deployment identity
        |
        v
Deploy malicious workload
        |
        v
Obtain workload execution
```

## Preventive controls

- Workload Identity Federation
- short-lived federated credentials
- narrow deployment permissions
- separate CI/CD identity
- environment-specific deployment identities
- production deployment approval controls

## Detective controls

```text
CI/CD authentication
       +
IAM activity
       +
Deployment activity
       |
       v
Central logging / detection
```

## Blast-radius controls

```text
Non-prod CI/CD identity
        X
Production administration
```

Production deployment identities should be scoped separately.

## Residual risk

Compromise of the CI/CD control plane can still be high impact because CI/CD
has legitimate ability to change workloads.

---

# 9. T5 — Credential Theft / Long-Lived Credentials

## Attack path

```text
Service-account key / static credential
        |
        v
Credential theft
        |
        v
Offline attacker access
```

## Preventive controls

- restrict service-account key creation
- prefer Workload Identity
- prefer federation
- use short-lived credentials
- eliminate unnecessary static secrets

## Detective controls

- credential creation and use logging
- abnormal authentication monitoring
- security findings

## Blast-radius controls

Short-lived identities reduce the useful lifetime of compromised credentials,
while workload-specific identities reduce the permission scope.

## Residual risk

Any static credential that remains necessary becomes a potentially
long-lived compromise path and requires additional lifecycle management.

---

# 10. T6 — Malicious Insider

## Attack path

```text
Legitimate employee
        |
        v
Existing authorized access
        |
        v
Intentional misuse
        |
        v
Sensitive resource / data
```

## Preventive controls

- least privilege
- separation of duties
- production access restrictions
- environment segmentation
- privileged identity separation

## Detective controls

- audit logging
- data-access monitoring
- SCC
- centralized security analytics

## Blast-radius controls

A developer should not have unrestricted access across all environments and
security administration.

## Residual risk

Preventive controls cannot completely eliminate misuse by an authorized
principal. Detection, auditability, and rapid response remain essential.

---

# 11. T7 — Cross-Project Unauthorized Access

## Attack path

```text
Compromised identity in Project A
        |
        v
Discover Project B
        |
        v
Attempt resource access
```

## Preventive controls

- project-level trust boundaries
- group-based IAM
- resource-level IAM
- explicit cross-project permissions
- folder separation

## Detective controls

- Cloud Audit Logs
- IAM access monitoring
- SCC / security analytics

## Blast-radius controls

Projects are intentionally separated by application, environment, or data
trust boundary.

## Residual risk

Explicit cross-project grants can create lateral-movement paths and must be
reviewed regularly.

---

# 12. T8 — Data Exfiltration

## Attack path

```text
Compromised identity / workload
        |
        v
Authorized data access
        |
        v
Export / copy / external service
        |
        v
Attacker-controlled destination
```

## Preventive controls

- least-privilege data access
- VPC Service Controls for sensitive data
- controlled egress
- restricted external sharing
- environment isolation

## Detective controls

```text
Data access logs
      |
      v
Security analytics / SCC
      |
      v
Exfiltration finding
```

The previous SCC lab demonstrated this model using a BigQuery-to-Google-Drive
exfiltration detection path.

## Blast-radius controls

Sensitive data should be placed inside dedicated trust boundaries and
protected by network/service-perimeter controls where appropriate.

## Residual risk

An attacker with legitimate read access can sometimes exfiltrate data unless
additional data-loss controls and monitoring are implemented.

---

# 13. T9 — Project / IAM Misconfiguration

## Attack path

```text
Administrator / developer
        |
        v
Incorrect IAM or resource configuration
        |
        v
Overexposed resource
```

## Preventive controls

- organization policies
- standardized project creation
- infrastructure-as-code
- separation of duties
- least privilege
- policy review

## Detective controls

- Security Command Center posture findings
- Cloud Audit Logs
- policy analysis tools
- continuous security monitoring

## Blast-radius controls

Central guardrails prevent individual projects from freely violating
enterprise security requirements.

## Residual risk

Configuration drift and newly introduced services can create gaps that
require continuous review.

---

# 14. T10 — Logging / Detection Bypass

## Attack path

```text
Attacker compromises privileged identity
        |
        v
Attempts to disable / evade logging
        |
        v
Reduced forensic visibility
```

## Preventive controls

- centralized logging administration
- separate security administration
- organization-level governance
- restricted modification rights

## Detective controls

- monitor logging configuration changes
- audit logging administration
- alert on security-control changes

## Blast-radius controls

Application teams should not independently control enterprise-wide security
logging.

## Residual risk

A sufficiently privileged attacker may still interfere with some security
controls. Independent security administration and centralized telemetry reduce
this risk.

---

# 15. T11 — Break-Glass Identity Compromise

## Attack path

```text
Break-glass credential theft
        |
        v
Emergency administrative access
        |
        v
Organization-wide control
```

## Preventive controls

- separate emergency identity
- strong authentication
- minimal membership
- secure credential storage
- documented emergency procedures

## Detective controls

- mandatory audit logging
- alerts for break-glass usage
- periodic access review

## Blast-radius controls

Break-glass identities are kept separate from ordinary identities and are not
used for daily operations.

## Residual risk

By design, break-glass access is highly privileged. Its compromise is a
high-severity event.

---

# 16. T12 — Sandbox-to-Production Pivot

## Attack path

```text
Compromise sandbox
       |
       v
Discover production identities/resources
       |
       v
Lateral movement
       |
       v
Production compromise
```

## Preventive controls

- separate Sandbox folder
- explicit IAM boundaries
- no implicit production access
- separate service identities
- network/data segmentation

## Detective controls

- cross-project API activity monitoring
- IAM access logs
- centralized security analytics

## Blast-radius controls

Sandbox is intentionally treated as the lowest-trust environment.

## Residual risk

Shared identities, secrets, or infrastructure can weaken environment
separation and must be avoided.

---

# 17. Threat-to-Control Matrix

| Threat | Preventive controls | Detective controls | Blast-radius control |
|---|---|---|---|
| Workforce compromise | MFA, least privilege, groups | Audit Logs, SCC | Environment/project isolation |
| Privilege escalation | SoD, deny controls, scoped IAM | IAM audit | Separate admin identities |
| Service-account compromise | Workload Identity, scoped roles | API/activity logs | Dedicated service identity |
| CI/CD compromise | WIF, scoped deployment roles | CI/CD + IAM logs | Environment-specific identities |
| Credential theft | No long-lived keys, federation | Auth/key activity | Short-lived credentials |
| Insider threat | Least privilege, SoD | Audit/data access logs | Environment boundaries |
| Cross-project access | Explicit grants, project boundaries | Access logs | Project trust boundaries |
| Data exfiltration | VPC-SC, egress/sharing controls | SCC + audit logs | Data trust boundaries |
| Misconfiguration | Org Policy, standardized provisioning | SCC posture findings | Central guardrails |
| Detection bypass | Restricted security admin | Logging-change alerts | Separate security plane |
| Break-glass compromise | Separate identity, MFA | Usage alerts | Dedicated emergency account |
| Sandbox pivot | Folder/IAM/network isolation | Cross-project monitoring | Sandbox boundary |

---

# 18. Attack Trees

## Identity compromise attack tree

```text
                 Enterprise compromise
                         |
              +----------+----------+
              |                     |
       Workforce identity     Workload identity
              |                     |
        Credential theft       Application exploit
              |                     |
              v                     v
         IAM access          Service identity
              |                     |
              +----------+----------+
                         |
                         v
                Privilege expansion
                         |
                         v
                 Sensitive resources
```

The architecture attempts to break this chain at multiple points:

```text
Strong identity
   +
Least privilege
   +
Trust boundaries
   +
Guardrails
   +
Detection
```

---

## Data exfiltration attack tree

```text
                Protected data
                     |
             Unauthorized read
                     |
          +----------+----------+
          |                     |
       User identity        Workload identity
          |                     |
          +----------+----------+
                     |
                     v
                Data export
                     |
          +----------+----------+
          |                     |
     Cloud service       External destination
          |                     |
          +----------+----------+
                     |
                     v
                  Exfil
```

Controls attempt to interrupt the path using:

```text
IAM
  +
VPC Service Controls
  +
Egress restrictions
  +
Audit logging
  +
SCC / detection
```

---

# 19. Residual Risk Summary

The architecture significantly reduces common cloud attack paths, but does
not eliminate risk.

### Highest residual-risk areas

**Privileged identity compromise**

A compromised organization or security administrator can still have broad
control.

**Authorized data access**

An attacker operating through a legitimate identity may be able to access
and export data that the identity is intentionally authorized to read.

**CI/CD compromise**

A compromised delivery pipeline can deploy malicious code using legitimate
deployment permissions.

**Configuration drift**

Security posture can degrade over time as projects, IAM bindings, services,
and exceptions change.

**Detection latency**

Detective controls reduce time to identify and respond; they do not prevent
every unauthorized action.

---

# 20. Security Assumptions

The design assumes:

1. The enterprise identity provider is itself adequately protected.
2. MFA is enforced for privileged human identities.
3. Service identities are not broadly shared.
4. Security administration is separated from normal application teams.
5. Organization policies are centrally governed.
6. Audit logs are retained according to enterprise requirements.
7. Production and non-production trust boundaries are maintained.
8. Exceptions to security controls require explicit review.

---

# 21. Threat Model Conclusion

The core security strategy is:

```text
Reduce attack surface
        +
Reduce privileges
        +
Separate trust boundaries
        +
Prevent dangerous configurations
        +
Detect suspicious activity
        +
Limit blast radius
        +
Maintain forensic visibility
```

The landing zone is therefore not dependent on a single security product.

Security emerges from the interaction of:

```text
Identity
   +
IAM
   +
Organization Policy
   +
Network/Data Boundaries
   +
Audit Logging
   +
Security Detection
   +
Operational Governance
```

The target outcome is:

> A compromised user, workload, service identity, or lower-trust project should
> not automatically become an organization-wide compromise.

---

# 22. Architecture Gate Assessment

| Area | Status |
|---|---|
| Organization hierarchy | Designed |
| Trust boundaries | Designed |
| Human identity model | Designed |
| Workload identity model | Designed |
| IAM model | Designed |
| Privileged access model | Designed |
| Organization guardrails | Designed |
| Network/data security model | Designed |
| Centralized logging | Designed |
| Detection architecture | Designed |
| Threat model | Complete |
| HLD | Complete |
