# GCP 11 — Secure Service-to-Service Identity with Private Cloud Run

## Objective

Implement and verify a secure service-to-service authentication and authorization pattern in Google Cloud using two private Cloud Run services:

- `caller-service` — initiates the request.
- `receiver-service` — exposes a protected HTTP endpoint.
- `caller-sa` — dedicated runtime identity for the caller.
- `receiver-sa` — dedicated runtime identity for the receiver.

The caller obtains a Google-signed OIDC ID token at runtime with the receiver service URL as the token audience and sends it as a Bearer token. The receiver remains private and authorizes `caller-sa` with the Cloud Run Invoker role.

## Security Outcome

The lab demonstrates:

1. Private Cloud Run services with unauthenticated invocation disabled.
2. Dedicated service accounts for each workload.
3. Runtime identity without service-account JSON keys.
4. Google-signed OIDC ID-token authentication between Cloud Run services.
5. Resource-level IAM authorization using `roles/run.invoker`.
6. Successful authenticated service-to-service invocation.
7. Rejection of anonymous access to the receiver.
8. Separation of deployment, build, and runtime identities.

## Architecture

```text
                         Google Cloud

      Deployment identity
      dhirajy076@gmail.com
               |
               | deploys Cloud Run services
               v
  +------------------------+        OIDC ID token        +-------------------------+
  |     caller-service     | --------------------------> |    receiver-service     |
  |       Cloud Run        |                             |        Cloud Run        |
  |                        |                             |                         |
  | Runtime identity:      |                             | Runtime identity:       |
  | caller-sa              |                             | receiver-sa             |
  |                        |                             |                         |
  | fetch_id_token()       |                             | Authentication required |
  | aud = receiver URL     |                             | IAM checks caller-sa    |
  +------------------------+                             +-------------------------+
             |                                                        ^
             |                                                        |
             +---------------- roles/run.invoker ---------------------+
```

## Environment

| Item | Value |
|---|---|
| Project | `dev-project-506017` |
| Project number | `229836775022` |
| Region | `asia-south1` |
| Caller service | `caller-service` |
| Receiver service | `receiver-service` |
| Caller service account | `caller-sa@dev-project-506017.iam.gserviceaccount.com` |
| Receiver service account | `receiver-sa@dev-project-506017.iam.gserviceaccount.com` |

## Identity Model

This lab intentionally distinguishes four identities.

### 1. Deployment identity

```text
dhirajy076@gmail.com
```

This identity executes `gcloud run deploy` and configures the Cloud Run resources.

### 2. Build identity

The source deployment required the Compute Engine default service account:

```text
229836775022-compute@developer.gserviceaccount.com
```

It was granted:

```text
roles/run.builder
```

This is a build/deployment concern, not the runtime identity of either application.

### 3. Caller runtime identity

```text
caller-sa@dev-project-506017.iam.gserviceaccount.com
```

This identity is attached to `caller-service` and is used to obtain the OIDC ID token for the receiver.

### 4. Receiver runtime identity

```text
receiver-sa@dev-project-506017.iam.gserviceaccount.com
```

This identity is attached to `receiver-service` for its application runtime.

## Authentication and Authorization Flow

### Authentication

The caller uses Google authentication libraries to obtain an identity token:

```python
from google.auth.transport.requests import Request
from google.oauth2 import id_token

request = Request()
token = id_token.fetch_id_token(request, RECEIVER_URL)
```

The token is then sent to the receiver:

```text
Authorization: Bearer <Google-signed OIDC ID token>
```

The intended audience is the receiver service URL.

### Authorization

The receiver service IAM policy grants:

```text
caller-sa@dev-project-506017.iam.gserviceaccount.com
    -> roles/run.invoker
    -> receiver-service
```

The receiver therefore does not need to allow unauthenticated invocation.

## Application Implementation

### Receiver

The receiver application exposes a minimal endpoint:

```python
@app.get("/")
def index():
    return "Hello from receiver-service\n"
```

### Caller

The caller:

1. Reads `RECEIVER_URL` from its environment.
2. Requests a Google-signed OIDC ID token for that audience.
3. Sends the token in the `Authorization` header.
4. Returns the receiver's response and status.

## Deployment

Both services were deployed from source with Buildpacks:

```bash
gcloud run deploy receiver-service \
  --source . \
  --region=asia-south1 \
  --service-account=receiver-sa@dev-project-506017.iam.gserviceaccount.com \
  --no-allow-unauthenticated
```

```bash
gcloud run deploy caller-service \
  --source . \
  --region=asia-south1 \
  --service-account=caller-sa@dev-project-506017.iam.gserviceaccount.com \
  --set-env-vars="RECEIVER_URL=$RECEIVER_URL" \
  --no-allow-unauthenticated
```

## IAM Configuration

The receiver has a service-level invoker binding:

```bash
gcloud run services add-iam-policy-binding receiver-service \
  --region=asia-south1 \
  --member="serviceAccount:caller-sa@dev-project-506017.iam.gserviceaccount.com" \
  --role="roles/run.invoker"
```

Verified policy:

```text
bindings:
- members:
  - serviceAccount:caller-sa@dev-project-506017.iam.gserviceaccount.com
  role: roles/run.invoker
```

## Validation Evidence

### 1. Anonymous access to receiver is blocked

```text
HTTP/2 403
Forbidden
```

Evidence file:

```text
evidence/unauthenticated-receiver-test.txt
```

This proves the receiver is not publicly invokable.

### 2. Caller-to-receiver invocation succeeds

```text
HTTP/2 200

Caller invoked receiver.
Receiver HTTP status: 200
Receiver response: Hello from receiver-service
```

Evidence file:

```text
evidence/end-to-end-test.txt
```

This proves the intended authenticated service-to-service path works.

### 3. Runtime identities are correctly attached

Caller:

```text
caller-service
serviceAccountName: caller-sa@dev-project-506017.iam.gserviceaccount.com
```

Receiver:

```text
receiver-service
serviceAccountName: receiver-sa@dev-project-506017.iam.gserviceaccount.com
```

Evidence files:

```text
evidence/caller-service.txt
evidence/receiver-service.txt
```

### 4. Receiver IAM policy is correct

Evidence file:

```text
evidence/receiver-iam.txt
```

## Important IAM Observation

A direct test from the project Owner identity also returned HTTP 200. This is expected because the deploying user has project-level `roles/owner`, which can authorize invocation through inherited permissions.

Therefore, the lab should **not** claim that `caller-sa` is the only identity capable of invoking `receiver-service` in the current project.

The security claims supported by the evidence are:

- anonymous invocation is denied;
- the intended workload identity `caller-sa` can invoke the receiver;
- invocation is controlled by Cloud Run IAM rather than public access;
- each workload has a dedicated runtime service account.

## Failure Analysis: Source Deployment

The first receiver deployment failed during source resolution with a 403 involving the generated `run-sources-*` Cloud Storage bucket. The error identified the Compute Engine default service account as lacking access required for the Cloud Run source build.

The fix was to grant:

```text
roles/run.builder
```

to:

```text
229836775022-compute@developer.gserviceaccount.com
```

After that change, the receiver source deployment completed successfully.

This was a useful demonstration of the distinction between:

```text
Deployment identity != Build identity != Runtime identity
```

## Security Properties

### Achieved

- Private service endpoints.
- Dedicated runtime identities.
- OIDC-based workload authentication.
- IAM-based invocation authorization.
- No service-account JSON keys.
- No static credentials embedded in application source.
- Receiver-specific `roles/run.invoker` binding.

### Not Claimed

This lab does not establish that `caller-sa` is the sole possible invoker because higher-level project IAM grants exist for the lab user.

## Repository Layout

```text
GCP/11-service-to-service-identity/
├── README.md
├── architecture.md
├── app/
│   ├── caller/
│   │   ├── app.py
│   │   └── requirements.txt
│   └── receiver/
│       ├── app.py
│       └── requirements.txt
└── evidence/
    ├── caller-service.txt
    ├── end-to-end-test.txt
    ├── receiver-iam.txt
    ├── receiver-service.txt
    └── unauthenticated-receiver-test.txt
```

## Result

**Status: PASS — working secure service-to-service identity demo.**

The lab demonstrates private-to-private Cloud Run communication using workload identity, Google-signed OIDC authentication, and resource-level IAM authorization without static service-account credentials.
