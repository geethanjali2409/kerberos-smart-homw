from __future__ import annotations

import json
import time

import paho.mqtt.publish as publish

from security.auth import create_signature


BROKER = "127.0.0.1"
PORT = 1883

DEVICE_ID = "door1"
DEVICE_TYPE = "door"


def main() -> None:

    print()
    print("=" * 60)
    print("        KERBEROS TAMPER ATTACK TEST")
    print("=" * 60)
    print()

    # --------------------------------------------------------
    # Create a legitimate message
    # --------------------------------------------------------

    message = {
        "device": DEVICE_ID,
        "type": DEVICE_TYPE,
        "state": "OPEN",
        "cycle_id": "TAMPER-TEST",
        "timestamp": time.time(),
        "nonce": "TAMPER-DEMO-NONCE-001",
    }

    message["signature"] = create_signature(
        message
    )

    print("[TEST] Legitimate message created")
    print(
        f"  state     = {message['state']}"
    )
    print(
        f"  signature = {message['signature']}"
    )

    # --------------------------------------------------------
    # Attack: modify the state AFTER signing
    # --------------------------------------------------------

    message["state"] = "CLOSED"

    print()
    print("[ATTACK] Sensor state modified after signing")
    print(
        f"  modified state = {message['state']}"
    )
    print(
        "  original signature retained"
    )

    # --------------------------------------------------------
    # Publish tampered message
    # --------------------------------------------------------

    publish.single(
        f"kerberos/sensors/{DEVICE_ID}",
        payload=json.dumps(message),
        hostname=BROKER,
        port=PORT,
        qos=1,
    )

    print()
    print("[ATTACK] Tampered message published")

    print()
    print("=" * 60)
    print("        TAMPER TEST COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    main()