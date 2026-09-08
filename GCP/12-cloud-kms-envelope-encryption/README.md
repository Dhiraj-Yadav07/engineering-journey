# GCP Cloud KMS Envelope Encryption Lab

## Overview

This lab demonstrates a practical Google Cloud Key Management Service (Cloud KMS) design and implementation for application-level envelope encryption.

The implementation uses:

- Cloud KMS as the Key Encryption Key (KEK) protection layer
- A locally generated 256-bit Data Encryption Key (DEK)
- AES-256-GCM for application data encryption
- Cloud KMS `Encrypt`/`Decrypt` operations to wrap and unwrap the DEK
- A dedicated service account with least-privilege KMS permissions
- Cloud KMS key versions and manual rotation
- Verification that ciphertext encrypted under an older key version remains decryptable after rotation

The goal is to gain hands-on experience operating a real KMS-backed encryption flow rather than only studying cryptographic concepts.

## Security Objective

Implement a key-management pattern in which application data is encrypted locally with a short-lived DEK, while the DEK is protected by a centrally managed Cloud KMS key.

The application never receives or stores the underlying KMS key material.

## Architecture

```text
                         Google Cloud KMS
                              |
                         app-keyring
                              |
                    data-encryption-key
                              |
                    +---------+---------+
                    |                   |
                  v1 ENABLED        v2 ENABLED
                                      PRIMARY
                    |                   |
                    +---------+---------+
                              |
                         wraps / unwraps
                              |
                              v
                   kms-demo-sa application
                              |
                +-------------+-------------+
                |                           |
          Generate DEK                 Plaintext
                |                           |
                |                    AES-256-GCM
                |                           |
                |                           v
                |                      Ciphertext
                |                           +
                +---- KMS wraps DEK -------+
                              |
                         Wrapped DEK
```

See [`architecture.md`](architecture.md) for the detailed design and trust boundaries.

## KMS Resource Hierarchy

The lab uses the following hierarchy:

```text
Project: dev-project-506017
└── Location: asia-south1
    └── Key Ring: app-keyring
        └── CryptoKey: data-encryption-key
            ├── CryptoKeyVersion: 1
            └── CryptoKeyVersion: 2 (PRIMARY)
```

The CryptoKey is the logical key-management object. Key versions represent individual versions of the cryptographic material.

## Key Configuration

| Property | Value |
|---|---|
| Project | `dev-project-506017` |
| Region | `asia-south1` |
| Key ring | `app-keyring` |
| CryptoKey | `data-encryption-key` |
| Purpose | `ENCRYPT_DECRYPT` |
| Algorithm | `GOOGLE_SYMMETRIC_ENCRYPTION` |
| Protection level | `SOFTWARE` |
| Initial primary version | `1` |
| Current primary version | `2` |

## IAM Model

The application uses a dedicated service account:

```text
kms-demo-sa@dev-project-506017.iam.gserviceaccount.com
```

It has the following permission on the CryptoKey:

```text
roles/cloudkms.cryptoKeyEncrypterDecrypter
```

The grant is scoped directly to the CryptoKey rather than broadly granting KMS permissions at the project level.

The service account does not receive KMS administration privileges.

## Envelope Encryption Flow

### Encryption

1. The application generates a fresh 256-bit DEK locally.
2. The DEK encrypts the plaintext locally using AES-256-GCM.
3. Cloud KMS wraps the DEK using the current primary version of `data-encryption-key`.
4. The application can persist the ciphertext, nonce, AAD, wrapped DEK, and KMS key reference.
5. The plaintext DEK is not persisted.

Conceptually:

```text
Plaintext
   |
   | AES-256-GCM + DEK
   v
Ciphertext

DEK
 |
 | Cloud KMS Encrypt
 v
Wrapped DEK
```

### Decryption

1. The application reads the wrapped DEK and encrypted envelope.
2. Cloud KMS unwraps the DEK.
3. The application uses the recovered DEK with AES-256-GCM.
4. The original plaintext is recovered and authenticated.

```text
Wrapped DEK
    |
    | Cloud KMS Decrypt
    v
  DEK
    |
    | AES-256-GCM
    v
Plaintext
```

## AES-256-GCM Parameters Used by the Demo

The Python implementation uses:

- 32-byte random DEK (256 bits)
- 12-byte random nonce for each encryption operation
- Associated Authenticated Data (AAD): `kms-lab:v1`
- AES-GCM authenticated encryption

The nonce is stored with the ciphertext. Reusing a nonce with the same AES-GCM key would be unsafe, so the demo generates a fresh nonce for every encryption.

## Key Rotation Demonstration

The lab deliberately demonstrates rotation in two steps.

### Initial state

```text
CryptoKey
└── v1 ← PRIMARY
```

An envelope is encrypted using v1:

```text
DEK-1 → KMS v1 → Wrapped DEK-1
```

### Rotation

A second key version is created and promoted:

```text
CryptoKey
├── v1 ENABLED
└── v2 ENABLED ← PRIMARY
```

New wrapping operations use v2.

### Existing ciphertext

The original envelope remains associated with v1 and is still decryptable while v1 remains enabled:

```text
Old envelope
     |
     | wrapped under v1
     v
Cloud KMS
     |
     | v1 still enabled
     v
DEK recovered
     |
     v
Original plaintext
```

The lab therefore demonstrates that **changing the primary key version does not automatically re-encrypt existing application ciphertext**.

## Implementation

The project contains two Python programs.

### `app/envelope_demo.py`

Demonstrates the complete envelope-encryption round trip:

```text
Generate DEK
    ↓
AES-256-GCM encrypt
    ↓
Cloud KMS wrap DEK
    ↓
Cloud KMS unwrap DEK
    ↓
AES-256-GCM decrypt
    ↓
Recovered plaintext
```

The application also records the exact KMS CryptoKeyVersion returned by the KMS Encrypt operation.

### `app/decrypt_envelope.py`

Demonstrates that an envelope created under KMS version 1 can still be decrypted after version 2 becomes primary.

## Evidence

The `evidence/` directory contains sanitized evidence captured from the actual GCP environment:

| Evidence | Purpose |
|---|---|
| `encryption-demo.txt` | Successful initial envelope-encryption round trip |
| `kms-iam.txt` | KMS CryptoKey IAM binding for `kms-demo-sa` |
| `kms-key-versions.txt` | KMS key-version state |
| `kms-rotation-state.txt` | Primary-version and key configuration after rotation |
| `rotation-evidence.txt` | Rotation and old-envelope decryption evidence |

No service-account private key is used by the application.

## Setup

### Enable Cloud KMS

```bash
gcloud services enable cloudkms.googleapis.com
```

### Create the key ring

```bash
gcloud kms keyrings create app-keyring \
  --location=asia-south1
```

### Create the CryptoKey

```bash
gcloud kms keys create data-encryption-key \
  --location=asia-south1 \
  --keyring=app-keyring \
  --purpose=encryption
```

### Create the application service account

```bash
gcloud iam service-accounts create kms-demo-sa \
  --project=dev-project-506017 \
  --display-name="KMS Envelope Encryption Demo"
```

### Grant CryptoKey access

```bash
gcloud kms keys add-iam-policy-binding data-encryption-key \
  --location=asia-south1 \
  --keyring=app-keyring \
  --member="serviceAccount:kms-demo-sa@dev-project-506017.iam.gserviceaccount.com" \
  --role="roles/cloudkms.cryptoKeyEncrypterDecrypter"
```

## Run the Demo

Create a virtual environment and install dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r app/requirements.txt
```

Set the environment variables:

```bash
export PROJECT_ID="dev-project-506017"
export REGION="asia-south1"
export KMS_KEYRING="app-keyring"
export KMS_KEY="data-encryption-key"
```

Run:

```bash
python app/envelope_demo.py
```

Expected result:

```text
Generated fresh 256-bit DEK locally.
Encrypted plaintext with AES-256-GCM.
Wrapped DEK using Cloud KMS.
Unwrapped DEK using Cloud KMS.
Decrypted ciphertext locally.

RESULT: Envelope encryption round trip SUCCESS
```

## Rotation Test

Create a new key version:

```bash
gcloud kms keys versions create \
  --location=asia-south1 \
  --keyring=app-keyring \
  --key=data-encryption-key
```

Promote version 2 to primary:

```bash
gcloud kms keys update data-encryption-key \
  --location=asia-south1 \
  --keyring=app-keyring \
  --primary-version=2
```

Verify:

```bash
gcloud kms keys describe data-encryption-key \
  --location=asia-south1 \
  --keyring=app-keyring \
  --format="value(primary.name)"
```

Expected:

```text
.../cryptoKeyVersions/2
```

Then run the decryption demonstration against the existing envelope:

```bash
python app/decrypt_envelope.py
```

Expected result:

```text
Envelope wrapped using: .../cryptoKeyVersions/1
Recovered plaintext: Confidential data for the KMS envelope encryption lab.

RESULT: Previously encrypted envelope successfully decrypted after rotation
```

## Security Properties Demonstrated

### Key isolation

Application plaintext data is encrypted with a locally generated DEK. The KMS-managed KEK remains inside Cloud KMS.

### Least privilege

The application identity receives only the cryptographic permissions required for this demo on the specific CryptoKey.

### Key versioning

Each rotation introduces a new key version without destroying previous versions.

### Safe rotation semantics

The new primary version is used for new wrapping operations, while older enabled versions remain available to process data protected by them.

### Keyless application authentication

No service-account JSON key or long-lived credential is embedded in the application.

## Important Operational Notes

This is a learning lab, not a production key-management platform.

In production, envelope metadata would normally be stored with the encrypted data in a durable datastore and lifecycle requirements would be defined for wrapped DEKs, old key versions, disabling, destruction, access logging, and recovery.

The lab intentionally keeps the scope focused on Cloud KMS design, envelope encryption, IAM, and key rotation.

## Repository Structure

```text
12-cloud-kms-envelope-encryption/
├── README.md
├── architecture.md
├── app/
│   ├── envelope_demo.py
│   ├── decrypt_envelope.py
│   └── requirements.txt
└── evidence/
    ├── encryption-demo.txt
    ├── kms-iam.txt
    ├── kms-key-versions.txt
    ├── kms-rotation-state.txt
    └── rotation-evidence.txt
```

## Result

**Lab status: PASS**

The working demo successfully demonstrated:

- Cloud KMS key hierarchy
- Symmetric CryptoKey configuration
- Dedicated application IAM identity
- AES-256-GCM data encryption
- DEK wrapping and unwrapping with Cloud KMS
- KMS key-version creation
- KMS primary-version rotation
- Decryption of an older envelope after rotation

The final architecture is a practical example of separating **data encryption keys** from centrally managed **key-encryption keys** while preserving least-privilege access to cryptographic operations.
