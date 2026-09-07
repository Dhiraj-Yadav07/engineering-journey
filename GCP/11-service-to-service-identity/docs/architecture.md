# GCP 11 — Service-to-Service Identity Architecture

## 1. Purpose

This lab implements a secure service-to-service communication pattern using two private Cloud Run services.

The design goal is to ensure that:

- services are not publicly invokable;
- each workload has its own runtime identity;
- the caller authenticates using a Google-signed OIDC ID token;
- the receiver authorizes the caller using Cloud Run IAM;
- no service-account JSON key is required.

## 2. High-Level Architecture

```text
                                      Google Cloud

  ┌────────────────────────┐
  │ Deployment identity    │
  │ dhirajy076@gmail.com   │
  └────────────┬───────────┘
               │
               │ Cloud Run deployment
               ▼
  ┌───────────────────────────────────────────────────────────────┐
  │                         Cloud Run                              │
  │                                                               │
  │   ┌──────────────────────┐          ┌──────────────────────┐  │
  │   │   caller-service     │          │   receiver-service   │  │
  │   │                      │          │                      │  │
  │   │ Runtime SA:          │          │ Runtime SA:          │  │
  │   │ caller-sa            │          │ receiver-sa           │  │
  │   │                      │          │                      │  │
  │   │ auth required        │          │ auth required        │  │
  │   └──────────┬───────────┘          └──────────▲───────────┘  │
  │              │                                 │              │
  └──────────────┼─────────────────────────────────┼──────────────┘
                 │                                 │
                 │ Google-signed OIDC ID token     │
                 │ aud = receiver service URL      │
                 └────────────────────────────────►│
                                                   │
                                      IAM: roles/run.invoker
                                      member: caller-sa
```

## 3. Trust Boundaries

There are three meaningful trust boundaries.

### Boundary A — Deployment

The human deployment identity configures Cloud Run resources. Deployment permissions do not become application runtime permissions.

### Boundary B — Workload Runtime

Each Cloud Run service runs as a dedicated service account:

```text
caller-service   -> caller-sa
receiver-service -> receiver-sa
```

### Boundary C — Receiver Authorization

The receiver's resource IAM policy defines which principals can invoke the service.

```text
caller-sa -> roles/run.invoker -> receiver-service
```

## 4. Authentication Flow

```text
1. caller-service receives a request.
2. caller application reads RECEIVER_URL.
3. caller requests an ID token using Google authentication libraries.
4. Google returns a signed OIDC ID token for the receiver audience.
5. caller sends:

       Authorization: Bearer <token>

6. Cloud Run validates the invocation authentication.
```

The caller does not store a private key or service-account JSON file.

## 5. Authorization Flow

After authentication, Cloud Run evaluates IAM permissions on the receiver service.

Required relationship:

```text
Principal:
  serviceAccount:caller-sa@dev-project-506017.iam.gserviceaccount.com

Permission role:
  roles/run.invoker

Resource:
  receiver-service
```

Conceptually:

```text
OIDC token identifies caller-sa
                │
                ▼
       Cloud Run IAM check
                │
       roles/run.invoker?
          ┌─────┴─────┐
         yes          no
          │            │
          ▼            ▼
        allow         deny
```

## 6. Runtime Identity Model

### Caller

```text
Service:        caller-service
Runtime SA:     caller-sa@dev-project-506017.iam.gserviceaccount.com
Role on receiver: roles/run.invoker
```

### Receiver

```text
Service:        receiver-service
Runtime SA:     receiver-sa@dev-project-506017.iam.gserviceaccount.com
Invocation:     authentication required
```

The receiver's runtime service account is not used as the caller's identity. Each service is independently identified.

## 7. Deployment and Build Identity Model

The lab also encountered a source-build permission issue. This establishes an important separation:

```text
Human/deployer
    │
    └── deploys service

Build identity
    │
    └── builds source-derived container

Runtime identity
    │
    └── executes application code
```

The Compute Engine default service account used by the source build was granted:

```text
roles/run.builder
```

This permission exists to support source deployment and should not be confused with `caller-sa` or `receiver-sa`.

## 8. Network and Exposure Model

Both services are configured with:

```text
--no-allow-unauthenticated
```

Therefore the application endpoints are not public anonymous HTTP endpoints.

The receiver was explicitly tested without credentials and returned:

```text
HTTP/2 403
```

## 9. Security Properties

### Authentication

Google-signed OIDC ID token.

### Token audience

Receiver service URL.

### Authorization

Cloud Run IAM.

### Least-privilege relationship

`caller-sa` receives the Cloud Run Invoker role on the receiver service rather than requiring a broad application-level credential.

### Credential management

No service-account key file is distributed to either application.

### Workload identity

Each service uses a dedicated service account as its runtime principal.

## 10. Sequence Diagram

```text
Caller Service                 Google Auth                 Receiver Service
     │                              │                              │
     │ fetch ID token               │                              │
     ├─────────────────────────────►│                              │
     │                              │                              │
     │ signed OIDC ID token         │                              │
     │◄─────────────────────────────┤                              │
     │                              │                              │
     │ HTTP request + Bearer token  │                              │
     ├──────────────────────────────┼─────────────────────────────►│
     │                              │                              │
     │                              │                      authenticate
     │                              │                              │
     │                              │                      IAM check
     │                              │                      caller-sa?
     │                              │                              │
     │                              │                         allow
     │                              │                              │
     │◄─────────────────────────────┼──────────────────────────────┤
     │                  HTTP 200 / receiver response               │
```

## 11. Failure Cases Tested

### Anonymous request

```text
curl https://receiver-service-...
        │
        ▼
HTTP 403
```

This verifies that the receiver is protected.

### Intended workload request

```text
caller-service
     │
     ▼
caller-sa + OIDC token
     │
     ▼
receiver-service
     │
     ▼
HTTP 200
```

This verifies that the intended workload identity is authorized.

### Human Owner request

The lab user's project-level `roles/owner` permission also allowed direct invocation of the receiver. This is expected IAM inheritance and is documented to avoid overstating the exclusivity of the service-level grant.

## 12. Design Rationale

### Why OIDC ID tokens?

The receiver is an HTTP service on Cloud Run, and the caller needs a verifiable workload identity. A Google-signed OIDC ID token lets the receiver authenticate the caller without requiring a static secret.

### Why separate service accounts?

Separate service accounts provide workload-level identity boundaries. Compromise or misuse of one service identity does not automatically imply use of the other service identity.

### Why resource-level `roles/run.invoker`?

The authorization relationship is between one caller workload and one protected receiver. A resource-level grant expresses that relationship more precisely than a project-wide invoker grant.

### Why keep the receiver private?

Public invocation would bypass the intended IAM authorization boundary. Requiring authentication ensures that the receiver evaluates the caller's identity before allowing the request.

## 13. Final Security Model

```text
                 AUTHENTICATION
                      │
                      ▼
         Google-signed OIDC token
                      │
                      ▼
                caller-sa
                      │
                      │ AUTHORIZATION
                      ▼
             roles/run.invoker
                      │
                      ▼
            receiver-service
                      │
                      ▼
                 receiver-sa
```

## 14. Verification Checklist

```text
[PASS] caller-service deployed
[PASS] receiver-service deployed
[PASS] caller uses caller-sa
[PASS] receiver uses receiver-sa
[PASS] unauthenticated receiver invocation denied
[PASS] receiver grants caller-sa roles/run.invoker
[PASS] caller invokes receiver successfully
[PASS] no service-account JSON key used
[PASS] evidence captured under evidence/
```
