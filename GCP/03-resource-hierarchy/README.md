# GCP Resource Hierarchy

## Objective

Understand GCP resource organization and IAM policy inheritance.

## Hierarchy

Organization
    ↓
Folder (optional)
    ↓
Project
    ↓
Resources

## Key Concepts

* **Organization** — Top-level resource container.
* **Folder** — Optional grouping of projects.
* **Project** — Core boundary for resources, IAM, APIs, and billing.
* **Resources** — Compute, Storage, BigQuery, Cloud Run, etc.

## IAM Inheritance

IAM policies can be applied at different hierarchy levels:

Organization
    ↓
Folder
    ↓
Project
    ↓
Resource
```

Policies granted at a parent level can be inherited by descendant resources.

## Engineering Takeaways

* Higher-level IAM policies provide centralized access control.
* Broad permissions at higher levels increase blast radius.
* Project separation can provide useful isolation boundaries.
* Troubleshooting access requires checking inherited policies.

## References

* [GCP Resource Hierarchy](https://docs.cloud.google.com/resource-manager/docs/cloud-platform-resource-hierarchy)
* [IAM Resource Hierarchy](https://docs.cloud.google.com/iam/docs/resource-hierarchy-access-control)
