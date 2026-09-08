from __future__ import annotations

import json
import time

import paho.mqtt.publish as publish

from security.auth import create_signature


BROKER = "127.0.0.1"
PORT = 1883

DEVICE_ID = "door1"
DEVICE_TYPE = "door"

# Must exceed MAX_MESSAGE_AGE in security/nonce_manager.py.
STALE_AGE = 30


def main() -> None:

    print()
    print("=" * 60)
    print("        KERBEROS STALE MESSAGE TEST")
    print("=" * 60)
    print()

    # --------------------------------------------------------
    # Create an intentionally old but correctly signed message
    # --------------------------------------------------------

    old_timestamp = time.time() - STALE_AGE

    message = {
        "device": DEVICE_ID,
        "type": DEVICE_TYPE,
        "state": "OPEN",
        "cycle_id": "STALE-TEST",
        "timestamp": old_timestamp,
        "nonce": "STALE-DEMO-NONCE-001",
    }

    message["signature"] = create_signature(
        message
    )

    print("[TEST] Signed stale message created")
    print(
        f"  timestamp = {message['timestamp']}"
    )
    print(
        f"  age       = approximately {STALE_AGE} seconds"
    )

    # --------------------------------------------------------
    # Publish
    # --------------------------------------------------------

    publish.single(
        f"kerberos/sensors/{DEVICE_ID}",
        payload=json.dumps(message),
        hostname=BROKER,
        port=PORT,
        qos=1,
    )

    print()
    print("[TEST] Stale message published")

    print()
    print("=" * 60)
    print("        STALE TEST COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    main()