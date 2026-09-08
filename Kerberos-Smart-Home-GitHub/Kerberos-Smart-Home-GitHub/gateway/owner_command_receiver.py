from __future__ import annotations

import json
from typing import Any

import paho.mqtt.client as mqtt

from gateway.command_guardian import evaluate_command
from gateway.evidence_fusion import fuse_evidence
from gateway.quorum import weighted_quorum
from security.owner_auth import verify_owner_command


BROKER = "127.0.0.1"
PORT = 1883

OWNER_COMMAND_TOPIC = "kerberos/owner/commands"


EXPECTED_DEVICES = {
    "door1",
    "pir1",
    "ultrasonic1",
    "camera1",
}


def normalize_house_state(quorum_decision: str) -> str:
    """
    Convert quorum output into the house-state names expected
    by the Command Guardian.
    """

    if quorum_decision == "INTRUSION":
        return "ALERT"

    if quorum_decision == "SAFE":
        return "SAFE"

    if quorum_decision == "UNCERTAIN":
        return "DEGRADED"

    return "DEGRADED"


def evaluate_received_command(
    command: dict[str, Any],
    votes: dict[str, str],
    trust: dict[str, float],
    behavior_anomaly: float = 0.0,
    used_nonces: set[str] | None = None,
) -> dict[str, Any]:
    """
    Evaluate one MQTT owner command against the current
    simulated physical evidence.
    """

    if used_nonces is None:
        used_nonces = set()

    # ---------------------------------------------------------
    # 1. Verify owner command
    # ---------------------------------------------------------

    authenticated, auth_reason = verify_owner_command(
        command,
        used_nonces=used_nonces,
    )

    print(
        "[OWNER AUTH] "
        f"{'✅ PASS' if authenticated else '❌ FAIL'} "
        f"- {auth_reason}"
    )

    if not authenticated:
        return {
            "decision": "REFUSE",
            "reason": (
                f"Owner authentication failed: {auth_reason}"
            ),
        }

    # ---------------------------------------------------------
    # 2. Existing weighted quorum
    # ---------------------------------------------------------

    quorum = weighted_quorum(
        votes,
        trust,
    )

    quorum_decision = quorum.get(
        "decision",
        "UNCERTAIN",
    )

    quorum_confidence = float(
        quorum.get(
            "confidence",
            0.0,
        )
    )

    house_state = normalize_house_state(
        quorum_decision
    )

    print(
        "[QUORUM] "
        f"Decision={quorum_decision} "
        f"Confidence={quorum_confidence * 100:.2f}%"
    )

    # ---------------------------------------------------------
    # 3. K-REAF
    # ---------------------------------------------------------

    fusion = fuse_evidence(
        votes,
        trust,
    )

    print(
        "[K-REAF] "
        f"Decision={fusion.decision} "
        f"SAFE={fusion.belief_safe * 100:.2f}% "
        f"INTRUSION={fusion.belief_intrusion * 100:.2f}% "
        f"Conflict={fusion.conflict * 100:.2f}% "
        f"Uncertainty={fusion.uncertainty * 100:.2f}%"
    )

    # ---------------------------------------------------------
    # 4. Command Guardian
    # ---------------------------------------------------------

    guardian = evaluate_command(
        action=command["action"],
        owner_authenticated=True,
        command_fresh=True,
        house_state=house_state,
        quorum_confidence=quorum_confidence,
        k_reaf_conflict=fusion.conflict,
        k_reaf_uncertainty=fusion.uncertainty,
        behavior_anomaly=behavior_anomaly,
        k_reaf_belief_intrusion=fusion.belief_intrusion,
    )

    print(
        "[GUARDIAN] "
        f"Decision={guardian.decision} "
        f"Risk={guardian.risk * 100:.2f}%"
    )

    print(
        "[GUARDIAN] "
        f"Reason={guardian.reason}"
    )

    return {
        "decision": guardian.decision,
        "reason": guardian.reason,
        "risk": guardian.risk,
        "owner": command["owner"],
        "command_id": command["command_id"],
        "action": command["action"],
        "house_state": house_state,
        "quorum_decision": quorum_decision,
        "quorum_confidence": quorum_confidence,
        "k_reaf_decision": fusion.decision,
        "k_reaf_belief_safe": fusion.belief_safe,
        "k_reaf_belief_intrusion": fusion.belief_intrusion,
        "k_reaf_conflict": fusion.conflict,
        "k_reaf_uncertainty": fusion.uncertainty,
        "behavior_anomaly": behavior_anomaly,
    }


def on_connect(
    client: mqtt.Client,
    userdata: Any,
    flags: Any,
    reason_code: Any,
    properties: Any = None,
) -> None:

    if reason_code == 0:
        print(
            "[OWNER MQTT] ✅ Connected to broker"
        )

        client.subscribe(
            OWNER_COMMAND_TOPIC,
            qos=1,
        )

        print(
            f"[OWNER MQTT] "
            f"Subscribed to {OWNER_COMMAND_TOPIC}"
        )

    else:
        print(
            "[OWNER MQTT] ❌ Connection failed: "
            f"{reason_code}"
        )


def on_message(
    client: mqtt.Client,
    userdata: Any,
    message: mqtt.MQTTMessage,
) -> None:

    print()
    print(
        "[OWNER MQTT] 📥 Owner command received"
    )

    try:
        command = json.loads(
            message.payload.decode("utf-8")
        )
    except (
        json.JSONDecodeError,
        UnicodeDecodeError,
    ) as exc:

        print(
            "[OWNER MQTT] ❌ Invalid JSON: "
            f"{exc}"
        )

        return

    print(
        f"[OWNER MQTT] Action="
        f"{command.get('action', 'UNKNOWN')}"
    )

    # ---------------------------------------------------------
    # Development-mode physical evidence.
    #
    # Later this will come from the live gateway state instead
    # of being supplied by the simulator.
    # ---------------------------------------------------------

    votes = userdata.get(
        "votes",
        {},
    )

    trust = userdata.get(
        "trust",
        {},
    )

    behavior_anomaly = userdata.get(
        "behavior_anomaly",
        0.0,
    )

    used_nonces = userdata.get(
        "used_nonces",
        set(),
    )

    result = evaluate_received_command(
        command=command,
        votes=votes,
        trust=trust,
        behavior_anomaly=behavior_anomaly,
        used_nonces=used_nonces,
    )

    print(
        "[OWNER MQTT] "
        f"Final decision: {result['decision']}"
    )


def run_receiver(
    votes: dict[str, str],
    trust: dict[str, float],
    behavior_anomaly: float = 0.0,
) -> None:

    userdata = {
        "votes": votes,
        "trust": trust,
        "behavior_anomaly": behavior_anomaly,
        "used_nonces": set(),
    }

    client = mqtt.Client(
        callback_api_version=mqtt.CallbackAPIVersion.VERSION2
    )

    client.user_data_set(
        userdata
    )

    client.on_connect = on_connect
    client.on_message = on_message

    print(
        f"[OWNER MQTT] Connecting to "
        f"{BROKER}:{PORT}..."
    )

    client.connect(
        BROKER,
        PORT,
        keepalive=60,
    )

    try:
        print(
            "[OWNER MQTT] 🟢 Waiting for owner commands..."
        )

        client.loop_forever()

    except KeyboardInterrupt:

        print(
            "\n[OWNER MQTT] Stopping receiver."
        )

        client.disconnect()


if __name__ == "__main__":

    safe_votes = {
        "door1": "SAFE",
        "pir1": "SAFE",
        "ultrasonic1": "SAFE",
        "camera1": "SAFE",
    }

    safe_trust = {
        "door1": 100,
        "pir1": 100,
        "ultrasonic1": 100,
        "camera1": 100,
    }

    run_receiver(
        safe_votes,
        safe_trust,
    )