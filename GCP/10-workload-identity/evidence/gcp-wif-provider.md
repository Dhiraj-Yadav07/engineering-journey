# GCP Workload Identity Federation Provider Evidence

## Purpose

This document records the Google Cloud Workload Identity Federation configuration used by the GitHub Actions lab.

The implementation uses **Direct Workload Identity Federation**. No Google Cloud service account is used in the runtime authentication path.

## Environment

| Item | Value |
|---|---|
| GCP Project ID | `dev-project-506017` |
| GCP Project Number | `229836775022` |
| GitHub Repository | `Dhiraj-Yadav07/engineering-journey` |
| GitHub Repository ID | `1336061111` |
| GitHub Repository Owner ID | `146002674` |
| Workload Identity Pool | `github-wif-lab` |
| Workload Identity Provider | `github-oidc` |
| External Identity Provider | GitHub Actions OIDC |

## Workload Identity Pool

Created with:

```bash
gcloud iam workload-identity-pools create github-wif-lab   --project="dev-project-506017"   --location="global"   --display-name="GitHub Actions WIF Lab"
```

Verification:

```bash
gcloud iam workload-identity-pools describe github-wif-lab   --project="dev-project-506017"   --location="global"
```

Verified state:

```text
displayName: GitHub Actions WIF Lab
name: projects/229836775022/locations/global/workloadIdentityPools/github-wif-lab
state: ACTIVE
```

## OIDC Provider

The provider trusts the GitHub Actions OIDC issuer:

```text
https://token.actions.githubusercontent.com/
```

Provider resource:

```text
projects/229836775022/locations/global/workloadIdentityPools/github-wif-lab/providers/github-oidc
```

## Attribute Mapping

Implemented provider mappings:

```text
google.subject                = assertion.sub
attribute.repository_id       = assertion.repository_id
attribute.repository_owner_id = assertion.repository_owner_id
attribute.repository          = assertion.repository
```

The mappings translate claims from the GitHub OIDC token into Google Cloud workload identity attributes.

## Attribute Condition

The provider is restricted to the intended GitHub repository using its stable numeric identifiers:

```text
attribute.repository_owner_id == '146002674'
&&
attribute.repository_id == '1336061111'
```

This means the WIF provider will only accept a GitHub workload whose owner and repository IDs match the intended repository.

The trust model is therefore:

```text
GitHub OIDC token
       |
       +-- repository_owner_id = 146002674
       |
       +-- repository_id       = 1336061111
       |
       v
     ACCEPT
```

Other repository identities fail the provider condition.

## Provider Creation

The provider was created with:

```bash
gcloud iam workload-identity-pools providers create-oidc github-oidc   --project="dev-project-506017"   --location="global"   --workload-identity-pool="github-wif-lab"   --issuer-uri="https://token.actions.githubusercontent.com/"   --attribute-mapping="google.subject=assertion.sub,attribute.repository_id=assertion.repository_id,attribute.repository_owner_id=assertion.repository_owner_id,attribute.repository=assertion.repository"   --attribute-condition="attribute.repository_owner_id == '146002674' && attribute.repository_id == '1336061111'"
```

## Verification Output

The provider was verified with:

```bash
gcloud iam workload-identity-pools providers describe github-oidc   --project="dev-project-506017"   --location="global"   --workload-identity-pool="github-wif-lab"
```

Observed configuration:

```text
attributeCondition: attribute.repository_owner_id == '146002674' && attribute.repository_id
  == '1336061111'

attributeMapping:
  attribute.repository: assertion.repository
  attribute.repository_id: assertion.repository_id
  attribute.repository_owner_id: assertion.repository_owner_id
  google.subject: assertion.sub

name: projects/229836775022/locations/global/workloadIdentityPools/github-wif-lab/providers/github-oidc

oidc:
  issuerUri: https://token.actions.githubusercontent.com/

state: ACTIVE
```

## Security Significance

The GitHub OIDC issuer is shared across many GitHub repositories and organizations. The provider therefore does not trust the issuer alone.

The provider establishes a narrower trust boundary by requiring:

```text
repository_owner_id = 146002674
repository_id       = 1336061111
```

This restricts federation to the intended GitHub repository.

## Runtime Model

The provider establishes workload identity trust. It does not directly grant Cloud Storage permissions.

The runtime flow is:

```text
GitHub Actions
      |
      | GitHub OIDC JWT
      v
GitHub OIDC Provider
      |
      | validate + map claims + condition
      v
Google Security Token Service
      |
      | short-lived federated credential
      v
Federated principal
      |
      v
Cloud Storage IAM
```

The workload does **not** use:

```text
Google service-account key
Service-account impersonation
roles/iam.workloadIdentityUser
```

## Evidence Summary

The provider is:

```text
ACTIVE
```

and is restricted to:

```text
Dhiraj-Yadav07/engineering-journey
repository_id = 1336061111
owner_id      = 146002674
```

This provider configuration is the trust layer of the lab.
Authorization is documented separately in `cloud-storage-iam.md`.
