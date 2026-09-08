import base64
import json
import os
import secrets

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from google.cloud import kms


PROJECT_ID = os.environ["PROJECT_ID"]
LOCATION = os.environ["REGION"]
KEY_RING = os.environ["KMS_KEYRING"]
KEY_NAME = os.environ["KMS_KEY"]

PLAINTEXT = b"Confidential data for the KMS envelope encryption lab."
AAD = b"kms-lab:v1"
ENVELOPE_FILE = "envelope.json"

KMS_KEY_NAME = (
    f"projects/{PROJECT_ID}/locations/{LOCATION}"
    f"/keyRings/{KEY_RING}/cryptoKeys/{KEY_NAME}"
)


def generate_dek() -> bytes:
    """Generate a fresh 256-bit Data Encryption Key."""
    return secrets.token_bytes(32)


def encrypt_data(dek: bytes, plaintext: bytes, aad: bytes):
    """Encrypt application data locally with AES-256-GCM."""
    nonce = secrets.token_bytes(12)

    aesgcm = AESGCM(dek)

    ciphertext = aesgcm.encrypt(
        nonce,
        plaintext,
        aad,
    )

    return nonce, ciphertext


def wrap_dek(kms_client, dek: bytes):
    """
    Wrap the DEK with Cloud KMS.

    EncryptResponse.name identifies the exact CryptoKeyVersion
    used by Cloud KMS for the operation.
    """
    response = kms_client.encrypt(
        request={
            "name": KMS_KEY_NAME,
            "plaintext": dek,
        }
    )

    return response.ciphertext, response.name


def unwrap_dek(kms_client, wrapped_dek: bytes) -> bytes:
    """Unwrap the DEK using Cloud KMS."""
    response = kms_client.decrypt(
        request={
            "name": KMS_KEY_NAME,
            "ciphertext": wrapped_dek,
        }
    )

    return response.plaintext


def main():
    kms_client = kms.KeyManagementServiceClient()

    print("=== Cloud KMS Envelope Encryption Demo ===")
    print(f"KMS key: {KMS_KEY_NAME}")
    print()

    # 1. Generate a fresh DEK locally.
    dek = generate_dek()
    print("1. Generated fresh 256-bit DEK locally.")

    # 2. Encrypt application data locally with AES-256-GCM.
    nonce, ciphertext = encrypt_data(
        dek,
        PLAINTEXT,
        AAD,
    )
    print("2. Encrypted plaintext with AES-256-GCM.")

    # 3. Wrap the DEK using the KMS CryptoKey.
    wrapped_dek, wrapping_version = wrap_dek(
        kms_client,
        dek,
    )

    print("3. Wrapped DEK using Cloud KMS.")
    print(f"   KMS version used: {wrapping_version}")

    envelope = {
        "kms_key": KMS_KEY_NAME,
        "kms_version_used": wrapping_version,
        "wrapped_dek": base64.b64encode(wrapped_dek).decode(),
        "nonce": base64.b64encode(nonce).decode(),
        "aad": base64.b64encode(AAD).decode(),
        "ciphertext": base64.b64encode(ciphertext).decode(),
    }

    with open(ENVELOPE_FILE, "w", encoding="utf-8") as f:
        json.dump(envelope, f, indent=2)

    print(f"4. Saved encrypted envelope to {ENVELOPE_FILE}.")

    # Remove plaintext DEK from the main application variable.
    del dek

    # 5. Recover the DEK through KMS.
    recovered_dek = unwrap_dek(
        kms_client,
        wrapped_dek,
    )
    print("5. Unwrapped DEK using Cloud KMS.")

    # 6. Decrypt locally using recovered DEK.
    recovered_plaintext = AESGCM(recovered_dek).decrypt(
        nonce,
        ciphertext,
        AAD,
    )

    print("6. Decrypted ciphertext locally.")
    print()
    print(f"Recovered plaintext: {recovered_plaintext.decode()}")

    if recovered_plaintext != PLAINTEXT:
        raise RuntimeError("Recovered plaintext does not match original.")

    print()
    print("RESULT: Envelope encryption round trip SUCCESS")


if __name__ == "__main__":
    main()
