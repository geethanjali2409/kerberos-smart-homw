from __future__ import annotations

import json
import time
from typing import Any

import paho.mqtt.publish as publish


BROKER = "127.0.0.1"
PORT = 1883

STATUS_TOPIC = "kerberos/status"


def publish_status(
    house_state: str,
    decision: str,
    confidence: float,
    devices: dict[str, dict[str, Any]],
    anomalous_devices: list[str],
    quarantined_devices: list[str],
) -> bool:
    """
    Publish the gateway's authoritative live security state.

    The dashboard consumes this message.
    retain=True ensures a newly started dashboard receives
    the most recent state immediately.
    """

    payload = {
        "timestamp": time.time(),
        "house_state": house_state,
        "decision": decision,
        "confidence": float(confidence),
        "devices": devices,
        "anomalous_devices": anomalous_devices,
        "quarantined_devices": quarantined_devices,
    }

    try:
        publish.single(
            STATUS_TOPIC,
            payload=json.dumps(payload),
            hostname=BROKER,
            port=PORT,
            qos=1,
            retain=True,
        )

        print(
            "[STATUS] ✅ Live security state published"
        )

        return True

    except Exception as exc:
        print(
            f"[STATUS] ❌ Failed to publish state: {exc}"
        )

        return False