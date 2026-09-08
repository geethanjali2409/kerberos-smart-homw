import json
import time
import uuid

import paho.mqtt.publish as publish

from event_logging.event_log import log_event


BROKER = "127.0.0.1"
PORT = 1883

ACTUATOR_TOPIC = "kerberos/actuators"


def build_command(action: str) -> dict:
    """
    Build a unique actuator command.
    """

    if not action:
        raise ValueError(
            "Actuator action cannot be empty."
        )

    return {
        "command_id": str(
            uuid.uuid4()
        ),
        "action": action,
        "timestamp": time.time(),
    }


def send_command(action: str) -> bool:
    """
    Publish a physical actuator command
    through MQTT and record it in the audit log.
    """

    command = build_command(action)

    topic = (
        f"{ACTUATOR_TOPIC}/"
        f"{action.lower()}"
    )

    try:

        publish.single(
            topic,
            payload=json.dumps(command),
            hostname=BROKER,
            port=PORT,
            qos=1,
        )

        print(
            f"[ACTUATOR] ✅ Command sent: "
            f"{action} "
            f"(id={command['command_id']})"
        )

        # ----------------------------------------------------
        # Tamper-evident audit record
        # ----------------------------------------------------

        try:

            log_event(
                "ACTUATOR_COMMAND",
                {
                    "command_id":
                        command["command_id"],
                    "action": action,
                    "topic": topic,
                },
            )

        except Exception as exc:

            print(
                f"[LOGGING] ⚠️ Failed to record "
                f"actuator event: {exc}"
            )

        return True

    except Exception as exc:

        print(
            f"[ACTUATOR] ❌ Failed to send "
            f"{action}: {exc}"
        )

        return False


def execute_actions(
    actions: list[str],
) -> list[str]:
    """
    Execute physical actuator actions.

    Non-physical actions remain gateway-side.
    """

    physical_actions = {
        "LOCK_DOOR",
        "UNLOCK_DOOR",
        "ACTIVATE_ALARM",
        "DEACTIVATE_ALARM",
    }

    executed = []

    for action in actions:

        if action in physical_actions:

            if send_command(action):
                executed.append(action)

    return executed