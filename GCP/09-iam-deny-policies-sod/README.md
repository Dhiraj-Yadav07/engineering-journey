# GCP Governance Lab — Deny Policies & Separation of Duties

## Lab Overview

| Field | Details |
|---|---|
| **Focus** | GCP Governance |
| **Task** | Implement Deny Policy concepts and Separation of Duties |
| **Type** | Lab |
| **Project** | `dev-project-506017` |
| **Project Number** | `229836775022` |
| **Folder** | `980279307111` |
| **Organization** | `865766687674` |
| **Primary administrator** | `dhirajy076@gmail.com` |
| **Deny Policy administrator** | `research.briefs07@gmail.com` |
| **Deny Policy** | `deny-vm-delete` |
| **Target principal** | `iam-lab-observer@dev-project-506017.iam.gserviceaccount.com` |
| **Target permission** | `compute.googleapis.com/instances.delete` |

---

## 1. Objective

This lab demonstrates two important GCP governance concepts:

1. **Separation of Duties (SoD)** — normal project administration and Deny Policy administration are assigned to different identities.
2. **IAM Deny Policy** — explicitly deny a sensitive permission for a specific principal, even when that principal has an Allow role containing the permission.

The lab intentionally uses a service account with Compute administration permissions as the target principal and applies a Deny Policy preventing that principal from deleting Compute Engine instances.

---

## 2. Governance Architecture

```text
Organization: 865766687674
│
├── Primary administrator
│   └── dhirajy076@gmail.com
│       └── Project Owner
│
├── Governance administrator
│   └── research.briefs07@gmail.com
│       └── roles/iam.denyAdmin
│
└── Folder: 980279307111
    │
    └── Project: dev-project-506017
        │
        ├── iam-lab-observer
        │   ├── custom: computeInstanceObserver
        │   └── roles/compute.instanceAdmin.v1
        │
        └── Deny Policy: deny-vm-delete
            └── DENY compute.googleapis.com/instances.delete
                for iam-lab-observer
```

The Organization-level `roles/iam.denyAdmin` binding was verified after cleanup and contains only `research.briefs07@gmail.com`.

---

## 3. Environment Verification

The project was confirmed to be inside the lab Organization hierarchy.

```bash
gcloud projects describe dev-project-506017 --format="yaml(projectId,parent)"
```

Evidence:

```text
parent:
  id: '980279307111'
  type: folder
projectId: dev-project-506017
```

Folder verification:

```bash
gcloud resource-manager folders describe 980279307111 --format="yaml(name,parent)"
```

Evidence:

```text
name: folders/980279307111
parent: organizations/865766687674
```

---

## 4. Deny Policy Administration — Separation of Duties

### Initial finding

The primary project administrator did not have `roles/iam.denyAdmin` at the project level.

The built-in role was inspected:

```bash
gcloud iam roles describe roles/iam.denyAdmin
```

The role includes permissions such as:

```text
iam.denypolicies.create
iam.denypolicies.delete
iam.denypolicies.get
iam.denypolicies.list
iam.denypolicies.update
```

The role is specifically intended to administer IAM Deny Policies.

### Dedicated governance identity

A separate human identity was granted:

```text
roles/iam.denyAdmin
```

at Organization `865766687674`:

```text
research.briefs07@gmail.com
```

Final verification:

```bash
gcloud organizations get-iam-policy 865766687674 \
  --flatten="bindings[].members" \
  --filter="bindings.role:roles/iam.denyAdmin" \
  --format="table(bindings.role,bindings.members)"
```

Evidence:

```text
ROLE: roles/iam.denyAdmin
MEMBERS: user:research.briefs07@gmail.com
```

This demonstrates the intended Separation of Duties boundary:

```text
dhirajy076@gmail.com
    └── Project administration

research.briefs07@gmail.com
    └── Deny Policy administration
```

A temporary `deny-policy-admin` service account was created during troubleshooting but its Organization-level `roles/iam.denyAdmin` binding was removed during cleanup.

---

## 5. Target Service Account

The lab observer service account was:

```text
iam-lab-observer@dev-project-506017.iam.gserviceaccount.com
```

Verification:

```bash
gcloud iam service-accounts describe \
  iam-lab-observer@dev-project-506017.iam.gserviceaccount.com
```

The service account was intentionally assigned:

```text
projects/dev-project-506017/roles/computeInstanceObserver
roles/compute.instanceAdmin.v1
```

Verification:

```bash
gcloud projects get-iam-policy dev-project-506017 \
  --flatten="bindings[].members" \
  --filter="bindings.members:iam-lab-observer@dev-project-506017.iam.gserviceaccount.com" \
  --format="table(bindings.role)"
```

Evidence:

```text
ROLE: projects/dev-project-506017/roles/computeInstanceObserver

ROLE: roles/compute.instanceAdmin.v1
```

The second role provides the underlying Compute Engine permissions needed to make the Deny Policy meaningful as an explicit governance restriction.

---

## 6. Deny Policy Definition

The final policy file used was:

```json
{
  "displayName": "Deny VM deletion for lab observer",
  "rules": [
    {
      "denyRule": {
        "deniedPrincipals": [
          "principal://iam.googleapis.com/projects/-/serviceAccounts/iam-lab-observer@dev-project-506017.iam.gserviceaccount.com"
        ],
        "deniedPermissions": [
          "compute.googleapis.com/instances.delete"
        ]
      }
    }
  ]
}
```

The initial policy file contained unsupported fields at the wrong level and was rejected by the API. The policy was corrected to the valid `denyRule` structure before creation.

---

## 7. Create the Deny Policy

The dedicated Deny Policy administrator authenticated as:

```text
research.briefs07@gmail.com
```

Initial policy listing returned no policies:

```bash
gcloud iam policies list \
  --kind=denypolicies \
  --attachment-point=cloudresourcemanager.googleapis.com/projects/dev-project-506017
```

Evidence:

```text
{}
```

The policy was then created:

```bash
gcloud iam policies create deny-vm-delete \
  --attachment-point=cloudresourcemanager.googleapis.com/projects/dev-project-506017 \
  --kind=denypolicies \
  --policy-file=deny-delete-vm.json
```

Creation was accepted:

```text
Create in progress for denyPolicy
[policies/cloudresourcemanager.googleapis.com%2Fprojects%2F229836775022/denypolicies/deny-vm-delete/operations/...]
```

---

## 8. Verify Deny Policy Existence

```bash
gcloud iam policies list \
  --kind=denypolicies \
  --attachment-point=cloudresourcemanager.googleapis.com/projects/dev-project-506017
```

Evidence:

```text
policies:
- createTime: '2026-08-22T11:05:00.607983Z'
  displayName: Deny VM deletion for lab observer
  kind: DenyPolicy
  name: policies/cloudresourcemanager.googleapis.com%2Fprojects%2F229836775022/denypolicies/deny-vm-delete
  uid: ea0faaec-dfe0-5183-66c1-7778c0be209a
  updateTime: '2026-08-22T11:05:00.607983Z'
```

---

## 9. Inspect the Final Deny Rule

```bash
gcloud iam policies get deny-vm-delete \
  --attachment-point=cloudresourcemanager.googleapis.com/projects/dev-project-506017 \
  --kind=denypolicies
```

Final policy evidence:

```text
displayName: Deny VM deletion for lab observer
kind: DenyPolicy

rules:
- denyRule:
    deniedPermissions:
    - compute.googleapis.com/instances.delete
    deniedPrincipals:
    - principal://iam.googleapis.com/projects/-/serviceAccounts/iam-lab-observer@dev-project-506017.iam.gserviceaccount.com
```

This is the core governance control:

```text
Principal:
iam-lab-observer@

        ↓

DENY

compute.googleapis.com/instances.delete
```

---

## 10. Governance Test — Allow vs Deny

The target service account had:

```text
roles/compute.instanceAdmin.v1
```

which supplies the underlying Compute Engine permissions.

The Deny Policy explicitly blocks:

```text
compute.googleapis.com/instances.delete
```

Therefore, the intended authorization model is:

```text
ALLOW
roles/compute.instanceAdmin.v1
        │
        ▼
Compute instance deletion capability
        │
        ▼
DENY POLICY
        │
        ▼
compute.googleapis.com/instances.delete
        │
        ▼
BLOCKED
```

This demonstrates the governance concept of using an explicit Deny control to constrain a principal that otherwise possesses an Allow role.

---

## 11. Disposable Runtime Test

A temporary test VM was created:

```bash
gcloud compute instances create deny-policy-test-vm \
  --zone=asia-south1-a \
  --machine-type=e2-micro
```

Creation evidence:

```text
NAME: deny-policy-test-vm
ZONE: asia-south1-a
MACHINE_TYPE: e2-micro
STATUS: RUNNING
```

Verification:

```bash
gcloud compute instances describe deny-policy-test-vm \
  --zone=asia-south1-a \
  --format="value(name,status)"
```

Evidence:

```text
deny-policy-test-vm     RUNNING
```

An attempt was then made to execute the deletion as the target service account using impersonation.

The impersonation request failed before the Compute deletion request reached the authorization evaluation:

```text
PERMISSION_DENIED: Failed to impersonate
[iam-lab-observer@dev-project-506017.iam.gserviceaccount.com]

Permission 'iam.serviceAccounts.getAccessToken' denied
```

A temporary Token Creator binding was added for this test and subsequently removed.

### Important Evidence Qualification

The runtime deletion test **was not successfully completed** because service-account impersonation was blocked.

Therefore, this lab does **not** claim a successful runtime `PERMISSION_DENIED` response from the Deny Policy itself.

What was successfully demonstrated and verified:

- Separation of Duties
- Dedicated Deny Policy administrator
- Valid Deny Policy configuration
- Correct project attachment
- Correct denied principal
- Correct denied permission
- Target principal's existing Allow role
- Cleanup of temporary test access

---

## 12. Cleanup

The temporary test VM was deleted successfully.

Final verification:

```bash
gcloud compute instances list --filter="name=deny-policy-test-vm"
```

Evidence:

```text
Listed 0 items.
```

The temporary Token Creator binding granted to:

```text
dhirajy076@gmail.com
```

on `iam-lab-observer` was also removed.

Verification produced no matching binding.

The temporary `deny-policy-admin` service account's Organization-level `roles/iam.denyAdmin` binding was removed.

Final Organization-level Deny Admin verification:

```bash
gcloud organizations get-iam-policy 865766687674 \
  --flatten="bindings[].members" \
  --filter="bindings.role:roles/iam.denyAdmin" \
  --format="table(bindings.role,bindings.members)"
```

Final evidence:

```text
ROLE: roles/iam.denyAdmin
MEMBERS: user:research.briefs07@gmail.com
```

This confirms that the final governance administrator is the intended dedicated human identity.

---

## 13. Final Lab State

```text
Organization: 865766687674
│
├── Primary administrator
│   └── dhirajy076@gmail.com
│       └── Project administration
│
├── Governance administrator
│   └── research.briefs07@gmail.com
│       └── roles/iam.denyAdmin
│
└── Project: dev-project-506017
    │
    ├── iam-lab-observer@
    │   ├── computeInstanceObserver
    │   └── roles/compute.instanceAdmin.v1
    │
    └── deny-vm-delete
        └── DENY
            ├── Principal:
            │   iam-lab-observer@
            │
            └── Permission:
                compute.googleapis.com/instances.delete
```

---

## 14. Evidence Summary

| Control / Test | Result |
|---|---|
| Project identified under Organization hierarchy | ✅ |
| Dedicated Deny Policy administrator | ✅ |
| `roles/iam.denyAdmin` assigned at Organization | ✅ |
| Primary project administrator separated from Deny administration | ✅ |
| Target service account identified | ✅ |
| Target service account has Compute Admin Allow role | ✅ |
| Deny Policy created | ✅ |
| Deny Policy attached to project | ✅ |
| Correct denied principal | ✅ |
| Correct denied permission | ✅ |
| Disposable VM created | ✅ |
| Runtime impersonation/deletion test | ⚠️ Not completed |
| Temporary Token Creator permission removed | ✅ |
| Test VM removed | ✅ |
| Temporary Deny Admin service account binding removed | ✅ |
| Final Deny Admin state verified | ✅ |

---

## 15. Key Governance Takeaways

### Separation of Duties

Do not give every administrator unrestricted control over both IAM grants and governance restrictions.

A dedicated governance identity can administer Deny Policies while the normal project administrator retains project-level operational responsibilities.

### Deny as a Guardrail

An IAM Deny Policy can be used as a preventive guardrail around sensitive permissions.

In this lab:

```text
compute.googleapis.com/instances.delete
```

was explicitly denied for a specific service account.

### Least Privilege

The Deny Policy targets one principal and one sensitive permission instead of broadly denying Compute operations.

### Evidence-Based Governance

The lab captures:

- IAM role assignments
- Organization-level governance assignment
- Deny Policy definition
- Deny Policy attachment
- Denied principal
- Denied permission
- Cleanup state
- Runtime-test limitation

This provides a reproducible governance evidence trail suitable for a security engineering portfolio.

---

## 16. Lessons Learned

1. `gcloud iam policies` uses `--kind=denypolicies` for Deny Policies.
2. Deny Policies are attached to supported resource attachment points rather than managed through the normal `gcloud projects get-iam-policy` IAM policy view.
3. `roles/iam.denyAdmin` is the relevant administrative role for creating and managing Deny Policies.
4. Organization-level IAM can be used to establish Separation of Duties.
5. A valid Deny Policy uses a `denyRule` containing `deniedPrincipals` and `deniedPermissions`.
6. Service-account impersonation requires appropriate token-generation permissions and can introduce a separate authorization dependency when performing runtime tests.
7. Temporary test permissions should always be removed after validation.
8. Governance evidence should distinguish between **policy configuration evidence** and **runtime enforcement evidence**.

---

## Conclusion

This lab successfully implemented and documented a GCP governance model combining:

- **IAM Deny Policies**
- **Separation of Duties**
- **Least Privilege**
- **Explicit authorization guardrails**
- **Evidence-based policy verification**
- **Temporary access cleanup**

The final environment retains the intended Deny Policy and dedicated governance administrator while removing temporary test access and resources.

**Lab status: COMPLETED — Governance policy configuration and SoD evidence verified. Runtime enforcement test not completed due to service-account impersonation limitations.**
