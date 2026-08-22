# GCP IAM – Cloud Audit Logs: Identity & Access Activity

## Overview

This lab demonstrates how to inspect **Google Cloud Audit Logs** for identity and access activity.

The lab was performed against the GCP project:

```text
dev-project-506017
```

The objective was to generate controlled IAM activity, inspect the resulting Cloud Audit Log entries, identify the authenticated principal and API operation, inspect the affected resource, examine the underlying audit record, and verify the IAM policy change through `policyDelta`.

The temporary IAM resources created for the lab were cleaned up successfully after the investigation.

---

## Lab Details

| Field | Details |
|---|---|
| Focus | GCP IAM |
| Task | Enable and inspect Cloud Audit Logs for identity/access activity |
| Type | Hands-on Lab |
| GCP Project | `dev-project-506017` |
| Tools | Google Cloud Shell, `gcloud`, Cloud Logging |
| Deliverable | Audit trail examples |
| Status | **Completed** |

---

## Objectives

- Inspect Cloud Audit Logs for IAM activity.
- Generate controlled IAM administrative activity.
- Identify the authenticated principal responsible for an operation.
- Identify the API method that was invoked.
- Identify the affected GCP resource.
- Inspect authorization information.
- Inspect IAM policy changes through `policyDelta`.
- Correlate an IAM action with its audit record.
- Verify cleanup of temporary IAM resources.

---

# 1. Project Verification

The active GCP project was verified using:

```bash
gcloud config get-value project
```

Result:

```text
dev-project-506017
```

The project was independently verified using:

```bash
gcloud projects describe dev-project-506017 \
  --format="value(projectId)"
```

Result:

```text
dev-project-506017
```

This confirms that the lab was performed against the intended project.

---

# 2. Cloud Audit Logs Inspection

Available logging streams were inspected using:

```bash
gcloud logging logs list
```

The project contained the Cloud Audit Logs activity stream:

```text
projects/dev-project-506017/logs/cloudaudit.googleapis.com%2Factivity
```

Audit activity was then queried using:

```bash
gcloud logging read \
'logName:"cloudaudit.googleapis.com"' \
--limit=10 \
--format="table(timestamp,logName,protoPayload.methodName,protoPayload.authenticationInfo.principalEmail)"
```

The query returned real audit activity, including examples such as:

```text
v1.compute.instances.delete
google.iam.admin.v1.DeleteServiceAccount
SetIamPolicy
google.api.serviceusage.v1.ServiceUsage.EnableService
v1.compute.instances.insert
```

This confirmed that Cloud Audit Logs were available and recording administrative activity in the project.

---

# 3. Generate Controlled IAM Activity

A temporary service account was created specifically for the audit investigation:

```bash
gcloud iam service-accounts create audit-lab-sa \
  --display-name="Audit Lab Service Account"
```

Creation result:

```text
Created service account [audit-lab-sa].

Service account email:
audit-lab-sa@dev-project-506017.iam.gserviceaccount.com
```

This action generated an IAM audit event.

---

# 4. Audit Evidence – CreateServiceAccount

The corresponding audit event was queried using:

```bash
gcloud logging read \
'protoPayload.methodName="google.iam.admin.v1.CreateServiceAccount"' \
--limit=10 \
--format="table(timestamp,protoPayload.authenticationInfo.principalEmail,protoPayload.methodName,protoPayload.resourceName)"
```

The lab-generated event:

```text
TIMESTAMP:
2026-08-22T06:22:56.131243158Z

PRINCIPAL:
dhirajy076@gmail.com

METHOD:
google.iam.admin.v1.CreateServiceAccount

RESOURCE:
projects/dev-project-506017
```

This establishes the first audit trail:

```text
Authenticated Principal
        ↓
google.iam.admin.v1.CreateServiceAccount
        ↓
projects/dev-project-506017
        ↓
Cloud Audit Logs
```

---

# 5. Raw AuditLog Evidence – CreateServiceAccount

The complete audit event was inspected using:

```bash
gcloud logging read \
'protoPayload.methodName="google.iam.admin.v1.CreateServiceAccount"' \
--limit=1 \
--format=json
```

Important fields from the captured audit record:

```text
principalEmail:
dhirajy076@gmail.com

principalSubject:
user:dhirajy076@gmail.com

permission:
iam.serviceAccounts.create

permissionType:
ADMIN_WRITE

methodName:
google.iam.admin.v1.CreateServiceAccount

resourceName:
projects/dev-project-506017

serviceName:
iam.googleapis.com
```

The request identified the temporary account:

```text
account_id:
audit-lab-sa
```

The response confirmed creation of:

```text
audit-lab-sa@dev-project-506017.iam.gserviceaccount.com
```

### What this proves

The audit record provides evidence of:

- **Who** performed the operation.
- **What** API operation was performed.
- **Which permission** was exercised.
- **What type of permission** was involved.
- **Which project/resource** was affected.
- **When** the operation occurred.

---

# 6. Generate an IAM Policy Change

The temporary service account was granted the Viewer role:

```bash
gcloud projects add-iam-policy-binding dev-project-506017 \
  --member="serviceAccount:audit-lab-sa@dev-project-506017.iam.gserviceaccount.com" \
  --role="roles/viewer"
```

The command successfully updated the project IAM policy.

The resulting IAM policy contained:

```text
serviceAccount:audit-lab-sa@dev-project-506017.iam.gserviceaccount.com
role: roles/viewer
```

---

# 7. Audit Evidence – SetIamPolicy

The IAM policy change was located using:

```bash
gcloud logging read \
'protoPayload.methodName="SetIamPolicy"' \
--limit=10 \
--format="table(timestamp,protoPayload.authenticationInfo.principalEmail,protoPayload.methodName,protoPayload.resourceName)"
```

The lab-generated event:

```text
TIMESTAMP:
2026-08-22T06:38:06.385396Z

PRINCIPAL:
dhirajy076@gmail.com

METHOD:
SetIamPolicy

RESOURCE:
projects/dev-project-506017
```

---

# 8. Raw AuditLog Evidence – IAM Policy Delta

The complete `SetIamPolicy` audit record was inspected using:

```bash
gcloud logging read \
'protoPayload.methodName="SetIamPolicy"' \
--limit=1 \
--format=json
```

The captured audit event contained:

```text
principalEmail:
dhirajy076@gmail.com
```

```text
permission:
resourcemanager.projects.setIamPolicy
```

```text
permissionType:
ADMIN_WRITE
```

```text
methodName:
SetIamPolicy
```

```text
resourceName:
projects/dev-project-506017
```

Most importantly, the audit record contained the policy delta:

```text
action:
ADD

member:
serviceAccount:audit-lab-sa@dev-project-506017.iam.gserviceaccount.com

role:
roles/viewer
```

### Security significance

The audit record does not merely show that an IAM policy was modified.

The `policyDelta.bindingDeltas` information identifies the actual change:

```text
ADD
  ↓
serviceAccount:audit-lab-sa@...
  ↓
roles/viewer
```

This provides useful evidence during IAM/security investigations.

---

# 9. Audit Investigation Model

The lab demonstrates the following investigation methodology:

```text
WHO?
  ↓
protoPayload.authenticationInfo.principalEmail

WHAT?
  ↓
protoPayload.methodName

WHERE?
  ↓
protoPayload.resourceName

WHEN?
  ↓
timestamp

WHAT CHANGED?
  ↓
serviceData.policyDelta.bindingDeltas
```

For example, to investigate:

> Who changed the IAM policy on this project?

Search for:

```text
protoPayload.methodName="SetIamPolicy"
```

Then inspect:

```text
authenticationInfo.principalEmail
timestamp
resourceName
authorizationInfo
serviceData.policyDelta
```

---

# 10. Broader Audit Trail

A one-day audit query was also performed:

```bash
gcloud logging read \
'logName:"cloudaudit.googleapis.com"' \
--freshness=1d \
--limit=20 \
--format="table(timestamp,protoPayload.authenticationInfo.principalEmail,protoPayload.methodName,protoPayload.resourceName)"
```

The resulting audit trail included activity such as:

```text
SetIamPolicy
google.iam.admin.v1.CreateServiceAccount
google.iam.admin.v1.DeleteServiceAccount
v1.compute.instances.insert
v1.compute.instances.delete
iam.serviceAccounts.actAs
google.api.serviceusage.v1.ServiceUsage.EnableService
```

This demonstrates that Cloud Audit Logs can provide a chronological activity trail across IAM, Compute Engine, and other GCP services.

---

# 11. Cleanup

The temporary IAM binding was removed after the audit investigation:

```bash
gcloud projects remove-iam-policy-binding dev-project-506017 \
  --member="serviceAccount:audit-lab-sa@dev-project-506017.iam.gserviceaccount.com" \
  --role="roles/viewer"
```

Result:

```text
Updated IAM policy for project [dev-project-506017].
```

The temporary service account was then deleted:

```bash
gcloud iam service-accounts delete \
  audit-lab-sa@dev-project-506017.iam.gserviceaccount.com
```

Result:

```text
deleted service account [audit-lab-sa@dev-project-506017.iam.gserviceaccount.com]
```

Final verification:

```bash
gcloud iam service-accounts list
```

The final inventory contained only the pre-existing service accounts:

```text
iam-lab-observer@dev-project-506017.iam.gserviceaccount.com

229836775022-compute@developer.gserviceaccount.com
```

The temporary `audit-lab-sa` service account was no longer present.

### Cleanup status

**Complete.**

The temporary IAM binding and service account created for the lab were successfully removed.

---

# 12. Final Evidence Summary

| Evidence | Result |
|---|---|
| Correct GCP project verified | `dev-project-506017` |
| Cloud Audit Logs activity stream found | `cloudaudit.googleapis.com/activity` |
| IAM service account creation generated audit event | ✅ |
| Principal identified | `dhirajy076@gmail.com` |
| IAM method identified | `CreateServiceAccount` |
| IAM permission identified | `iam.serviceAccounts.create` |
| Permission type identified | `ADMIN_WRITE` |
| IAM policy change generated audit event | ✅ |
| Policy modification method identified | `SetIamPolicy` |
| Policy permission identified | `resourcemanager.projects.setIamPolicy` |
| Policy delta inspected | `ADD → roles/viewer` |
| Affected project identified | `projects/dev-project-506017` |
| Temporary IAM binding removed | ✅ |
| Temporary service account deleted | ✅ |
| Final service-account inventory verified | ✅ |

---

# 13. Key Security Engineering Takeaways

## 1. IAM actions are auditable

Administrative IAM operations such as service-account creation and IAM policy changes generate Cloud Audit Log records.

## 2. Identity attribution matters

`authenticationInfo.principalEmail` can identify the principal that performed an operation.

## 3. API methods identify the action

`protoPayload.methodName` identifies the API operation that occurred.

Examples from this lab:

```text
google.iam.admin.v1.CreateServiceAccount
SetIamPolicy
```

## 4. Resource attribution identifies the target

`resourceName` identifies the affected project/resource.

## 5. Authorization information provides additional security context

The audit records included authorization information such as:

```text
permission
permissionType
granted
```

## 6. IAM policy deltas reveal what changed

For IAM policy changes, `policyDelta.bindingDeltas` can show the actual binding modification.

Example:

```text
ADD
serviceAccount:audit-lab-sa@...
roles/viewer
```

## 7. Audit investigation follows a repeatable model

```text
WHO
 ↓
WHAT
 ↓
WHERE
 ↓
WHEN
 ↓
WHAT CHANGED
```

This is a useful foundation for IAM security investigations, incident response, and cloud security monitoring.

---

# 14. Lab Completion

**Status: COMPLETE ✅**

The lab successfully demonstrated:

- Cloud Audit Logs inspection.
- IAM administrative activity generation.
- Identity/principal attribution.
- API operation attribution.
- Resource attribution.
- Authorization information inspection.
- IAM policy delta inspection.
- Audit trail investigation.
- Temporary resource cleanup and verification.

The lab provides practical evidence of how GCP IAM activity can be traced through Cloud Audit Logs.

---

## Interview Takeaway

A concise way to describe this lab in an interview:

> I created controlled IAM activity in GCP, queried Cloud Audit Logs to identify the authenticated principal, API operation, affected resource, and authorization details, and then inspected the IAM `policyDelta` to determine exactly what binding was added. I also verified cleanup of the temporary IAM resources afterward.

The core investigation pattern is:

```text
WHO → WHAT → WHERE → WHEN → WHAT CHANGED
```
