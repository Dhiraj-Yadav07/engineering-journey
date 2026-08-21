# GCP IAM Conditions — Contextual Access Lab

## Objective

Implement and validate **Google Cloud IAM Conditions** using a temporary, time-based IAM binding.

The lab demonstrates:

- Creating a dedicated test service account.
- Creating a Compute Engine test VM.
- Granting `roles/compute.viewer` conditionally.
- Using **Policy Troubleshooter** to validate access.
- Testing access immediately before and at the condition expiry boundary.
- Capturing IAM policy evidence for the lab deliverable.

---

## Environment

| Item | Value |
|---|---|
| GCP Project | `dev-project-506017` |
| Project ID | `dev-project-506017` |
| Test Service Account | `iam-condition-test@dev-project-506017.iam.gserviceaccount.com` |
| Test VM | `iam-condition-test-vm` |
| Zone | `asia-south1-a` |
| Machine Type | `e2-micro` |
| Test Permission | `compute.instances.get` |
| Conditional Role | `roles/compute.viewer` |
| Condition | `request.time < timestamp("2026-08-22T17:00:00Z")` |
| Condition Title | `Temporary-Compute-Viewer` |

---

# 1. Verify GCP Project and Authentication

Check the active project:

```bash
gcloud config get-value project
```

Expected:

```text
dev-project-506017
```

Check the authenticated account:

```bash
gcloud auth list
```

Expected active account:

```text
dhirajy076@gmail.com
```

---

# 2. Inspect Existing IAM Policy

Command:

```bash
gcloud projects get-iam-policy dev-project-506017
```

At this stage the project already contained IAM bindings including:

- `roles/compute.viewer` for the user.
- `roles/owner` for the user.
- Custom role `projects/dev-project-506017/roles/computeInstanceObserver`.

The important point is that the new test service account should receive access through a **conditional** binding rather than unconditional access.

---

# 3. Create the Test Service Account

Create a dedicated principal for the IAM Conditions test:

```bash
gcloud iam service-accounts create iam-condition-test \
  --display-name="IAM Condition Test Principal"
```

Expected:

```text
Created service account [iam-condition-test].
```

Service account:

```text
iam-condition-test@dev-project-506017.iam.gserviceaccount.com
```

Verify:

```bash
gcloud iam service-accounts describe \
  iam-condition-test@dev-project-506017.iam.gserviceaccount.com
```

---

# 4. Verify Existing Compute Resources

Check whether test instances already exist:

```bash
gcloud compute instances list
```

The lab initially returned:

```text
Listed 0 items.
```

Therefore, create a dedicated test VM.

---

# 5. Create the Test VM

Create an inexpensive `e2-micro` VM:

```bash
gcloud compute instances create iam-condition-test-vm \
  --zone=asia-south1-a \
  --machine-type=e2-micro
```

Expected resource:

```text
Name: iam-condition-test-vm
Zone: asia-south1-a
Machine Type: e2-micro
Status: RUNNING
```

The VM is only being used as the target resource for IAM policy evaluation.

---

# 6. Enable Policy Troubleshooter API

Policy Troubleshooter is required to evaluate whether the test principal has a specific permission.

Run:

```bash
gcloud policy-intelligence troubleshoot-policy iam \
  "//compute.googleapis.com/projects/dev-project-506017/zones/asia-south1-a/instances/iam-condition-test-vm" \
  --principal-email="iam-condition-test@dev-project-506017.iam.gserviceaccount.com" \
  --permission="compute.instances.get"
```

If prompted to enable:

```text
policytroubleshooter.googleapis.com
```

answer:

```text
y
```

---

# 7. Important Resource Name Discovery

The initial attempts used:

```text
cloudresourcemanager.googleapis.com/projects/dev-project-506017
```

and:

```text
compute.googleapis.com/projects/dev-project-506017/...
```

without the required full-resource-name format.

The correct Compute Engine resource format for Policy Troubleshooter is:

```text
//compute.googleapis.com/projects/dev-project-506017/zones/asia-south1-a/instances/iam-condition-test-vm
```

Notice the leading:

```text
//
```

Use this exact format in the troubleshooting commands.

---

# 8. Baseline Troubleshooting

Before granting the conditional role, test:

```bash
gcloud policy-intelligence troubleshoot-policy iam \
  "//compute.googleapis.com/projects/dev-project-506017/zones/asia-south1-a/instances/iam-condition-test-vm" \
  --principal-email="iam-condition-test@dev-project-506017.iam.gserviceaccount.com" \
  --permission="compute.instances.get"
```

The service account does not have the required permission through the project IAM policy at this point.

The important expected result is:

```text
overallAccessState: CANNOT_ACCESS
```

This establishes the baseline:

> The test service account cannot access the VM before the conditional binding is added.

---

# 9. Implement IAM Condition

Grant `roles/compute.viewer` to the test service account with a time-based IAM Condition.

Command used:

```bash
gcloud projects add-iam-policy-binding dev-project-506017 \
  --member="serviceAccount:iam-condition-test@dev-project-506017.iam.gserviceaccount.com" \
  --role="roles/compute.viewer" \
  --condition='expression=request.time < timestamp("2026-08-22T17:00:00Z"),title=Temporary-Compute-Viewer,description=Temporary access for IAM Conditions lab'
```

The resulting conditional binding is:

```yaml
- condition:
    description: Temporary access for IAM Conditions lab
    expression: request.time < timestamp("2026-08-22T17:00:00Z")
    title: Temporary-Compute-Viewer
  members:
  - serviceAccount:iam-condition-test@dev-project-506017.iam.gserviceaccount.com
  role: roles/compute.viewer
```

---

# 10. Verify the IAM Condition

Run:

```bash
gcloud projects get-iam-policy dev-project-506017 \
  --flatten="bindings[]" \
  --filter="bindings.members:iam-condition-test@dev-project-506017.iam.gserviceaccount.com" \
  --format="table(bindings.role,bindings.condition.title,bindings.condition.expression,bindings.condition.description)"
```

Expected:

```text
ROLE: roles/compute.viewer
TITLE: Temporary-Compute-Viewer
EXPRESSION: request.time < timestamp("2026-08-22T17:00:00Z")
DESCRIPTION: Temporary access for IAM Conditions lab
```

This is one of the primary pieces of evidence for the lab.

---

# 11. Test Access Before Expiration

The IAM Condition is:

```text
request.time < 2026-08-22T17:00:00Z
```

Therefore, test one second before expiration:

```bash
gcloud policy-intelligence troubleshoot-policy iam \
  "//compute.googleapis.com/projects/dev-project-506017/zones/asia-south1-a/instances/iam-condition-test-vm" \
  --principal-email="iam-condition-test@dev-project-506017.iam.gserviceaccount.com" \
  --permission="compute.instances.get" \
  --request-time="2026-08-22T16:59:59Z"
```

Expected result:

```text
overallAccessState: UNKNOWN_INFO
```

More importantly, inspect the condition evaluation:

```yaml
conditionExplanation:
  evaluationStates:
  - end: 48
    value: true
  value: true
```

And the binding:

```yaml
membership: MEMBERSHIP_MATCHED
```

The conditional binding itself is therefore evaluated as granted.

The top-level `UNKNOWN_INFO` result is related to deny-policy evaluation not being fully determined by the troubleshooter output:

```text
denyAccessState: DENY_ACCESS_STATE_UNKNOWN_INFO
```

For this lab, the critical evidence is that the IAM Condition evaluates to:

```text
value: true
```

and the conditional binding is:

```text
ALLOW_ACCESS_STATE_GRANTED
```

---

# 12. Test Access Exactly at Expiration

Now test at the exact expiry timestamp:

```bash
gcloud policy-intelligence troubleshoot-policy iam \
  "//compute.googleapis.com/projects/dev-project-506017/zones/asia-south1-a/instances/iam-condition-test-vm" \
  --principal-email="iam-condition-test@dev-project-506017.iam.gserviceaccount.com" \
  --permission="compute.instances.get" \
  --request-time="2026-08-22T17:00:00Z"
```

Expected condition evaluation:

```yaml
conditionExplanation:
  evaluationStates:
  - end: 48
    value: false
  value: false
```

And:

```text
membership: MEMBERSHIP_MATCHED
```

but:

```text
ALLOW_ACCESS_STATE_NOT_GRANTED
```

The overall result was:

```text
overallAccessState: CANNOT_ACCESS
```

This is the strongest evidence that the time-based IAM Condition successfully denied access at the expiration boundary.

---

# 13. Test Access After Expiration

A test after expiration was also performed:

```bash
gcloud policy-intelligence troubleshoot-policy iam \
  "//compute.googleapis.com/projects/dev-project-506017/zones/asia-south1-a/instances/iam-condition-test-vm" \
  --principal-email="iam-condition-test@dev-project-506017.iam.gserviceaccount.com" \
  --permission="compute.instances.get" \
  --request-time="2026-08-23T17:00:00Z"
```

Expected condition result:

```yaml
value: false
```

and:

```text
overallAccessState: CANNOT_ACCESS
```

This confirms that the conditional binding does not grant access after the expiration timestamp.

---

# 14. Condition Boundary Test Summary

| Request Time | Condition | Conditional Binding | Overall Result |
|---|---:|---|---|
| Before `2026-08-22T17:00:00Z` | `true` | Granted | `UNKNOWN_INFO` due to deny-policy uncertainty |
| Exactly `2026-08-22T17:00:00Z` | `false` | Not granted | `CANNOT_ACCESS` |
| After expiration | `false` | Not granted | `CANNOT_ACCESS` |

The most important security observation is:

```text
request.time < expiration
```

is a strict comparison.

Therefore:

```text
16:59:59 < 17:00:00  → TRUE
17:00:00 < 17:00:00  → FALSE
17:00:01 < 17:00:00  → FALSE
```

---

# 15. What This Lab Demonstrates

This lab demonstrates **context-aware IAM authorization**.

Instead of granting:

```text
Service Account → roles/compute.viewer → Project
```

unconditionally, the authorization becomes:

```text
Service Account
       |
       v
roles/compute.viewer
       |
       v
Condition:
request.time < expiration
       |
       v
Compute VM
```

The role is therefore only effective when the IAM Condition evaluates to `true`.

---

# 16. IAM Condition Logic

The expression used:

```text
request.time < timestamp("2026-08-22T17:00:00Z")
```

uses the IAM Conditions Common Expression Language (CEL).

Conceptually:

```text
IF request.time < expiration_time
    THEN grant the permissions from roles/compute.viewer
ELSE
    do not grant the permissions from this binding
```

The important distinction is:

> The IAM role still exists, but its binding is conditionally effective.

---

# 17. Why Policy Troubleshooter Is Important

Policy Troubleshooter allows us to answer a precise authorization question:

```text
Can principal X perform permission Y on resource Z under this request context?
```

In this lab:

```text
Principal:
iam-condition-test@dev-project-506017.iam.gserviceaccount.com

Permission:
compute.instances.get

Resource:
//compute.googleapis.com/projects/dev-project-506017/zones/asia-south1-a/instances/iam-condition-test-vm
```

The request context includes:

```text
request.time
```

which allows the IAM Condition to be evaluated.

This makes Policy Troubleshooter useful for validating complex authorization behavior before relying on production access tests.

---

# 18. Evidence Collected

## Evidence 1 — Test Service Account

```text
iam-condition-test@dev-project-506017.iam.gserviceaccount.com
```

Created specifically for conditional-access testing.

## Evidence 2 — Test VM

```text
iam-condition-test-vm
```

Zone:

```text
asia-south1-a
```

## Evidence 3 — IAM Conditional Binding

```text
ROLE:
roles/compute.viewer

TITLE:
Temporary-Compute-Viewer

EXPRESSION:
request.time < timestamp("2026-08-22T17:00:00Z")

DESCRIPTION:
Temporary access for IAM Conditions lab
```

## Evidence 4 — Before Expiration

At:

```text
2026-08-22T16:59:59Z
```

Condition:

```text
true
```

Conditional binding:

```text
ALLOW_ACCESS_STATE_GRANTED
```

## Evidence 5 — At Expiration

At:

```text
2026-08-22T17:00:00Z
```

Condition:

```text
false
```

Overall access:

```text
CANNOT_ACCESS
```

## Evidence 6 — After Expiration

At:

```text
2026-08-23T17:00:00Z
```

Condition:

```text
false
```

Overall access:

```text
CANNOT_ACCESS
```

---

# 19. Key IAM Security Lessons

### 19.1 Least Privilege

The test principal receives only:

```text
roles/compute.viewer
```

instead of a broader administrative role.

### 19.2 Time-Bound Access

The role is available only until:

```text
2026-08-22T17:00:00Z
```

This is useful for:

- Temporary administrative access
- Incident response
- Vendor access
- Break-glass workflows
- Short-lived project access
- Maintenance windows

### 19.3 Context-Aware Authorization

IAM Conditions allow authorization to depend on request context such as:

```text
request.time
resource.name
resource.type
principal
destination
```

depending on the supported condition attributes for the relevant service and authorization path.

### 19.4 Authorization Is Dynamic

The principal does not permanently receive the effective permissions of the role.

Instead:

```text
Role + Principal + Request Context + Condition
                         |
                         v
                 Authorization Decision
```

---

# 20. Interview-Level Explanation

A concise explanation of the lab:

> I implemented a time-bound GCP IAM binding for a dedicated service account using IAM Conditions. The service account received `roles/compute.viewer`, but only while `request.time` was before a specified expiration timestamp. I used Policy Troubleshooter with an explicit request time to validate the authorization boundary. At `16:59:59Z`, the condition evaluated to true and the conditional binding was granted. At exactly `17:00:00Z` and after expiration, the condition evaluated to false and access was denied. This demonstrated contextual, least-privilege authorization rather than unconditional role assignment.

---

# 21. Useful Commands

## View project IAM policy

```bash
gcloud projects get-iam-policy dev-project-506017
```

## View only the test principal's conditional binding

```bash
gcloud projects get-iam-policy dev-project-506017 \
  --flatten="bindings[]" \
  --filter="bindings.members:iam-condition-test@dev-project-506017.iam.gserviceaccount.com" \
  --format="table(bindings.role,bindings.condition.title,bindings.condition.expression,bindings.condition.description)"
```

## List Compute instances

```bash
gcloud compute instances list
```

## Describe the test service account

```bash
gcloud iam service-accounts describe \
  iam-condition-test@dev-project-506017.iam.gserviceaccount.com
```

## Test conditional access before expiration

```bash
gcloud policy-intelligence troubleshoot-policy iam \
  "//compute.googleapis.com/projects/dev-project-506017/zones/asia-south1-a/instances/iam-condition-test-vm" \
  --principal-email="iam-condition-test@dev-project-506017.iam.gserviceaccount.com" \
  --permission="compute.instances.get" \
  --request-time="2026-08-22T16:59:59Z"
```

## Test access at expiration

```bash
gcloud policy-intelligence troubleshoot-policy iam \
  "//compute.googleapis.com/projects/dev-project-506017/zones/asia-south1-a/instances/iam-condition-test-vm" \
  --principal-email="iam-condition-test@dev-project-506017.iam.gserviceaccount.com" \
  --permission="compute.instances.get" \
  --request-time="2026-08-22T17:00:00Z"
```

## Test access after expiration

```bash
gcloud policy-intelligence troubleshoot-policy iam \
  "//compute.googleapis.com/projects/dev-project-506017/zones/asia-south1-a/instances/iam-condition-test-vm" \
  --principal-email="iam-condition-test@dev-project-506017.iam.gserviceaccount.com" \
  --permission="compute.instances.get" \
  --request-time="2026-08-23T17:00:00Z"
```

---

# 22. Cleanup

The lab resources should be removed after evidence has been captured.

## Remove the conditional IAM binding

Use the same condition definition:

```bash
gcloud projects remove-iam-policy-binding dev-project-506017 \
  --member="serviceAccount:iam-condition-test@dev-project-506017.iam.gserviceaccount.com" \
  --role="roles/compute.viewer" \
  --condition='expression=request.time < timestamp("2026-08-22T17:00:00Z"),title=Temporary-Compute-Viewer,description=Temporary access for IAM Conditions lab'
```

Verify:

```bash
gcloud projects get-iam-policy dev-project-506017 \
  --flatten="bindings[]" \
  --filter="bindings.members:iam-condition-test@dev-project-506017.iam.gserviceaccount.com" \
  --format="table(bindings.role,bindings.condition.title,bindings.condition.expression)"
```

The conditional `roles/compute.viewer` binding should no longer appear.

## Delete the test VM

```bash
gcloud compute instances delete iam-condition-test-vm \
  --zone=asia-south1-a
```

Confirm when prompted.

## Delete the test service account

```bash
gcloud iam service-accounts delete \
  iam-condition-test@dev-project-506017.iam.gserviceaccount.com
```

Confirm when prompted.

---

# 23. Final Lab Status

```text
[✓] Created dedicated test service account
[✓] Created Compute Engine test VM
[✓] Enabled Policy Troubleshooter
[✓] Implemented IAM Condition
[✓] Verified conditional IAM binding
[✓] Tested access before expiration
[✓] Tested access at expiration
[✓] Tested access after expiration
[✓] Captured condition evaluation evidence
[✓] Demonstrated contextual authorization
```

## Deliverable

**Condition tests completed successfully.**

The lab proves that a GCP IAM role can be made effective only when a contextual condition evaluates to `true`, providing a practical implementation of time-bound, least-privilege access.
