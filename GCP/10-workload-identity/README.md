# GitHub Actions → GCP Workload Identity Federation → Cloud Storage

A hands-on **Google Cloud Security** lab demonstrating keyless workload authentication from **GitHub Actions to Google Cloud** using **Workload Identity Federation (WIF)** and **direct resource access to Cloud Storage**.

The lab intentionally does **not** use a Google Cloud service account, service-account private key, or service-account impersonation in the runtime path.

---

## 1. Objective

The objective of this project is to understand and implement:

- GitHub Actions OIDC
- Google Cloud Workload Identity Federation
- Workload Identity Pools
- OIDC Workload Identity Providers
- OIDC claim / attribute mapping
- Attribute-based trust conditions
- Federated IAM principals
- Direct resource authorization
- Least-privilege access to Cloud Storage
- Keyless CI/CD authentication

The final result is:

```text
GitHub Actions
      |
      | GitHub OIDC token
      v
GCP Workload Identity Federation
      |
      | provider validation
      | attribute mapping
      | repository restriction
      v
Federated Principal
      |
      | roles/storage.objectViewer
      v
Cloud Storage
```

---

## 2. Why This Lab?

A traditional CI/CD integration often stores a Google Cloud service-account JSON key in GitHub.

That creates a long-lived credential:

```text
GitHub Secrets
      |
      | service-account private key
      v
Google Cloud
```

The key must then be protected, rotated, revoked, and carefully handled.

This lab replaces that model with:

```text
GitHub Actions
      |
      | short-lived OIDC identity
      v
Google Workload Identity Federation
      |
      | short-lived federated credential
      v
Federated Principal
      |
      | direct IAM authorization
      v
Cloud Storage
```

The workload does not need a persistent Google private key.

---

# 3. Architecture

## High-Level Architecture

```text
                         GITHUB
+-----------------------------------------------------+
|                                                     |
|  Repository: Dhiraj-Yadav07/engineering-journey    |
|                                                     |
|  GitHub Actions                                     |
|        |                                            |
|        | requests OIDC token                        |
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
|  Project Number: 229836775022                      |
|                                                     |
|  Workload Identity Pool                            |
|      github-wif-lab                                |
|             |                                      |
|             v                                      |
|  OIDC Provider                                     |
|      github-oidc                                   |
|             |                                      |
|             +-- issuer validation                  |
|             +-- attribute mapping                  |
|             +-- repository condition               |
|             |                                      |
|             v                                      |
|  Google Security Token Service                     |
|             |                                      |
|             | short-lived federated credential     |
|             v                                      |
|  Federated Principal                               |
|             |                                      |
|             | roles/storage.objectViewer            |
|             v                                      |
|  Cloud Storage                                     |
|  gs://dev-project-506017-github-wif-11878          |
|             |                                      |
|             v                                      |
|       wif-test.txt                                 |
+-----------------------------------------------------+
```

---

# 4. Authentication vs Authorization

A central concept demonstrated by this lab is that **authentication/federation and authorization are separate controls**.

### Authentication / Federation

The question is:

> Is this GitHub workload an identity that GCP is willing to trust?

The provider handles:

```text
OIDC issuer
     +
claim mapping
     +
attribute condition
```

### Authorization

The question is:

> What can the trusted workload do?

Cloud Storage IAM handles this:

```text
Federated principal
      |
      | roles/storage.objectViewer
      v
Bucket
```

Therefore:

```text
WIF
 =
trusted external workload identity

IAM
 =
authorization
```

---

# 5. Implemented Configuration

| Component | Value |
|---|---|
| GitHub repository | `Dhiraj-Yadav07/engineering-journey` |
| GitHub repository ID | `1336061111` |
| GitHub owner ID | `146002674` |
| GCP project ID | `dev-project-506017` |
| GCP project number | `229836775022` |
| Workload Identity Pool | `github-wif-lab` |
| OIDC Provider | `github-oidc` |
| GitHub OIDC issuer | `https://token.actions.githubusercontent.com/` |
| Cloud Storage bucket | `gs://dev-project-506017-github-wif-11878` |
| Test object | `wif-test.txt` |
| IAM role | `roles/storage.objectViewer` |
| Authentication model | Direct WIF |
| Service account | Not used |
| Service-account key | Not used |
| Service-account impersonation | Not used |

---

# 6. Workload Identity Pool

The lab uses:

```text
github-wif-lab
```

Canonical resource:

```text
projects/229836775022/locations/global/workloadIdentityPools/github-wif-lab
```

The pool provides the Google Cloud trust boundary for the external workload.

Created with:

```bash
gcloud iam workload-identity-pools create github-wif-lab   --project="dev-project-506017"   --location="global"   --display-name="GitHub Actions WIF Lab"
```

Verified state:

```text
state: ACTIVE
```

---

# 7. GitHub OIDC Provider

The provider is:

```text
github-oidc
```

Canonical resource:

```text
projects/229836775022/locations/global/workloadIdentityPools/github-wif-lab/providers/github-oidc
```

Issuer:

```text
https://token.actions.githubusercontent.com/
```

The provider was configured to:

1. Trust the GitHub OIDC issuer.
2. Map GitHub claims into Google attributes.
3. Restrict federation to the intended repository.

---

## 7.1 Attribute Mapping

Implemented mappings:

```text
google.subject                = assertion.sub
attribute.repository_id       = assertion.repository_id
attribute.repository_owner_id = assertion.repository_owner_id
attribute.repository          = assertion.repository
```

---

## 7.2 Attribute Condition

The provider requires:

```text
attribute.repository_owner_id == '146002674'
&&
attribute.repository_id == '1336061111'
```

Therefore the trust boundary is:

```text
GitHub
  |
  +-- owner ID = 146002674
  |
  +-- repository ID = 1336061111
  |
  v
ACCEPT
```

The provider does not broadly trust every GitHub repository.

---

# 8. Cloud Storage Authorization

The lab bucket is:

```text
gs://dev-project-506017-github-wif-11878
```

The test object is:

```text
wif-test.txt
```

The federated principal set was granted:

```text
roles/storage.objectViewer
```

using:

```text
principalSet://iam.googleapis.com/projects/229836775022/locations/global/workloadIdentityPools/github-wif-lab/attribute.repository_id/1336061111
```

The resulting authorization model is:

```text
Federated GitHub identity
        |
        | roles/storage.objectViewer
        v
Cloud Storage bucket
```

This is **direct resource access**.

There is no intermediate Google Cloud service account.

---

# 9. GitHub Actions Workflow

The workflow is located at the repository root:

```text
.github/
└── workflows/
    └── gcp-wif-test.yml
```

The workflow requests only the permissions required for the demonstration:

```yaml
permissions:
  contents: read
  id-token: write
```

The relevant authentication step is:

```yaml
- name: Authenticate to Google Cloud with WIF
  uses: google-github-actions/auth@v3
  with:
    workload_identity_provider: "projects/229836775022/locations/global/workloadIdentityPools/github-wif-lab/providers/github-oidc"
```

Notice that the workflow does **not** specify:

```yaml
service_account:
```

This is intentional. The lab uses **Direct Workload Identity Federation**.

The validation step reads:

```bash
gcloud storage cat gs://dev-project-506017-github-wif-11878/wif-test.txt
```

---

# 10. End-to-End Authentication Flow

The runtime flow is:

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
4. Google GitHub authentication action
   sends the token to GCP WIF
        |
        v
5. WIF provider validates the token
        |
        +-- issuer
        +-- mapped claims
        +-- repository condition
        |
        v
6. Google Security Token Service
   exchanges the external identity
        |
        v
7. Short-lived federated credential
        |
        v
8. Federated principal is evaluated by IAM
        |
        v
9. Cloud Storage bucket IAM policy
        |
        v
10. roles/storage.objectViewer allows access
        |
        v
11. wif-test.txt is returned
```

---

# 11. Validation

The lab was successfully validated through GitHub Actions.

Successful workflow stages:

```text
Checkout repository                    PASS
Authenticate to Google Cloud with WIF PASS
Verify federated identity              PASS
Read test object from Cloud Storage    PASS
```

The final Cloud Storage operation returned:

```text
GitHub WIF laboratory object
```

This proves the end-to-end path:

```text
GitHub Actions
      ↓
GitHub OIDC
      ↓
GCP WIF
      ↓
Federated identity
      ↓
Direct IAM authorization
      ↓
Cloud Storage
```

---

# 12. Security Properties

## Keyless Authentication

No Google Cloud service-account private key is stored in GitHub.

```text
No JSON key
No static private key
No long-lived cloud credential
```

## Repository-Restricted Trust

Federation is limited using:

```text
repository_owner_id
repository_id
```

## Least Privilege

The workload receives:

```text
roles/storage.objectViewer
```

rather than a broad administrative role.

## Direct Resource Access

The federated identity is authorized directly against the bucket.

## Separation of Controls

```text
GitHub OIDC
      ↓
WIF trust decision
      ↓
Federated identity
      ↓
IAM authorization
      ↓
Cloud Storage
```

---

# 13. Why Direct WIF?

For this lab, direct federation is preferable because Cloud Storage supports direct resource access with a federated principal.

It removes the additional runtime identity hop that would exist with service-account impersonation:

```text
Direct WIF:

Federated principal
        ↓
Cloud Storage


Alternative:

Federated principal
        ↓
Google service account
        ↓
Cloud Storage
```

Direct WIF therefore keeps this lab focused on the fundamental workload federation model.

The lab deliberately excludes service-account impersonation because it is not required for the chosen Cloud Storage use case.

---

# 14. Security Threats and Controls

| Threat | Control |
|---|---|
| Long-lived service-account key leakage | Use GitHub OIDC + WIF |
| Any GitHub repository gaining trust | Repository/owner attribute condition |
| Excessive Cloud Storage access | `roles/storage.objectViewer` |
| Shared workload identity | Repository-specific principal set |
| Unrestricted federation | Provider condition |
| Credential persistence | Short-lived federated credentials |

---

# 15. Key Lessons Learned

## 15.1 WIF is not an IAM permission

WIF establishes a trusted external identity.

IAM determines what that identity can access.

---

## 15.2 `id-token: write` is not GCP access

The GitHub workflow permission:

```yaml
id-token: write
```

allows the workflow to request an OIDC token.

GCP still independently evaluates:

```text
provider
+
attribute condition
+
IAM policy
```

---

## 15.3 Attribute mapping enables policy decisions

External OIDC claims such as:

```text
repository_id
repository_owner_id
```

become Google-recognized attributes and can then be used in the provider's trust condition.

---

## 15.4 Authentication can succeed while authorization fails

A workload can have a valid identity but still lack:

```text
roles/storage.objectViewer
```

Therefore:

```text
valid identity
      !=
authorized identity
```

---

## 15.5 Federation reduces secret management

Instead of:

```text
private key
  +
GitHub secret
  +
rotation
  +
revocation
```

the workload uses:

```text
GitHub OIDC
  +
WIF
  +
short-lived credential
```

---

# 16. Evidence

Detailed evidence is stored under:

```text
evidence/
├── gcp-wif-provider.md
└── cloud-storage-iam.md
```

The repository-level GitHub Actions workflow is:

```text
.github/workflows/gcp-wif-test.yml
```

The architecture/design documentation is:

```text
identity-architecture-note.md
```

A successful GitHub Actions execution provides runtime validation that the federated workload can access the target Cloud Storage object.

---

# 17. Project Completion Checklist

- [x] GCP administrative authentication configured
- [x] Cloud Storage bucket created
- [x] Test object uploaded
- [x] Required GCP APIs enabled
- [x] Workload Identity Pool created
- [x] GitHub OIDC Provider created
- [x] OIDC issuer configured
- [x] Attribute mappings configured
- [x] Repository-restricted attribute condition configured
- [x] Direct federated IAM binding configured
- [x] Least-privilege Cloud Storage role configured
- [x] GitHub Actions OIDC permission configured
- [x] GitHub Actions authenticated through WIF
- [x] Cloud Storage object successfully read
- [x] No service-account private key used
- [x] No service-account impersonation used
- [x] Workflow updated to current action version used in the lab
- [x] End-to-end successful validation completed

---

# 18. Interview-Level Explanation

> **I implemented GitHub Actions to Google Cloud using Direct Workload Identity Federation. GitHub Actions obtains an OIDC token, which Google Cloud validates through a Workload Identity Pool and GitHub OIDC provider. The provider maps GitHub claims such as repository ID and owner ID and restricts federation to the intended repository. Google Security Token Service exchanges the external credential for a short-lived federated credential. I then grant the federated principal `roles/storage.objectViewer` directly on a Cloud Storage bucket. There is no service-account key and no service-account impersonation. The key architectural separation is that WIF establishes trusted workload identity, while IAM provides resource authorization.**

---

# 19. Project Structure

```text
engineering-journey/
│
├── .github/
│   └── workflows/
│       └── gcp-wif-test.yml
│
└── GCP/
    └── 10-workload-identity/
        ├── README.md
        ├── identity-architecture-note.md
        └── evidence/
            ├── gcp-wif-provider.md
            └── cloud-storage-iam.md
```

---

# 20. Final Architecture

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
          | WIF Pool                  |
          | github-wif-lab            |
          +-------------+-------------+
                        |
                        v
          +---------------------------+
          | OIDC Provider             |
          | github-oidc               |
          |                           |
          | Claim mapping             |
          | Repository condition      |
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
                        | roles/storage.objectViewer
                        v
             +---------------------+
             | Cloud Storage       |
             | github-wif bucket   |
             +----------+----------+
                        |
                        v
                  wif-test.txt
```

---

## Final Principle

```text
External workload identity
          +
Explicit trust boundary
          +
Claim/attribute restrictions
          +
Short-lived credentials
          +
Least-privilege IAM
          +
Direct resource access
          =
Secure keyless workload access to GCP
```

---

## Official References

- Google Cloud — Workload Identity Federation  
  https://docs.cloud.google.com/iam/docs/workload-identity-federation

- Google Cloud — Direct resource access for federated identities  
  https://docs.cloud.google.com/iam/docs/workload-download-cred-and-grant-access

- Google Cloud — WIF with deployment pipelines  
  https://docs.cloud.google.com/iam/docs/workload-identity-federation-with-deployment-pipelines

- Google Cloud — Supported services for federated identities  
  https://docs.cloud.google.com/iam/docs/federated-identity-supported-services

- GitHub — OpenID Connect  
  https://docs.github.com/en/actions/reference/security/oidc

- GitHub — OIDC with Google Cloud  
  https://docs.github.com/en/actions/how-tos/secure-your-work/security-harden-deployments/oidc-in-google-cloud-platform

- google-github-actions/auth  
  https://github.com/google-github-actions/auth
