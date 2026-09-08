from __future__ import annotations

import json
import time

import paho.mqtt.publish as publish

from security.owner_auth import build_owner_command


BROKER = "127.0.0.1"
PORT = 1883
TOPIC = "kerberos/owner/commands"


def send_owner_command(action: str) -> dict:
    command = build_owner_command(
        "owner1",
        action,
    )

    publish.single(
        TOPIC,
        payload=json.dumps(command),
        hostname=BROKER,
        port=PORT,
        qos=1,
    )

    print(
        f"[OWNER SIM] ✅ Sent {action}"
    )

    print(
        f"[OWNER SIM] command_id="
        f"{command['command_id']}"
    )

    return command


def main() -> None:

    print()
    print("=" * 78)
    print("KERBEROS OWNER MQTT SIMULATOR")
    print("=" * 78)

    command = send_owner_command(
        "UNLOCK_DOOR"
    )

    print(
        "[OWNER SIM] timestamp="
        f"{command['timestamp']}"
    )

    print(
        "[OWNER SIM] nonce="
        f"{command['nonce']}"
    )

    print()
    print(
        "Command published successfully."
    )

    # Keep the process alive briefly so the MQTT broker has time
    # to deliver the message before the script exits.
    time.sleep(1)


if __name__ == "__main__":
    main()