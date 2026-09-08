from __future__ import annotations

import copy
import json
import time

import paho.mqtt.publish as publish

from security.auth import create_signature


BROKER = "127.0.0.1"
PORT = 1883

DEVICE_ID = "door1"
DEVICE_TYPE = "door"


def build_message() -> dict:
    """
    Build one legitimate signed sensor message.
    """

    message = {
        "device": DEVICE_ID,
        "type": DEVICE_TYPE,
        "state": "OPEN",
        "cycle_id": "REPLAY-TEST",
        "timestamp": time.time(),
        "nonce": "REPLAY-DEMO-NONCE-001",
    }

    message["signature"] = create_signature(
        message
    )

    return message


def publish_message(message: dict) -> None:
    """
    Publish one MQTT sensor message.
    """

    publish.single(
        f"kerberos/sensors/{DEVICE_ID}",
        payload=json.dumps(message),
        hostname=BROKER,
        port=PORT,
        qos=1,
    )


def main() -> None:
    print()
    print("=" * 60)
    print("        KERBEROS REPLAY ATTACK TEST")
    print("=" * 60)
    print()

    message = build_message()

    print("[TEST] Original message:")
    print(
        f"  device    = {message['device']}"
    )
    print(
        f"  nonce     = {message['nonce']}"
    )
    print(
        f"  timestamp = {message['timestamp']}"
    )

    print()
    print("[TEST] Publishing legitimate message...")
    publish_message(message)

    time.sleep(2)

    replayed_message = copy.deepcopy(
        message
    )

    print()
    print(
        "[ATTACK] Replaying the exact same message..."
    )

    publish_message(
        replayed_message
    )

    print()
    print("=" * 60)
    print("        REPLAY TEST COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    main()