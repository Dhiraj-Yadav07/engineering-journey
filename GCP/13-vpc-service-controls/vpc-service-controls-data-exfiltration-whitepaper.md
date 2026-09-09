# Whitepaper: VPC Service Controls and Data Exfiltration

## GCP Security Study

**Focus:** VPC Service Controls and data exfiltration scenarios  
**Type:** Study / Threat Modeling  
**Primary case study:** Commerzbank's use of Google Cloud VPC Service Controls  
**Primary deliverable:** Threat-scenario analysis

---

## Executive Summary

Cloud security has a critical distinction between **controlling access to data** and **controlling where data can move**.

Google Cloud IAM answers questions such as:

> Which identity is allowed to perform this operation?

VPC Service Controls adds a separate security boundary around supported Google Cloud services and resources:

> Can this access or data movement cross the organization's protected boundary?

This distinction becomes especially important when an attacker compromises an application or obtains valid credentials. A stolen identity may still possess legitimate IAM permissions. VPC Service Controls provides an additional perimeter-based control that can help reduce the ability to use those permissions to move data to unauthorized Google Cloud resources or across protected boundaries.

Google documents VPC Service Controls as an additional layer independent of IAM and recommends using both together for defense in depth. It can create service perimeters around supported Google-managed services and control cross-perimeter communication through ingress and egress rules.

This whitepaper examines the problem through a real-world financial-services example: **Commerzbank's adoption of VPC Service Controls**. Commerzbank described its objective as controlling data flow and preventing both **data exfiltration** and **lateral data movement** as its Google Cloud estate increasingly relied on API-based communication.

---

# 1. The Fundamental Security Problem

Imagine an organization stores sensitive customer information in BigQuery:

```text
                   Sensitive Data
                         |
                         v
                +------------------+
                |     BigQuery     |
                |                  |
                | Customer Data    |
                +------------------+
```

An IAM policy may correctly grant a service account read access:

```text
analytics-sa
    |
    +--> BigQuery Data Viewer
```

From an IAM perspective:

```text
analytics-sa --> READ DATA = ALLOWED
```

But a security team must also ask:

```text
Where can that data go after it is read?
```

For example:

```text
BigQuery
   |
   | copy sensitive data
   v
Unauthorized project
   |
   v
External environment
```

The identity may be valid.

The IAM permission may be valid.

The **destination may still be unauthorized**.

This is the data-exfiltration problem.

---

# 2. IAM vs VPC Service Controls

The simplest mental model is:

```text
                  SECURITY DECISION
                         |
              +----------+----------+
              |                     |
              v                     v
             IAM                  VPC-SC
              |                     |
       Who can perform        Can the request/data
       the operation?         cross the boundary?
              |                     |
              +----------+----------+
                         |
                         v
                    Final access
```

### IAM

IAM is primarily an **identity and authorization control**.

It answers:

```text
Who?
What action?
On which resource?
```

Example:

```text
caller-sa
   |
   +--> bigquery.tables.getData
   |
   +--> sensitive-dataset
```

### VPC Service Controls

VPC Service Controls provides a **service-perimeter boundary** for supported Google Cloud services.

It helps answer:

```text
Where is this resource allowed to be accessed from?
Where can data move?
Can this API request cross a protected boundary?
```

Google explicitly describes VPC Service Controls as independent of IAM and recommends using both controls together.

---

# 3. What Is a VPC Service Controls Perimeter?

A service perimeter creates a logical security boundary around selected Google Cloud resources.

Conceptually:

```text
              VPC SERVICE PERIMETER

        +--------------------------------+
        |                                |
        |  BigQuery                      |
        |  Cloud Storage                 |
        |  Other supported services      |
        |                                |
        +--------------------------------+
                     |
                     X
                     |
          Unauthorized crossing
```

Within a perimeter, supported resources can communicate according to applicable policies. Communication across the perimeter is restricted unless an allowed path is explicitly configured.

VPC Service Controls can protect supported services such as Cloud Storage and BigQuery, with ingress and egress rules controlling approved cross-perimeter data exchange.

---

# 4. Why This Matters in a Cloud Environment

Traditional on-premises security often relies heavily on network segmentation:

```text
           Traditional data center

+----------+     firewall     +----------+
| Server A | ---------------- | Server B |
+----------+                  +----------+
```

Security teams can reason about:

```text
IP address
port
protocol
network zone
firewall rule
```

Cloud-native systems often rely much more heavily on managed services and APIs:

```text
Cloud Run
    |
    v
BigQuery
    |
    v
Cloud Storage
    |
    v
Pub/Sub
```

The communication may not resemble traditional server-to-server traffic.

Commerzbank reported that more than 90% of its BDAA Google Cloud use cases used API-only communication. The organization concluded that traditional firewall rules could not provide sufficient protection for this API-centric threat model, increasing the importance of controlling identity, API access, and data flow.

This is one reason VPC Service Controls becomes useful.

---

# 5. Real-World Case Study: Commerzbank

Commerzbank is a major European financial institution with substantial regulatory and data-protection requirements.

Its Google Cloud security architecture evolved as more applications and data-processing workloads moved to Google Cloud. The bank described a growing need to control **where data flows**, not merely who has access.

Their security requirements included:

- controlling unauthorized data movement
- reducing data-exfiltration risk
- supporting a Zero Trust approach
- providing contextual access controls
- separating applications and software stages
- maintaining monitoring and logging
- scaling security controls through automation

Commerzbank selected VPC Service Controls as a foundational control for this problem and described it as functioning like a firewall for Google Cloud APIs.

---

# 6. Commerzbank's Data Flow Boundary Model

A particularly useful design concept from the case study is the idea of **Data Flow Boundaries**.

Commerzbank described three main boundary types:

```text
                     ORGANIZATION
                          |
          +---------------+---------------+
          |               |               |
     Application A   Application B   Application C
          |
       +--+-------------+
       |                |
   Production       Development
       |
      Stage
```

## 6.1 Organization Boundary

The organization wants to prevent protected data from crossing into unauthorized organizations or external environments.

```text
+-----------------------------------------+
|          Organization Perimeter         |
|                                         |
|   Sensitive Cloud Resources             |
|                                         |
+--------------------X--------------------+
                     |
              unauthorized
                destination
```

## 6.2 Application Boundary

Two applications may belong to the same organization but still represent different trust domains.

```text
+------------------+      +------------------+
| Application A    |  X   | Application B    |
|                  |      |                  |
| Sensitive Data   |      | Different trust |
+------------------+      +------------------+
```

The objective is to prevent unauthorized lateral movement.

## 6.3 Software-Stage Boundary

Production, testing, and development may have very different trust levels.

A common security requirement is:

```text
Production Data
      |
      X
      |
Development Environment
```

Development environments should not automatically receive production data.

Commerzbank explicitly described its Data Flow Boundaries as protecting data at organization, application, and software-stage levels.

---

# 7. Threat Scenario 1 — Stolen Service Account Credentials

## Scenario

An attacker obtains credentials associated with a service account:

```text
Attacker
   |
   v
Compromised credentials
   |
   v
service-account
   |
   v
Sensitive BigQuery
```

IAM may recognize the service account as legitimate.

If the account has:

```text
BigQuery Data Viewer
```

then the attacker may be able to perform legitimate data reads.

## Risk

```text
Credential compromise
        |
        v
Valid IAM identity
        |
        v
Sensitive data access
        |
        v
Exfiltration attempt
```

This is dangerous because the request may look legitimate from an identity perspective.

## VPC-SC Mitigation

VPC Service Controls can add another condition around access and data movement. For example, organizations can restrict protected access to authorized networks or contexts and limit cross-perimeter resource access.

Google specifically identifies protection against stolen OAuth or service-account credentials as one of the security benefits of VPC Service Controls.

---

# 8. Threat Scenario 2 — Compromised Workload

## Scenario

Suppose a Cloud Run application has access to sensitive BigQuery data:

```text
+----------------------+
| Cloud Run Application|
+----------+-----------+
           |
           v
      analytics-sa
           |
           v
       BigQuery
```

An attacker compromises the application:

```text
                    Attacker
                       |
                       v
              Compromised application
                       |
                       v
                  analytics-sa
                       |
                       v
              Sensitive BigQuery
```

The attacker attempts:

```text
Sensitive BigQuery
       |
       | read
       v
Sensitive data
       |
       | copy
       v
Unauthorized project
```

## Risk

The attacker is abusing a legitimate application's identity rather than creating an obviously malicious identity.

## VPC-SC Mitigation

A VPC Service Controls perimeter can prevent unauthorized data movement across the protected boundary when the attempted destination or access path is not permitted.

Google documents that VPC Service Controls can prevent data from being copied to unauthorized resources outside a service perimeter through service operations such as Cloud Storage copy operations or BigQuery table creation/copy operations.

---

# 9. Threat Scenario 3 — Cross-Project Data Exfiltration

Consider:

```text
Project A
+-----------------------+
| Sensitive BigQuery    |
+-----------+-----------+
            |
            | data copy
            v
Project B
+-----------------------+
| Unauthorized bucket   |
+-----------------------+
```

Without an appropriate perimeter:

```text
Sensitive Data
      |
      v
Unauthorized project
```

With VPC Service Controls:

```text
+---------------------------+
|       PERIMETER            |
|                           |
| Sensitive Project         |
| BigQuery                  |
|                           |
+-------------X-------------+
              |
        Cross-perimeter
        data movement
```

The request can be denied unless a valid ingress/egress path is configured.

---

# 10. Threat Scenario 4 — Lateral Data Movement

Data exfiltration is not limited to leaving the company.

Suppose:

```text
Application A
    |
    | sensitive data
    v
Application B
```

Both applications belong to the same organization.

That does not necessarily mean Application B should receive Application A's sensitive data.

This is **lateral data movement**.

## Risk

A compromised or overly privileged application could move sensitive information into another internal application or environment.

## Solution

Use separate service perimeters/data-flow boundaries and explicitly permit required data exchanges.

```text
Application A Perimeter
          |
          X
          |
Application B Perimeter
```

Then define only the approved exchange path.

---

# 11. Threat Scenario 5 — Production-to-Development Data Exposure

## Scenario

A team wants to use real production data in development.

```text
Production
   |
   | sensitive customer data
   v
Development
```

This may be operationally convenient but creates security and compliance risk.

## Risk

Development environments commonly have:

- more users
- more debugging tools
- lower security hardening
- broader access
- more third-party dependencies

Therefore:

```text
Production data
       +
Lower-trust environment
       =
Higher exposure risk
```

## Solution

Create trust boundaries between stages.

```text
+-------------------+       X       +--------------------+
| Production        |               | Development        |
|                   |               |                    |
| Sensitive data    |               | Lower trust        |
+-------------------+               +--------------------+
```

Where a legitimate pipeline needs data movement, explicitly authorize that path rather than assuming all internal environments are trusted equally.

---

# 12. Threat Scenario 6 — Malicious Insider

## Scenario

An employee has legitimate access to sensitive data.

```text
Employee
    |
    v
Valid corporate identity
    |
    v
BigQuery
    |
    v
Sensitive data
```

The employee attempts to move the data outside the approved environment.

## Why IAM Alone May Be Insufficient

IAM may correctly say:

```text
Employee --> READ = ALLOWED
```

The security question is different:

```text
Employee --> MOVE DATA OUTSIDE PERIMETER = ?
```

VPC Service Controls adds a data-boundary layer intended to help mitigate unauthorized cross-perimeter movement.

---

# 13. Ingress and Egress

These two concepts are central to VPC Service Controls.

## Ingress

Ingress means access **from outside the perimeter into protected resources**.

```text
Outside
   |
   | ingress
   v
+-------------------+
| Protected         |
| Perimeter         |
|                   |
| BigQuery          |
+-------------------+
```

Ingress rules can define who or what is allowed to cross into the perimeter.

## Egress

Egress means access **from protected resources toward resources outside the perimeter**.

```text
+-------------------+
| Protected         |
| Perimeter         |
|                   |
| BigQuery          |
+---------+---------+
          |
          | egress
          v
       Outside
```

Egress rules can be used to explicitly allow legitimate cross-perimeter communication.

---

# 14. Zero Trust Interpretation

A Zero Trust architecture does not assume:

```text
"Internal = trusted"
```

Instead it evaluates contextual properties of a request.

Conceptually:

```text
                     Request
                        |
       +----------------+----------------+
       |                |                |
       v                v                v
    Identity          Action          Context
       |                |                |
       +----------------+----------------+
                        |
                        v
              Security policy decision
```

VPC Service Controls can incorporate context such as:

- identity
- identity type
- network origin
- VPC network
- device information through supported access-level mechanisms
- direction of access
- protected resource
- service/API

---

# 15. VPC-SC as a Data-Flow Control

A useful abstraction is:

```text
             Data Plane

    +-----------------------+
    | Sensitive Resources   |
    |                       |
    | BigQuery              |
    | Cloud Storage         |
    | Other supported APIs  |
    +-----------+-----------+
                |
         VPC-SC boundary
                |
        +-------+-------+
        |               |
      ALLOW            DENY
        |               |
        v               X
 Approved resource   Unauthorized
 or workload         destination
```

The perimeter is not simply another IAM role.

It is an additional **boundary condition** on access and data movement.

---

# 16. What VPC Service Controls Does Not Replace

VPC Service Controls should not be treated as a replacement for IAM.

### It does not answer:

```text
Should this user have BigQuery access?
```

IAM handles that.

### It does not replace application security.

If an application has a vulnerability, that remains an application-security problem.

### It is not a generic internet firewall.

A service perimeter controls Google-managed services and resources within its scope; it does not automatically block arbitrary third-party internet APIs.

### It does not provide comprehensive metadata protection.

VPC Service Controls is primarily focused on controlling the movement of **data/content**, not comprehensive enforcement over all metadata movement. IAM remains important for metadata access control.

---

# 17. Defense-in-Depth Model

A mature architecture combines multiple security controls:

```text
                  Request
                     |
        +------------+------------+
        |                         |
        v                         v
       IAM                      VPC-SC
        |                         |
  Identity & action         Data boundary &
      permission            context control
        |                         |
        +------------+------------+
                     |
                     v
              Security decision
```

Additional controls may include:

```text
IAM
+
VPC Service Controls
+
Network egress controls
+
MFA
+
Organization policies
+
Logging / monitoring
+
Security Command Center
+
Application security
```

The important design principle is defense in depth rather than attempting to make one control solve every security problem.

---

# 18. Enterprise Architecture Pattern

A simplified enterprise design could look like:

```text
                      Organization
                           |
          +----------------+----------------+
          |                                 |
          v                                 v
    Application Boundary A             Application B
          |                                 |
      +---+---+                         +---+---+
      |       |                         |       |
      v       v                         v       v
    Prod     Data                     Prod     Data
      |                                         |
      +------------------X----------------------+
                         |
                  unauthorized
                 lateral movement

             Outer Organization Boundary
           +-------------------------------+
           | Trusted Google Cloud Estate   |
           |                               |
           | Perimeters / Data Boundaries  |
           +-------------------------------+
```

The design allows organizations to create trust boundaries that reflect the actual business architecture rather than treating the entire cloud environment as one trust domain.

Commerzbank's three-level Data Flow Boundary model is a concrete example of this principle.

---

# 19. Risk-to-Control Matrix

| Threat | Example | Primary Risk | VPC-SC Contribution |
|---|---|---|---|
| Stolen credentials | Compromised service account reads data | Data theft | Restrict context and cross-perimeter access |
| Compromised workload | Cloud Run code exports BigQuery data | Exfiltration | Restrict unauthorized destinations |
| Malicious insider | User copies sensitive data | Data loss | Control cross-perimeter movement |
| Cross-project copy | BigQuery → unauthorized bucket | Data exfiltration | Perimeter enforcement |
| Lateral movement | App A → App B | Internal data exposure | Separate application boundaries |
| Prod → Dev | Production data enters test project | Sensitive-data exposure | Stage-level boundaries |
| Excessive IAM | Wrong identity has access | Unauthorized access | **Primarily IAM problem** |
| Vulnerable app | RCE or application flaw | Initial compromise | **Application-security problem** |
| Internet SaaS upload | Data sent directly to arbitrary third-party API | External exfiltration | **Not automatically blocked by VPC-SC** |

---

# 20. Security Decision Flow

A useful mental model for evaluating a request is:

```text
                  Request
                     |
                     v
            +----------------+
            | Authenticate   |
            +-------+--------+
                    |
                    v
            +----------------+
            | IAM authorize  |
            +-------+--------+
                    |
              IAM allowed?
               /       \
             NO         YES
             |           |
           DENY          v
                  +-------------+
                  | VPC-SC      |
                  | perimeter   |
                  | evaluation  |
                  +------+------+
                         |
                   Allowed path?
                    /        \
                  NO          YES
                  |            |
                DENY           v
                         Access allowed
```

This is a conceptual security model. Actual enforcement depends on the Google Cloud service, request path, perimeter configuration, and supported VPC Service Controls behavior.

---

# 21. Commerzbank — Why the Case Matters

The Commerzbank case is useful because it illustrates a mature cloud-security problem:

```text
Cloud adoption
      |
      v
More APIs and managed services
      |
      v
Traditional network controls become less sufficient
      |
      v
Identity becomes more important
      |
      v
But identity alone does not control data movement
      |
      v
Need for data-flow boundaries
      |
      v
VPC Service Controls
```

Commerzbank described VPC Service Controls as meeting requirements around data-flow control, cloud-first operation, regulatory/security requirements, Zero Trust context awareness, hierarchical administration, and monitoring/logging. Its deployment was described as fully automated and operating within a Zero Trust framework.

---

# 22. Design Principles

### Principle 1 — Treat data movement as a security event

Do not evaluate only:

```text
Who accessed the data?
```

Also evaluate:

```text
Where did the data go?
```

### Principle 2 — Separate trust domains

Useful boundaries can exist between:

```text
Organization
Application
Environment
Software stage
```

### Principle 3 — Use IAM and VPC-SC together

IAM controls identity and authorization.

VPC-SC adds perimeter and context controls.

### Principle 4 — Make exceptions explicit

Avoid broad cross-perimeter trust.

Prefer tightly scoped ingress and egress paths for legitimate data exchange.

### Principle 5 — Design for compromised credentials

Assume credentials can eventually be stolen.

A strong architecture should reduce the damage caused by valid credentials being abused from an unauthorized context.

---

# 23. Key Takeaways

The most important lessons from this study are:

```text
IAM
  = Who can do what?

VPC Service Controls
  = Where can protected Google Cloud data/API access flow?

Ingress
  = Outside -> Protected perimeter

Egress
  = Protected perimeter -> Outside

Service perimeter
  = Logical trust boundary around supported Google Cloud resources

Data exfiltration
  = Data leaves the intended trust boundary

Lateral movement
  = Data moves between internal trust domains without authorization
```

The overarching design principle is:

```text
                Identity Security
                      |
                     IAM
                      |
                      v
             "Who can access?"
                      |
                      +
                      |
               Data Boundary
                      |
                   VPC-SC
                      |
                      v
          "Where can data move?"
```

---

# 24. Final Security Model

A mature cloud-security architecture should therefore look conceptually like:

```text
                         +---------------------+
                         |       Request       |
                         +----------+----------+
                                    |
                       +------------+------------+
                       |                         |
                       v                         v
                 Identity Plane              Data Plane
                       |                         |
                      IAM                     VPC-SC
                       |                         |
              Who can do what?           Where can it move?
                       |                         |
                       +------------+------------+
                                    |
                                    v
                              Final decision
                                    |
                         +----------+----------+
                         |                     |
                       ALLOW                 DENY
```

This is the core lesson from VPC Service Controls and the Commerzbank case: **cloud security must protect not only access to data, but also the boundaries across which sensitive data is permitted to move.**

---

## References

1. Google Cloud, **Overview of VPC Service Controls** — service perimeters, data-exfiltration protection, ingress/egress, access levels, IAM relationship, and limitations.  
   https://docs.cloud.google.com/vpc-service-controls/docs/overview

2. Google Cloud Blog, **How Commerzbank safeguards its data with VPC Service Controls** — real-world enterprise case study, API-centric threat model, data-flow boundaries, Zero Trust, and automation.  
   https://cloud.google.com/blog/topics/customers/how-commerzbank-safeguards-its-data-with-vpc-service-controls

3. Google Cloud, **VPC Service Controls product page** — current positioning, use cases, and data-boundary capabilities.  
   https://cloud.google.com/security/vpc-service-controls
