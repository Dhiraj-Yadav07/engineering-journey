# GCP IAM — Concept Note

## Objective

Understand how Google Cloud IAM controls **who can perform what actions on which resources**.

---

## 1. Principal

A **principal** is an identity that can be granted access to a GCP resource.

Examples:

* Google user
* Google group
* Service account
* Workforce/Workload identity

Example:

```text
developer@example.com
```

The principal represents **who** is requesting access.

---

## 2. Permission

A **permission** represents a specific operation that can be performed on a resource.

Examples:

```text
compute.instances.get
compute.instances.start
storage.objects.get
resourcemanager.projects.get
```

A permission answers:

> **What can be done?**

Permissions are generally not granted directly to users. They are included in roles.

---

## 3. Role

A **role** is a collection of permissions.

Example:

```text
roles/storage.objectViewer
```

may contain permissions that allow a principal to view objects in Cloud Storage.

Conceptually:

```text
Role
 |
 +-- Permission A
 +-- Permission B
 +-- Permission C
```

### Types of roles

**Basic roles**

```text
Owner
Editor
Viewer
```

**Predefined roles**

Google-managed roles designed for specific services and use cases.

Examples:

```text
roles/storage.objectViewer
roles/compute.viewer
roles/securityReviewer
```

**Custom roles**

Roles created with a specific set of permissions for an organization's requirements.

---

## 4. IAM Policy

An **IAM policy** defines which principals receive which roles on a resource.

Conceptually:

```text
Principal
    +
Role
    ↓
IAM Policy
    ↓
Resource
```

Example:

```text
developer@example.com
        ↓
roles/storage.objectViewer
        ↓
Cloud Storage Bucket
```

This means the developer is granted the permissions contained in
`roles/storage.objectViewer` for that bucket.

---

## 5. IAM Authorization Model

A useful mental model is:

```text
Principal
    ↓
IAM Policy
    ↓
Role
    ↓
Permissions
    ↓
Resource
```

When a principal makes an API request:

```text
User
 ↓
API Request
 ↓
IAM Authorization
 ↓
Allowed / Denied
 ↓
Resource Operation
```

Example:

```text
developer@example.com
        ↓
storage.objects.get
        ↓
IAM evaluation
        ↓
Cloud Storage object
```

If the required permission is granted through an applicable role,
the operation can be authorized.

---

## 6. IAM Policy Inheritance

GCP resources are organized hierarchically:

```text
Organization
    ↓
Folder
    ↓
Project
    ↓
Resource
```

IAM policies can be applied at different levels.

```text
Organization Policy
        ↓
Folder Policy
        ↓
Project Policy
        ↓
Resource Policy
```

A policy granted at a parent level can be inherited by descendant
resources.

### Example

```text
Engineering Folder
       |
       +-- Project-A
       |
       +-- Project-B
```

If a principal receives:

```text
roles/viewer
```

at the **Engineering Folder** level, the access can apply to
Project-A and Project-B through inheritance.

---

## 7. Inheritance and Blast Radius

Higher-level permissions can affect a larger number of resources.

```text
Organization
    ↓
Many Folders
    ↓
Many Projects
    ↓
Many Resources
```

Therefore:

```text
Higher-level IAM binding
        ↓
Larger potential blast radius
```

Example:

```text
Organization
    ↓
roles/editor
    ↓
Principal
```

can provide extremely broad access.

A more restrictive approach may be:

```text
Project-A
    ↓
Specific predefined role
    ↓
Principal
```

This supports the principle of **least privilege**.

---

## 8. Complete Example

### Scenario

A developer needs to read objects from a production bucket.

```text
Principal:
developer@example.com

Role:
roles/storage.objectViewer

Resource:
prod-data-bucket
```

Authorization model:

```text
developer@example.com
        ↓
roles/storage.objectViewer
        ↓
storage.objects.get
        ↓
prod-data-bucket
```

The developer can perform operations covered by the role's
permissions, without requiring broad project-level access.

---

## 9. Key Takeaways

| Concept     | Meaning                                     |
| ----------- | ------------------------------------------- |
| Principal   | **Who** is requesting access                |
| Permission  | **What operation** can be performed         |
| Role        | Collection of permissions                   |
| Policy      | Binds principals to roles                   |
| Resource    | **Where** access applies                    |
| Inheritance | Parent-level access can flow to descendants |

### Mental Model

```text
WHO
 ↓
Principal
 ↓
GETS WHICH ROLE
 ↓
CONTAINS WHICH PERMISSIONS
 ↓
ON WHICH RESOURCE
 ↓
THROUGH WHICH POLICY / INHERITANCE
```

## Engineering Takeaways

* IAM is an **authorization system**, not an authentication system.
* Roles provide reusable permission sets.
* Policies establish principal-to-role bindings.
* IAM can be applied at multiple resource hierarchy levels.
* Parent-level permissions can increase the potential blast radius.
* Prefer granular roles and least-privilege access over broad permissions.
* When troubleshooting access, check both direct and inherited IAM policies.

## References

* [Google Cloud IAM Overview](https://docs.cloud.google.com/iam/docs/overview)
* [Google Cloud IAM Documentation](https://docs.cloud.google.com/iam/docs)
* [IAM Resource Hierarchy](https://docs.cloud.google.com/iam/docs/resource-hierarchy-access-control)
