# Cloud KMS Envelope Encryption — Architecture

## 1. Overview

This lab demonstrates a practical Google Cloud KMS design using envelope encryption.

The application generates a Data Encryption Key (DEK) locally and uses AES-256-GCM to encrypt application data. The DEK is then protected (wrapped) using a Cloud KMS symmetric CryptoKey, acting as the Key Encryption Key (KEK).

The lab also demonstrates KMS key version rotation and proves that ciphertext created with an older key version remains decryptable after a newer version becomes primary.

## 2. High-Level Architecture

```text
                         Google Cloud
┌───────────────────────────────────────────────────────────────────┐
│                                                                   │
│  Cloud KMS                                                        │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │ Location: asia-south1                                     │  │
│  │                                                             │  │
│  │ Key Ring: app-keyring                                      │  │
│  │      │                                                      │  │
│  │      └── CryptoKey: data-encryption-key                    │  │
│  │             ├── Version 1                                  │  │
│  │             └── Version 2  ← PRIMARY after rotation        │  │
│  └─────────────────────────────────────────────────────────────┘  │
│                        ▲                    │                      │
│                        │ wrap / unwrap      │                      │
│                        │                    │                      │
│                   ┌────┴────────────────────┴────┐                │
│                   │      kms-demo-sa              │                │
│                   │ KMS crypto permissions only  │                │
│                   └──────────────┬───────────────┘                │
│                                  │                                │
└──────────────────────────────────┼────────────────────────────────┘
                                   │
                                   │
                         Application / Demo
                         ┌─────────────────────┐
                         │ Generate random DEK │
                         │                     │
                         │ AES-256-GCM         │
                         │ plaintext           │
                         │      ↓              │
                         │ ciphertext           │
                         │                     │
                         │ DEK                  │
                         │      ↓              │
                         │ Cloud KMS            │
                         │      ↓              │
                         │ wrapped DEK          │
                         └─────────────────────┘
```

## 3. Key Hierarchy

The project uses the Cloud KMS resource hierarchy:

```text
Project
└── Location: asia-south1
    └── Key Ring: app-keyring
        └── CryptoKey: data-encryption-key
            ├── CryptoKeyVersion 1
            └── CryptoKeyVersion 2
```

### Key Ring

`app-keyring` is the administrative container for the encryption key.

### CryptoKey

`data-encryption-key` is the logical KMS key used by the application to encrypt and decrypt the DEK.

The CryptoKey is used as the KEK in the envelope-encryption design.

### Key Version

A key version represents a specific version of the cryptographic material.

Initial state:

```text
v1 ← PRIMARY
```

After rotation:

```text
v1 = ENABLED
v2 = ENABLED ← PRIMARY
```

Rotation changes the primary version used for new encryption operations. It does not automatically re-encrypt existing application ciphertext.

## 4. Envelope Encryption Flow

The application performs encryption in two layers.

### Layer 1 — Data Encryption

A fresh 256-bit DEK is generated locally:

```text
DEK = random 32-byte value
```

The plaintext is encrypted locally using AES-256-GCM:

```text
plaintext
   +
DEK
   +
random 12-byte nonce
   +
AAD
   ↓
AES-256-GCM
   ↓
ciphertext
```

### Layer 2 — DEK Protection

The DEK itself is sent to Cloud KMS:

```text
DEK
  ↓
Cloud KMS CryptoKey
  ↓
wrapped DEK
```

The application persists the envelope rather than the plaintext DEK.

Conceptually:

```json
{
  "kms_key": ".../cryptoKeys/data-encryption-key",
  "kms_version_used": ".../cryptoKeyVersions/1",
  "wrapped_dek": "<wrapped DEK>",
  "nonce": "<nonce>",
  "aad": "<AAD>",
  "ciphertext": "<ciphertext>"
}
```

The actual lab envelope was intentionally not committed to Git.

## 5. Decryption Flow

Decryption reverses the process:

```text
wrapped DEK
      │
      ▼
 Cloud KMS
      │
      ▼
 plaintext DEK
      │
      ▼
 AES-256-GCM
      │
      ▼
 plaintext
```

The application never needs access to the underlying KMS key material.

## 6. Identity and IAM

The demo uses a dedicated service account:

```text
kms-demo-sa@dev-project-506017.iam.gserviceaccount.com
```

It is granted:

```text
roles/cloudkms.cryptoKeyEncrypterDecrypter
```

directly on:

```text
data-encryption-key
```

The design intentionally avoids granting the application:

```text
roles/cloudkms.admin
```

or broad project-level KMS administration permissions.

The application can perform cryptographic operations on the target CryptoKey, but it does not administer the KMS hierarchy.

## 7. Rotation Design

Initial state:

```text
data-encryption-key
└── v1 ← PRIMARY
```

A second version was created:

```text
data-encryption-key
├── v1
└── v2
```

Version 2 was then promoted to primary:

```text
data-encryption-key
├── v1 = ENABLED
└── v2 = ENABLED ← PRIMARY
```

The lab created an encrypted envelope while v1 was primary:

```text
DEK-1
  ↓
KMS v1
  ↓
wrapped-DEK-1
```

After promoting v2 to primary, the old envelope was still decrypted successfully.

This demonstrates:

```text
Old ciphertext
    ↓
wrapped DEK created under v1
    ↓
KMS
    ↓
v1 material used for unwrap
    ↓
DEK recovered
    ↓
AES-256-GCM
    ↓
plaintext
```

At the same time, new encryption operations use v2 because v2 is the current primary version.

## 8. Security Properties Demonstrated

### Key separation

The KEK is managed by Cloud KMS while the DEK performs data encryption locally.

### Key material protection

The application's runtime identity never receives the underlying KMS key material.

### Least privilege

The application service account receives only cryptographic permissions required for the target CryptoKey.

### Key rotation

A new KMS version can become primary without immediately invalidating ciphertext protected by an older enabled version.

### Fresh DEKs

Each encryption operation generates a new DEK instead of reusing a long-lived data-encryption key.

### Authenticated encryption

AES-256-GCM provides confidentiality and integrity. Additional Authenticated Data (AAD) is included in the authenticated encryption operation.

## 9. Actual Lab Configuration

```text
Project:
dev-project-506017

Region:
asia-south1

Key Ring:
app-keyring

CryptoKey:
data-encryption-key

Protection:
SOFTWARE

Purpose:
ENCRYPT_DECRYPT

Algorithm:
GOOGLE_SYMMETRIC_ENCRYPTION

KMS Application Identity:
kms-demo-sa@dev-project-506017.iam.gserviceaccount.com
```

Final key state:

```text
Version 1: ENABLED
Version 2: ENABLED
Primary: Version 2
```

## 10. Evidence

The lab captures evidence for:

```text
evidence/
├── encryption-demo.txt
├── kms-iam.txt
├── kms-key-versions.txt
├── kms-rotation-state.txt
└── rotation-evidence.txt
```

The evidence demonstrates:

1. KMS key hierarchy and key versions
2. CryptoKey IAM binding
3. Successful envelope-encryption round trip
4. Key rotation from v1 to v2
5. Successful decryption of data encrypted before rotation

## 11. Design Takeaway

The main architectural pattern is:

```text
                  Cloud KMS
                     │
             manages the KEK
                     │
                     ▼
               wrapped DEK
                     ▲
                     │
Application ── generates DEK locally
                     │
                     ▼
              AES-256-GCM
                     │
                     ▼
                ciphertext
```

This separates **key management** from **bulk data encryption**.

The application performs the data-plane encryption locally, while Cloud KMS provides centralized protection and lifecycle management for the key-encryption key.
