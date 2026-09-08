from __future__ import annotations

import hashlib
import hmac
import json
import time
import uuid
from typing import Any


OWNER_KEYS = {
    "owner1": b"kerberos-owner1-key-8c41f2",
}


COMMAND_MAX_AGE = 10


def _serialize_payload(payload: dict[str, Any]) -> bytes:
    """
    Canonical serialization used for signing and verification.
    """
    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def get_owner_key(owner: str) -> bytes | None:
    return OWNER_KEYS.get(owner)


def create_owner_signature(
    payload: dict[str, Any],
) -> str:
    """
    Create an HMAC-SHA256 signature for an owner command.
    """

    owner = payload.get("owner")

    if not owner:
        raise ValueError(
            "Cannot sign a command without an owner ID."
        )

    key = get_owner_key(owner)

    if key is None:
        raise ValueError(
            f"Unknown owner: {owner}"
        )

    message = _serialize_payload(payload)

    return hmac.new(
        key,
        message,
        hashlib.sha256,
    ).hexdigest()


def verify_owner_signature(
    payload: dict[str, Any],
    signature: str,
) -> bool:
    """
    Verify the owner's HMAC signature.
    """

    if not isinstance(signature, str):
        return False

    owner = payload.get("owner")

    if not owner:
        return False

    key = get_owner_key(owner)

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


def check_owner_freshness(
    timestamp: float,
    nonce: str,
    *,
    max_age: int = COMMAND_MAX_AGE,
    used_nonces: set[str] | None = None,
) -> tuple[bool, str]:
    """
    Check command freshness and replay protection.

    A nonce set can be supplied by the caller so replay state can
    be shared across the gateway. For this development version,
    an in-memory set is sufficient.
    """

    if not isinstance(timestamp, (int, float)):
        return False, "INVALID_TIMESTAMP"

    if not isinstance(nonce, str) or not nonce:
        return False, "INVALID_NONCE"

    if used_nonces is None:
        used_nonces = _USED_OWNER_NONCES

    age = abs(
        time.time() - float(timestamp)
    )

    if age > max_age:
        return False, "COMMAND_TOO_OLD"

    if nonce in used_nonces:
        return False, "REPLAY_DETECTED"

    used_nonces.add(nonce)

    return True, "FRESH"


_USED_OWNER_NONCES: set[str] = set()


def build_owner_command(
    owner: str,
    action: str,
) -> dict[str, Any]:
    """
    Build a fresh signed owner command envelope.
    """

    payload = {
        "command_id": str(uuid.uuid4()),
        "owner": owner,
        "action": action.upper(),
        "timestamp": time.time(),
        "nonce": str(uuid.uuid4()),
    }

    signature = create_owner_signature(
        payload
    )

    payload["signature"] = signature

    return payload


def verify_owner_command(
    command: dict[str, Any],
    *,
    used_nonces: set[str] | None = None,
) -> tuple[bool, str]:
    """
    Verify the complete cryptographic command envelope.

    Checks:
        - required fields
        - owner identity
        - signature
        - freshness
        - replay
    """

    if not isinstance(command, dict):
        return False, "INVALID_COMMAND"

    required_fields = {
        "command_id",
        "owner",
        "action",
        "timestamp",
        "nonce",
        "signature",
    }

    if not required_fields.issubset(command):
        return False, "MISSING_FIELD"

    payload = {
        key: command[key]
        for key in (
            "command_id",
            "owner",
            "action",
            "timestamp",
            "nonce",
        )
    }

    if not verify_owner_signature(
        payload,
        command["signature"],
    ):
        return False, "SIGNATURE_INVALID"

    fresh, reason = check_owner_freshness(
        payload["timestamp"],
        payload["nonce"],
        used_nonces=used_nonces,
    )

    if not fresh:
        return False, reason

    return True, "AUTHENTICATED"