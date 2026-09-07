# Cloud Storage IAM Evidence

## Purpose

This document records the Google Cloud IAM authorization granted to the federated GitHub workload.

The lab uses **Direct Workload Identity Federation**. The federated GitHub identity receives permission directly on the Cloud Storage bucket.

## Environment

| Item | Value |
|---|---|
| GCP Project ID | `dev-project-506017` |
| GCP Project Number | `229836775022` |
| WIF Pool | `github-wif-lab` |
| WIF Provider | `github-oidc` |
| GitHub Repository | `Dhiraj-Yadav07/engineering-journey` |
| Repository ID | `1336061111` |
| Repository Owner ID | `146002674` |
| Cloud Storage Bucket | `gs://dev-project-506017-github-wif-11878` |
| Test Object | `wif-test.txt` |
| IAM Role | `roles/storage.objectViewer` |

## Test Resource

The lab bucket was created with uniform bucket-level access:

```bash
export PROJECT_ID="dev-project-506017"
export BUCKET_NAME="${PROJECT_ID}-github-wif-${RANDOM}"

gcloud storage buckets create "gs://${BUCKET_NAME}"   --project="${PROJECT_ID}"   --location=asia-south1   --uniform-bucket-level-access
```

The actual bucket used by the successful lab is:

```text
gs://dev-project-506017-github-wif-11878
```

A test object was uploaded:

```bash
echo "GitHub WIF laboratory object" > wif-test.txt

gcloud storage cp wif-test.txt   "gs://dev-project-506017-github-wif-11878/wif-test.txt"
```

Verification:

```bash
gcloud storage ls "gs://dev-project-506017-github-wif-11878/"
```

Result:

```text
gs://dev-project-506017-github-wif-11878/wif-test.txt
```

## Direct WIF Authorization

The federated GitHub workload is authorized directly on the bucket.

IAM principal set:

```text
principalSet://iam.googleapis.com/projects/229836775022/locations/global/workloadIdentityPools/github-wif-lab/attribute.repository_id/1336061111
```

IAM role:

```text
roles/storage.objectViewer
```

This binding means:

```text
Federated identities from github-wif-lab
        |
        | repository_id = 1336061111
        v
roles/storage.objectViewer
        |
        v
gs://dev-project-506017-github-wif-11878
```

## IAM Configuration Command

The binding was created with:

```bash
gcloud storage buckets add-iam-policy-binding   "gs://dev-project-506017-github-wif-11878"   --role="roles/storage.objectViewer"   --member="principalSet://iam.googleapis.com/projects/229836775022/locations/global/workloadIdentityPools/github-wif-lab/attribute.repository_id/1336061111"
```

## IAM Verification

The bucket policy was verified with:

```bash
gcloud storage buckets get-iam-policy   "gs://dev-project-506017-github-wif-11878"
```

Relevant verified binding:

```text
members:
- principalSet://iam.googleapis.com/projects/229836775022/locations/global/workloadIdentityPools/github-wif-lab/attribute.repository_id/1336061111

role: roles/storage.objectViewer
```

The bucket policy also contains Google-managed legacy project-level entries such as:

```text
projectEditor
projectOwner
projectViewer
```

These were already present as part of the bucket/project policy. The WIF lab-specific authorization is the `principalSet` binding shown above.

## Why `roles/storage.objectViewer`?

The workload only needs to read the test object.

Therefore:

```text
roles/storage.objectViewer
```

is preferred over broader roles such as:

```text
roles/storage.admin
```

This demonstrates least-privilege authorization.

## Runtime Verification

The GitHub Actions workflow successfully executed:

```bash
gcloud storage cat   gs://dev-project-506017-github-wif-11878/wif-test.txt
```

and returned:

```text
GitHub WIF laboratory object
```

Successful workflow stages:

```text
Checkout repository                    PASS
Authenticate to Google Cloud with WIF PASS
Verify federated identity              PASS
Read test object from Cloud Storage    PASS
```

This is the end-to-end authorization evidence.

## Security Model

The runtime path is:

```text
GitHub Actions
      |
      | OIDC token
      v
GCP WIF Provider
      |
      | repository-restricted federation
      v
Federated principal
      |
      | roles/storage.objectViewer
      v
Cloud Storage bucket
```

There is deliberately no:

```text
Service account
Service-account private key
Service-account impersonation
roles/iam.workloadIdentityUser
```

The federated identity is authorized directly against the Cloud Storage resource.

## Least-Privilege Assessment

The workload can read/list objects required by the lab, but it was not granted Cloud Storage administration privileges.

Security principle:

```text
Authentication
    +
Federation trust
    +
Least-privilege IAM
    =
Controlled workload access
```

## Evidence Summary

The successful GitHub Actions run proves that:

1. GitHub issued an OIDC identity for the workflow.
2. The WIF provider accepted the intended repository identity.
3. Google Cloud established a federated workload identity.
4. IAM authorized that identity directly on the bucket.
5. The workflow successfully read the Cloud Storage test object.

This file documents the authorization layer of the lab.
The trust configuration is documented separately in `gcp-wif-provider.md`.
