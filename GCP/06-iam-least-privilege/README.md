# GCP IAM — Least Privilege

## Objective

Implement GCP IAM using predefined roles, custom roles, and least-privilege access.

## What I Built

- Assigned the predefined `Compute Viewer` role.
- Created a custom role: `GCP Compute Instance Observer`.
- Limited the custom role to:
  - `compute.instances.get`
  - `compute.instances.list`
- Created a dedicated service account: `iam-lab-observer`.
- Assigned only the custom role to the service account.
- Documented the IAM role matrix and policy evidence.
- Designed a group-based IAM model.

## IAM Model

Principal
↓
IAM Policy Binding
↓
Role
↓
Permissions
↓
GCP Resource

## Custom Role

**GCP Compute Instance Observer**

Permissions:

- `compute.instances.get`
- `compute.instances.list`

The role does not include state-changing permissions such as:

- `compute.instances.start`
- `compute.instances.stop`
- `compute.instances.delete`

## Least-Privilege Design

The dedicated service account demonstrates a narrow IAM principal with only the permissions required to inspect Compute Engine instances.

iam-lab-observer
↓
GCP Compute Instance Observer
↓
compute.instances.get
compute.instances.list
↓
dev-project

## Group-Based IAM

Group-based IAM was designed but not implemented because the current GCP organization is not domain-verified and therefore does not support creating Google Cloud Identity groups through the console.

Conceptual model:

Google Group
↓
IAM Role
↓
Non-Production Folder
↓
Projects

## Evidence

### Predefined Role Binding

![Predefined Role Binding](./screenshots/01-predefined-role-binding.png)

### Custom Role Definition

![Custom Role Definition](./screenshots/02-custom-role-definition.png)

### Custom Role Binding

![Custom Role Binding](./screenshots/03-custom-role-binding.png)

### Least-Privilege Service Account

![Least-Privilege Service Account](./screenshots/04-least-privilege-service-account.png)

## Deliverables

- [Role Matrix](./ROLE-MATRIX.md)
- IAM policy evidence
- Custom role definition
- Least-privilege service account configuration

## Key Takeaways

- Predefined roles provide reusable permission sets.
- Custom roles allow granular permission control.
- IAM bindings connect principals to roles at a defined scope.
- Least privilege means granting only the permissions required.
- Dedicated service accounts are useful for narrow workload access.
- Group-based IAM provides a scalable enterprise access model.

## References

- [Google Cloud IAM](https://cloud.google.com/iam/docs)
- [IAM Roles](https://cloud.google.com/iam/docs/roles-overview)
- [Custom IAM Roles](https://cloud.google.com/iam/docs/creating-custom-roles)
- [IAM Best Practices](https://cloud.google.com/iam/docs/best-practices)