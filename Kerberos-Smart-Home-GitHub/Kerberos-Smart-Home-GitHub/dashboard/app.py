from __future__ import annotations

import json
import os
import threading
from datetime import datetime
from typing import Any

import paho.mqtt.client as mqtt
from flask import Flask, jsonify, render_template


# ============================================================
# PATHS / CONFIGURATION
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

LOG_FILE = os.path.join(
    BASE_DIR,
    "event_logging",
    "security_events.jsonl",
)

BROKER = "127.0.0.1"
PORT = 1883

STATUS_TOPIC = "kerberos/status"


# ============================================================
# FLASK
# ============================================================

app = Flask(__name__)


# ============================================================
# LIVE STATUS
# ============================================================

status_lock = threading.Lock()

live_status: dict[str, Any] = {
    "timestamp": 0,
    "house_state": "UNKNOWN",
    "decision": "UNKNOWN",
    "confidence": 0.0,
    "devices": {},
    "anomalous_devices": [],
    "quarantined_devices": [],
}


# ============================================================
# MQTT STATUS CALLBACK
# ============================================================

def on_status_message(
    client: mqtt.Client,
    userdata: Any,
    msg: mqtt.MQTTMessage,
) -> None:
    """
    Receive live security status from the gateway.
    """

    global live_status

    try:
        payload = msg.payload.decode(
            "utf-8"
        )

        data = json.loads(payload)

        if not isinstance(data, dict):
            raise ValueError(
                "Status payload must be a JSON object."
            )

        with status_lock:
            live_status = data

    except (
        UnicodeDecodeError,
        json.JSONDecodeError,
        ValueError,
    ) as exc:

        print(
            f"[DASHBOARD] ❌ Invalid status message: {exc}"
        )


def start_mqtt_listener() -> mqtt.Client:
    """
    Start background MQTT listener for gateway status.
    """

    client = mqtt.Client(
        mqtt.CallbackAPIVersion.VERSION2
    )

    client.on_message = on_status_message

    print(
        "[DASHBOARD] Connecting to MQTT broker..."
    )

    client.connect(
        BROKER,
        PORT,
        60,
    )

    client.subscribe(
        STATUS_TOPIC,
        qos=1,
    )

    client.loop_start()

    print(
        f"[DASHBOARD] ✅ Subscribed to {STATUS_TOPIC}"
    )

    return client


# ============================================================
# AUDIT LOG
# ============================================================

def load_events() -> list[dict[str, Any]]:
    """
    Load security events from the tamper-evident JSONL log.
    """

    if not os.path.exists(LOG_FILE):
        return []

    events: list[dict[str, Any]] = []

    try:

        with open(
            LOG_FILE,
            "r",
            encoding="utf-8",
        ) as file:

            for line in file:

                line = line.strip()

                if not line:
                    continue

                try:

                    record = json.loads(
                        line
                    )

                    if isinstance(record, dict):
                        events.append(record)

                except json.JSONDecodeError:

                    # Ignore malformed lines in the UI.
                    # The separate verifier is authoritative
                    # for log integrity.
                    continue

    except OSError as exc:

        print(
            f"[DASHBOARD] ⚠️ Unable to read audit log: {exc}"
        )

    return events


# ============================================================
# TIME FORMAT
# ============================================================

def format_timestamp(
    timestamp: Any,
) -> str:
    """
    Convert Unix timestamp to HH:MM:SS.
    """

    try:

        return datetime.fromtimestamp(
            float(timestamp)
        ).strftime(
            "%H:%M:%S"
        )

    except (
        TypeError,
        ValueError,
        OSError,
    ):

        return "--:--:--"


# ============================================================
# DASHBOARD DATA
# ============================================================

def build_dashboard_data() -> dict[str, Any]:
    """
    Combine live gateway state with historical audit events.
    """

    records = load_events()

    defense_events = []
    actuator_events = []
    quarantine_events = []

    for record in records:

        event = record.get(
            "event",
            {},
        )

        event_type = event.get(
            "event_type"
        )

        if event_type == "DEFENSE_DECISION":
            defense_events.append(record)

        elif event_type == "ACTUATOR_COMMAND":
            actuator_events.append(record)

        elif event_type == "DEVICE_QUARANTINED":
            quarantine_events.append(record)

    # --------------------------------------------------------
    # Current live gateway status
    # --------------------------------------------------------

    with status_lock:

        current_status = dict(
            live_status
        )

    current_devices = current_status.get(
        "devices",
        {},
    )

    if not isinstance(
        current_devices,
        dict,
    ):
        current_devices = {}

    current_quarantined = current_status.get(
        "quarantined_devices",
        [],
    )

    if not isinstance(
        current_quarantined,
        list,
    ):
        current_quarantined = []

    current_anomalies = current_status.get(
        "anomalous_devices",
        [],
    )

    if not isinstance(
        current_anomalies,
        list,
    ):
        current_anomalies = []

    # --------------------------------------------------------
    # Latest defense event
    # --------------------------------------------------------

    latest_defense = None

    if defense_events:

        event = defense_events[-1].get(
            "event",
            {},
        )

        data = event.get(
            "data",
            {},
        )

        latest_defense = {
            "state": data.get(
                "state",
                "UNKNOWN",
            ),
            "intrusion_detected": bool(
                data.get(
                    "intrusion_detected",
                    False,
                )
            ),
            "actions": data.get(
                "actions",
                [],
            ),
            "timestamp": format_timestamp(
                event.get(
                    "timestamp"
                )
            ),
        }

    # --------------------------------------------------------
    # Latest actuator event
    # --------------------------------------------------------

    latest_actuator = None

    if actuator_events:

        event = actuator_events[-1].get(
            "event",
            {},
        )

        data = event.get(
            "data",
            {},
        )

        latest_actuator = {
            "action": data.get(
                "action",
                "UNKNOWN",
            ),
            "command_id": data.get(
                "command_id",
                "UNKNOWN",
            ),
            "topic": data.get(
                "topic",
                "",
            ),
            "timestamp": format_timestamp(
                event.get(
                    "timestamp"
                )
            ),
        }

    # --------------------------------------------------------
    # Quarantine history fallback
    # --------------------------------------------------------

    quarantine_from_log = []

    for record in quarantine_events:

        data = record.get(
            "event",
            {}
        ).get(
            "data",
            {},
        )

        device = data.get(
            "device"
        )

        if (
            device
            and device not in quarantine_from_log
        ):
            quarantine_from_log.append(
                device
            )

    # --------------------------------------------------------
    # Prefer current live quarantine state.
    # Fall back to audit history only when live state
    # has not been published yet.
    # --------------------------------------------------------

    if current_status.get(
        "timestamp",
        0,
    ):

        quarantined_devices = (
            current_quarantined
        )

    else:

        quarantined_devices = (
            quarantine_from_log
        )

    # --------------------------------------------------------
    # Recent events
    # --------------------------------------------------------

    recent_events = []

    for record in reversed(
        records[-30:]
    ):

        event = record.get(
            "event",
            {},
        )

        recent_events.append(
            {
                "event_type": event.get(
                    "event_type",
                    "UNKNOWN",
                ),
                "timestamp": format_timestamp(
                    event.get(
                        "timestamp"
                    )
                ),
                "data": event.get(
                    "data",
                    {},
                ),
            }
        )

    # --------------------------------------------------------
    # Return combined dashboard data
    # --------------------------------------------------------

    return {
        "timestamp": current_status.get(
            "timestamp",
            0,
        ),
        "house_state": current_status.get(
            "house_state",
            "UNKNOWN",
        ),
        "decision": current_status.get(
            "decision",
            "UNKNOWN",
        ),
        "confidence": float(
            current_status.get(
                "confidence",
                0.0,
            )
        ),
        "devices": current_devices,
        "anomalous_devices": current_anomalies,
        "quarantined_devices": quarantined_devices,
        "event_count": len(records),
        "actuator_count": len(
            actuator_events
        ),
        "quarantine_count": len(
            quarantine_events
        ),
        "latest_defense": latest_defense,
        "latest_actuator": latest_actuator,
        "recent_events": recent_events,
    }


# ============================================================
# ROUTES
# ============================================================

@app.route("/")
def index():
    return render_template(
        "index.html"
    )


@app.route("/api/status")
def api_status():
    return jsonify(
        build_dashboard_data()
    )


# ============================================================
# MAIN
# ============================================================

def main() -> None:

    print()
    print("=" * 60)
    print(
        "        KERBEROS SECURITY DASHBOARD"
    )
    print("=" * 60)
    print()

    mqtt_client = start_mqtt_listener()

    print(
        "Open: http://127.0.0.1:5000"
    )

    print()

    try:

        app.run(
            host="127.0.0.1",
            port=5000,
            debug=False,
        )

    finally:

        mqtt_client.loop_stop()
        mqtt_client.disconnect()


if __name__ == "__main__":
    main()