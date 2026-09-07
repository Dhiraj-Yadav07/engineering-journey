# GCP Security — Workload Identity Federation
## Identity Architecture Note: GitHub Actions → GCP Cloud Storage (Direct WIF)

**Focus:** GCP Security  
**Task:** Study Workload Identity and Workload Identity Federation  
**Deliverable:** Identity architecture note  
**Implementation:** GitHub Actions → Google Cloud Workload Identity Federation → Cloud Storage  
**Federation model:** **Direct Workload Identity Federation**  
**Service-account impersonation:** **Not used**

---

## 1. Executive Summary

This lab demonstrates how a GitHub Actions workload can access a Google Cloud resource without storing a long-lived Google Cloud service-account key in GitHub.

The workload uses the following identity path:

```text
GitHub Actions
      |
      | GitHub OIDC token
      v
Google Workload Identity Federation
      |
      | validate issuer
      | map claims
      | evaluate trust condition
      v
Federated principal
      |
      | IAM role directly on resource
      v
Cloud Storage bucket
```

The lab uses **Direct Workload Identity Federation**. The federated GitHub identity is granted an IAM role directly on the Cloud Storage bucket. There is no intermediate Google Cloud service account and no service-account impersonation.

Google currently recommends direct resource access for federated workloads where the target Google Cloud resource supports it. Cloud Storage is a supported example. Some Google Cloud services have federation limitations; those cases are outside the scope of this lab.

---

## 2. Problem Statement

### Traditional key-based design

A common but weaker pattern is:

```text
GitHub Actions
      |
      | stored JSON private key
      v
Google Cloud Service Account
      |
      v
Cloud Storage
```

The private key becomes a long-lived credential that must be stored, protected, rotated, and revoked.

### Lab design

Instead:

```text
GitHub Actions
      |
      | GitHub-issued OIDC token
      v
Google WIF Provider
      |
      | short-lived federated credential
      v
Federated principal
      |
      | direct IAM authorization
      v
Cloud Storage
```

This removes the need to distribute a static Google private key.

---

## 3. Architecture

### 3.1 High-Level Architecture

```text
                         GITHUB
+-----------------------------------------------------+
|                                                     |
|  Repository: Dhiraj-Yadav07/engineering-journey    |
|                                                     |
|  GitHub Actions workflow                            |
|        |                                            |
|        | OIDC token                                 |
|        v                                            |
|  GitHub OIDC Issuer                                 |
|  https://token.actions.githubusercontent.com/       |
+--------------------------+--------------------------+
                           |
                           | signed OIDC JWT
                           v
+-----------------------------------------------------+
|                  GOOGLE CLOUD                       |
|                                                     |
|  Project: dev-project-506017                       |
|  Project number: 229836775022                      |
|                                                     |
|  Workload Identity Pool                            |
|      github-wif-lab                                |
|             |                                       |
|             v                                       |
|      OIDC Provider                                  |
|          github-oidc                                |
|             |                                       |
|             +-- issuer validation                  |
|             +-- attribute mapping                  |
|             +-- attribute condition                |
|             |                                      |
|             v                                      |
|      Google Security Token Service                 |
|             |                                      |
|             | short-lived federated credential     |
|             v                                      |
|      Federated principal                           |
|             |                                      |
|             | roles/storage.objectViewer            |
|             v                                      |
|      Cloud Storage                                 |
|      gs://dev-project-506017-github-wif-11878      |
|             |                                      |
|             v                                      |
|      wif-test.txt                                  |
+-----------------------------------------------------+
```

---

## 4. Authentication vs Authorization

These are separate security decisions.

### Authentication

Authentication establishes:

> Which external workload is this?

In this lab, the workload is represented by GitHub's OIDC token.

```text
GitHub Actions
      |
      v
GitHub OIDC token
      |
      v
WIF Provider
```

### Authorization

Authorization establishes:

> What is this workload allowed to do?

IAM grants the federated principal:

```text
roles/storage.objectViewer
```

on the specific Cloud Storage bucket.

Therefore:

```text
Federation
    =
authentication / trust

IAM
    =
authorization
```

This distinction is fundamental to workload federation.

---

## 5. Workload Identity Federation Components

### 5.1 Workload Identity Pool

The pool is the Google Cloud container for external workload identities.

This lab uses:

```text
github-wif-lab
```

Canonical resource:

```text
projects/229836775022/locations/global/workloadIdentityPools/github-wif-lab
```

The pool itself does not grant Cloud Storage permissions.

---

### 5.2 Workload Identity Provider

The provider establishes trust with GitHub's OIDC issuer.

This lab uses:

```text
github-oidc
```

Issuer:

```text
https://token.actions.githubusercontent.com/
```

Canonical provider resource:

```text
projects/229836775022/locations/global/workloadIdentityPools/github-wif-lab/providers/github-oidc
```

---

## 6. Attribute Mapping

The provider maps GitHub OIDC claims into Google-recognized attributes.

Implemented mappings:

```text
google.subject                = assertion.sub
attribute.repository_id       = assertion.repository_id
attribute.repository_owner_id = assertion.repository_owner_id
attribute.repository          = assertion.repository
```

Conceptually:

```text
GitHub OIDC JWT
       |
       +-- sub
       +-- repository
       +-- repository_id
       +-- repository_owner_id
       |
       v
Google mapped attributes
```

### Why `google.subject`?

`google.subject` provides the canonical federated subject used by Google IAM identity principals.

### Why repository IDs?

This lab uses:

```text
repository_id       = 1336061111
repository_owner_id = 146002674
```

rather than relying only on mutable repository/owner names.

GitHub documents repository and owner IDs among the claims available in GitHub Actions OIDC tokens.

---

## 7. Attribute Condition

The provider is restricted using:

```text
attribute.repository_owner_id == '146002674'
&&
attribute.repository_id == '1336061111'
```

This means the provider trusts only the intended GitHub repository identity.

Conceptually:

```text
Incoming GitHub token
        |
        +-- owner ID matches?      YES
        |
        +-- repository ID matches? YES
        |
        v
     ACCEPT
```

Otherwise:

```text
       DENY
```

This is important because GitHub's OIDC issuer is shared across many repositories and organizations. Issuer validation alone would establish too broad a trust boundary.

---

## 8. Direct Resource Access

This lab intentionally uses direct resource access.

The federated identity is granted:

```text
roles/storage.objectViewer
```

directly on:

```text
gs://dev-project-506017-github-wif-11878
```

The principal-set binding is:

```text
principalSet://iam.googleapis.com/projects/229836775022/locations/global/workloadIdentityPools/github-wif-lab/attribute.repository_id/1336061111
```

Resulting authorization model:

```text
Federated GitHub identity
        |
        | roles/storage.objectViewer
        v
Specific Cloud Storage bucket
```

There is no intermediate service account.

---

## 9. Why Direct WIF?

Direct WIF simplifies the identity path:

```text
GitHub
  ↓
OIDC
  ↓
WIF
  ↓
Federated principal
  ↓
Resource IAM
```

There is no additional service-account identity or impersonation relationship.

This is appropriate for a resource that supports direct federation and keeps the lab focused on the core WIF architecture.

### Trade-off

Direct federation is not universally supported by every Google Cloud API or every API method.

Where a target API has a federation limitation, another architecture may be required. That limitation is intentionally out of scope for this lab.

---

## 10. GitHub Actions Workflow

The implemented workflow is:

```yaml
name: GCP Workload Identity Federation Test

on:
  workflow_dispatch:

permissions:
  contents: read
  id-token: write

jobs:
  test-gcp-wif:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout repository
        uses: actions/checkout@v7

      - name: Authenticate to Google Cloud with WIF
        uses: google-github-actions/auth@v3
        with:
          workload_identity_provider: "projects/229836775022/locations/global/workloadIdentityPools/github-wif-lab/providers/github-oidc"

      - name: Verify federated identity
        run: |
          gcloud auth list

      - name: Read test object from Cloud Storage
        run: |
          gcloud storage cat gs://dev-project-506017-github-wif-11878/wif-test.txt
```

### Important observation

There is deliberately no:

```yaml
service_account:
```

field.

When `service_account` is omitted, the Google GitHub Actions authentication action uses Direct Workload Identity Federation.

---

## 11. GitHub OIDC Permission

The workflow includes:

```yaml
permissions:
  contents: read
  id-token: write
```

`id-token: write` allows the workflow to request a GitHub OIDC token.

It does not itself grant access to Google Cloud.

The final authorization decision still happens in Google Cloud through:

```text
WIF provider trust condition
+
IAM resource policy
```

This separation is important:

```text
GitHub permission
    ↓
Can request OIDC token

GCP WIF
    ↓
Can this GitHub identity federate?

GCP IAM
    ↓
What can that federated identity access?
```

---

## 12. End-to-End Token Flow

The practical request flow is:

```text
1. GitHub Actions starts
        |
        v
2. Workflow requests GitHub OIDC token
        |
        v
3. GitHub issues signed JWT
        |
        v
4. google-github-actions/auth sends the token
   to Google Cloud Workload Identity Federation
        |
        v
5. WIF provider validates:
   - issuer
   - OIDC token
   - mapped claims
   - attribute condition
        |
        v
6. Google Security Token Service
   exchanges the external credential
        |
        v
7. Short-lived federated credential
        |
        v
8. Federated principal is evaluated by IAM
        |
        v
9. Cloud Storage checks bucket IAM policy
        |
        v
10. roles/storage.objectViewer allows read
        |
        v
11. wif-test.txt is returned
```

The key security principle is:

```text
External identity
      +
Explicit trust boundary
      +
Short-lived credential
      +
Least-privilege IAM
      =
Keyless workload access
```

---

## 13. Implemented Lab Configuration

| Component | Value |
|---|---|
| GitHub repository | `Dhiraj-Yadav07/engineering-journey` |
| GitHub repository ID | `1336061111` |
| GitHub owner ID | `146002674` |
| GCP project ID | `dev-project-506017` |
| GCP project number | `229836775022` |
| WIF pool | `github-wif-lab` |
| WIF provider | `github-oidc` |
| OIDC issuer | `https://token.actions.githubusercontent.com/` |
| Cloud Storage bucket | `gs://dev-project-506017-github-wif-11878` |
| Test object | `wif-test.txt` |
| IAM role | `roles/storage.objectViewer` |
| Federation model | Direct WIF |
| Service account | Not used |
| Service-account key | Not used |
| Service-account impersonation | Not used |

---

## 14. Evidence

### GCP-side evidence

Successfully created:

```text
Workload Identity Pool
github-wif-lab
ACTIVE
```

```text
OIDC Provider
github-oidc
ACTIVE
```

Provider condition:

```text
attribute.repository_owner_id == '146002674'
&&
attribute.repository_id == '1336061111'
```

Bucket IAM binding:

```text
principalSet://iam.googleapis.com/projects/229836775022/locations/global/workloadIdentityPools/github-wif-lab/attribute.repository_id/1336061111
    |
    +-- roles/storage.objectViewer
```

### GitHub-side evidence

GitHub Actions execution succeeded.

Successful steps:

```text
Checkout repository                    PASS
Authenticate to Google Cloud with WIF PASS
Verify federated identity              PASS
Read test object from Cloud Storage    PASS
```

The Cloud Storage step successfully returned:

```text
GitHub WIF laboratory object
```

This demonstrates successful end-to-end federated access from GitHub Actions to the GCP bucket.

---

## 15. Security Properties Demonstrated

### No long-lived GCP private key

The workflow does not contain:

```text
GOOGLE_APPLICATION_CREDENTIALS
service-account JSON
private key
```

### No service-account impersonation

The architecture contains no service account and no:

```text
roles/iam.workloadIdentityUser
```

binding.

The federated identity receives authorization directly on the bucket.

### Repository-restricted trust

The WIF provider validates:

```text
repository_owner_id
repository_id
```

before accepting the federated identity.

### Least privilege

The federated principal receives:

```text
roles/storage.objectViewer
```

only on the lab bucket.

The workload therefore has read access rather than administrative access to Cloud Storage.

---

## 16. Threat Model

| Threat | Mitigation used in this lab |
|---|---|
| Long-lived credential leakage | No service-account key |
| Broad GitHub trust | Repository and owner attribute condition |
| Excessive resource privileges | `roles/storage.objectViewer` only |
| Shared workload identity | Repository-specific federated identity |
| Persistent cloud credentials | GitHub OIDC / short-lived federation model |
| Cross-repository access | Repository ID restriction |
| Confused-deputy risk | Explicit issuer and identity conditions |

---

## 17. Key Design Decisions

### Decision 1 — Use Workload Identity Federation

Reason:

Avoid distributing long-lived Google Cloud service-account keys to GitHub.

### Decision 2 — Use Direct Resource Access

Reason:

Cloud Storage supports direct federation, so an intermediate Google Cloud service account is unnecessary for this workload.

### Decision 3 — Restrict by repository identity

Reason:

Trust should be limited to the intended GitHub workload rather than the entire GitHub OIDC issuer.

### Decision 4 — Use least privilege

Reason:

The workload only needs to read the test object.

Therefore:

```text
roles/storage.objectViewer
```

is sufficient.

### Decision 5 — Use a dedicated lab trust boundary

Reason:

The learning environment is isolated from unrelated identities and resources.

---

## 18. What This Lab Teaches

### Workload Identity

A workload needs an identity just as a user does.

### Federation

The workload's identity can originate outside Google Cloud.

### OIDC

GitHub provides a signed identity assertion describing the workflow context.

### Workload Identity Provider

Google Cloud establishes how GitHub credentials are trusted and interpreted.

### Attribute Mapping

External OIDC claims become Google-recognized attributes.

### Attribute Conditions

Those attributes restrict which external identities may federate.

### Security Token Service

STS performs the credential exchange and produces a short-lived federated credential.

### IAM

IAM remains responsible for authorization.

### Direct Resource Access

The federated principal can be granted resource-specific permissions without a Google service account.

---

## 19. Interview Explanation

> "I implemented GitHub Actions to Google Cloud using Direct Workload Identity Federation. GitHub Actions obtains an OIDC token, and Google Cloud trusts GitHub through a Workload Identity Pool and OIDC provider. The provider maps GitHub claims such as repository ID and owner ID and applies a condition restricting federation to my specific repository. Google Security Token Service exchanges the external credential for a short-lived federated credential. I then grant the federated principal `roles/storage.objectViewer` directly on a Cloud Storage bucket. There is no Google service-account key and no service-account impersonation. The important separation is that WIF establishes the trusted workload identity, while IAM determines what that identity is allowed to access."

---

## 20. Lessons Learned

### Authentication and authorization are separate

A successful OIDC token does not automatically provide resource access.

```text
OIDC
 ↓
Federation
 ↓
Identity
 ↓
IAM
 ↓
Resource access
```

### WIF is not the same thing as IAM

WIF establishes trust for an external identity.

IAM provides authorization.

### Direct WIF can remove an entire identity hop

For supported resources:

```text
Federated principal
        ↓
Resource IAM
```

is simpler because there is no intermediate service account.

### Attribute conditions are a security boundary

A provider should not blindly trust every identity issued by a shared external OIDC issuer.

### Least privilege still matters

Federation removes key-management problems but does not prevent an administrator from granting an excessive IAM role.

---

## 21. Lab Completion Checklist

- [x] GCP administrative authentication working
- [x] Cloud Storage bucket created
- [x] Test object created
- [x] Workload Identity Pool created
- [x] GitHub OIDC provider created
- [x] Attribute mappings configured
- [x] Repository/owner attribute condition configured
- [x] Direct IAM binding configured
- [x] GitHub Actions OIDC permission configured
- [x] GitHub Actions authenticated using direct WIF
- [x] Cloud Storage access verified
- [x] No service-account key used
- [x] No service-account impersonation used
- [x] Workflow updated to current checkout action
- [x] Successful end-to-end execution demonstrated

---

## 22. Final Architecture Summary

```text
                GitHub Actions
                      |
                      | OIDC JWT
                      v
          +---------------------------+
          | GitHub OIDC Issuer        |
          | token.actions...          |
          +-------------+-------------+
                        |
                        v
          +---------------------------+
          | GCP WIF Provider          |
          |                           |
          | issuer validation         |
          | attribute mapping         |
          | repository condition      |
          +-------------+-------------+
                        |
                        v
             Google Security Token
                    Service
                        |
                        | short-lived
                        | federated credential
                        v
               Federated Principal
                        |
                        | IAM:
                        | storage.objectViewer
                        v
             +---------------------+
             | Cloud Storage       |
             | github-wif bucket   |
             +----------+----------+
                        |
                        v
                  wif-test.txt
```

### Final principle

```text
Trusted external workload identity
              +
       Explicit trust condition
              +
       Short-lived credential
              +
       Direct least-privilege IAM
              =
     Keyless GCP workload access
```

---

## Official References

- Google Cloud — Workload Identity Federation:
  https://docs.cloud.google.com/iam/docs/workload-identity-federation
- Google Cloud — Direct resource access:
  https://docs.cloud.google.com/iam/docs/workload-download-cred-and-grant-access
- Google Cloud — Workload Identity Federation with deployment pipelines:
  https://docs.cloud.google.com/iam/docs/workload-identity-federation-with-deployment-pipelines
- Google Cloud — Identity federation supported services and limitations:
  https://docs.cloud.google.com/iam/docs/federated-identity-supported-services
- Google GitHub Actions authentication:
  https://github.com/google-github-actions/auth
- GitHub — OpenID Connect reference:
  https://docs.github.com/en/actions/reference/security/oidc
- GitHub — Configure OIDC with Google Cloud:
  https://docs.github.com/en/actions/how-tos/secure-your-work/security-harden-deployments/oidc-in-google-cloud-platform
