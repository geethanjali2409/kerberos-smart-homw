import hashlib
import hmac
import json
from typing import Any


# =========================================================
# DEVICE KEY REGISTRY
# =========================================================
#
# Development keys are pre-provisioned per device.
#
# IMPORTANT:
# These are demonstration keys for the current build.
# For the final physical deployment, these should be stored
# securely on the ESP32 and outside the source repository.
#
# Each logical device has its own independent credential.
# =========================================================

DEVICE_KEYS = {
    "door1": b"kerberos-door1-key-9f7a2c",
    "pir1": b"kerberos-pir1-key-4b81de",
    "ultrasonic1": b"kerberos-ultrasonic-key-63c9af",
    "camera1": b"kerberos-camera-key-a17e52",
}


# =========================================================
# CANONICAL MESSAGE SERIALIZATION
# =========================================================

def _serialize_payload(payload: dict[str, Any]) -> bytes:
    """
    Convert a message into a deterministic byte sequence.

    sort_keys=True guarantees that the same logical message
    produces the same byte representation before signing.
    """

    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


# =========================================================
# DEVICE KEY LOOKUP
# =========================================================

def get_device_key(device_id: str) -> bytes | None:
    """
    Return the pre-provisioned secret for a device.

    Unknown devices have no valid key and therefore cannot
    authenticate.
    """

    return DEVICE_KEYS.get(device_id)


# =========================================================
# CREATE SIGNATURE
# =========================================================

def create_signature(payload: dict[str, Any]) -> str:
    """
    Create an HMAC-SHA256 signature using the key belonging
    to payload['device'].

    The device identity is therefore bound to the message.
    """

    device_id = payload.get("device")

    if not device_id:
        raise ValueError(
            "Cannot sign a message without a device ID."
        )

    key = get_device_key(device_id)

    if key is None:
        raise ValueError(
            f"Unknown device: {device_id}"
        )

    message = _serialize_payload(payload)

    signature = hmac.new(
        key,
        message,
        hashlib.sha256,
    ).hexdigest()

    return signature


# =========================================================
# VERIFY SIGNATURE
# =========================================================

def verify_signature(
    payload: dict[str, Any],
    signature: str,
) -> bool:
    """
    Verify an HMAC-SHA256 signature using the key assigned
    to the claimed device.

    Returns False for unknown devices, malformed signatures,
    or invalid signatures.
    """

    if not isinstance(signature, str):
        return False

    device_id = payload.get("device")

    if not device_id:
        return False

    key = get_device_key(device_id)

    if key is None:
        return False

    message = _serialize_payload(payload)

    expected_signature = hmac.new(
        key,
        message,
        hashlib.sha256,
    ).hexdigest()

    return hmac.compare_digest(
        expected_signature,
        signature,
    )