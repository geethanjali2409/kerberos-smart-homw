from __future__ import annotations

import copy
import time

from security.owner_auth import (
    build_owner_command,
    create_owner_signature,
    verify_owner_command,
    verify_owner_signature,
)


def test_valid_owner_command():
    command = build_owner_command(
        "owner1",
        "UNLOCK_DOOR",
    )

    valid, reason = verify_owner_command(
        command,
        used_nonces=set(),
    )

    assert valid is True
    assert reason == "AUTHENTICATED"


def test_tampered_action_is_rejected():
    command = build_owner_command(
        "owner1",
        "UNLOCK_DOOR",
    )

    command["action"] = "LOCK_DOOR"

    valid, reason = verify_owner_command(
        command,
        used_nonces=set(),
    )

    assert valid is False
    assert reason == "SIGNATURE_INVALID"


def test_tampered_owner_is_rejected():
    command = build_owner_command(
        "owner1",
        "UNLOCK_DOOR",
    )

    command["owner"] = "attacker"

    valid, reason = verify_owner_command(
        command,
        used_nonces=set(),
    )

    assert valid is False
    assert reason == "SIGNATURE_INVALID"


def test_invalid_signature_is_rejected():
    command = build_owner_command(
        "owner1",
        "UNLOCK_DOOR",
    )

    command["signature"] = "deadbeef"

    valid, reason = verify_owner_command(
        command,
        used_nonces=set(),
    )

    assert valid is False
    assert reason == "SIGNATURE_INVALID"


def test_replay_is_rejected():
    command = build_owner_command(
        "owner1",
        "UNLOCK_DOOR",
    )

    used_nonces = set()

    valid1, reason1 = verify_owner_command(
        command,
        used_nonces=used_nonces,
    )

    valid2, reason2 = verify_owner_command(
        command,
        used_nonces=used_nonces,
    )

    assert valid1 is True
    assert reason1 == "AUTHENTICATED"

    assert valid2 is False
    assert reason2 == "REPLAY_DETECTED"


def test_stale_command_is_rejected():
    command = build_owner_command(
        "owner1",
        "UNLOCK_DOOR",
    )

    command["timestamp"] = (
        time.time() - 30
    )

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

    command["signature"] = create_owner_signature(
        payload
    )

    valid, reason = verify_owner_command(
        command,
        used_nonces=set(),
    )

    assert valid is False
    assert reason == "COMMAND_TOO_OLD"


def test_missing_field_is_rejected():
    command = build_owner_command(
        "owner1",
        "UNLOCK_DOOR",
    )

    del command["nonce"]

    valid, reason = verify_owner_command(
        command,
        used_nonces=set(),
    )

    assert valid is False
    assert reason == "MISSING_FIELD"


def test_signature_verification_is_deterministic():
    command = build_owner_command(
        "owner1",
        "LOCK_DOOR",
    )

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

    signature = command["signature"]

    assert verify_owner_signature(
        payload,
        signature,
    ) is True

    tampered = copy.deepcopy(payload)
    tampered["action"] = "UNLOCK_DOOR"

    assert verify_owner_signature(
        tampered,
        signature,
    ) is False


if __name__ == "__main__":
    tests = [
        test_valid_owner_command,
        test_tampered_action_is_rejected,
        test_tampered_owner_is_rejected,
        test_invalid_signature_is_rejected,
        test_replay_is_rejected,
        test_stale_command_is_rejected,
        test_missing_field_is_rejected,
        test_signature_verification_is_deterministic,
    ]

    for test in tests:
        test()
        print(f"[PASS] {test.__name__}")

    print()
    print("✅ ALL OWNER AUTHENTICATION TESTS PASSED")