import base64
import json
import os

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from google.cloud import kms


PROJECT_ID = os.environ["PROJECT_ID"]
LOCATION = os.environ["REGION"]
KEY_RING = os.environ["KMS_KEYRING"]
KEY_NAME = os.environ["KMS_KEY"]

KMS_KEY_NAME = (
    f"projects/{PROJECT_ID}/locations/{LOCATION}"
    f"/keyRings/{KEY_RING}/cryptoKeys/{KEY_NAME}"
)

ENVELOPE_FILE = "envelope.json"


def main():
    with open(ENVELOPE_FILE, "r", encoding="utf-8") as f:
        envelope = json.load(f)

    print("=== Decrypt Previously Encrypted Envelope ===")
    print(f"KMS key: {KMS_KEY_NAME}")
    print(f"Envelope wrapped using: {envelope['kms_version_used']}")

    kms_client = kms.KeyManagementServiceClient()

    wrapped_dek = base64.b64decode(envelope["wrapped_dek"])
    nonce = base64.b64decode(envelope["nonce"])
    aad = base64.b64decode(envelope["aad"])
    ciphertext = base64.b64decode(envelope["ciphertext"])

    response = kms_client.decrypt(
        request={
            "name": KMS_KEY_NAME,
            "ciphertext": wrapped_dek,
        }
    )

    recovered_dek = response.plaintext

    plaintext = AESGCM(recovered_dek).decrypt(
        nonce,
        ciphertext,
        aad,
    )

    print(f"Recovered plaintext: {plaintext.decode()}")
    print()
    print(
        "RESULT: Previously encrypted envelope successfully "
        "decrypted after rotation"
    )


if __name__ == "__main__":
    main()
