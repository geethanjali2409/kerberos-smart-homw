"""
Kerberos Smart Home Security Gateway

Responsibilities:
    1. Receive sensor messages over MQTT.
    2. Verify HMAC authentication.
    3. Verify timestamp freshness and nonce uniqueness.
    4. Build synchronized house snapshots.
    5. Check physical consistency between devices.
    6. Convert sensor observations into security votes.
    7. Apply trust-weighted quorum.
    8. Track device behavior and anomalies.
    9. Quarantine unreliable devices.
    10. Determine the house security state.
    11. Produce fail-safe defense actions.
    12. Publish physical actuator commands over MQTT.

Run from the project root:

    python -m gateway.main
"""

from __future__ import annotations

import json
import time
from typing import Any

import paho.mqtt.client as mqtt

from gateway.status import publish_status
from gateway.status import publish_status
from security.auth import verify_signature
from security.nonce_manager import check_freshness
from event_logging.event_log import log_event
from gateway.actuator import execute_actions
from gateway.anomaly import is_anomalous, record_behavior
from gateway.consistency import check_consistency
from gateway.failsafe import decide_actions
from gateway.fsm import (
    ALERT,
    DEGRADED,
    LOCKDOWN,
    SAFE,
    determine_state,
)
from gateway.quarantine import (
    get_quarantined_devices,
    is_quarantined,
    quarantine_device,
    should_quarantine,
)
from gateway.quorum import weighted_quorum
from gateway.trust import (
    get_trust,
    penalize_disagreement,
    penalize_replay,
    penalize_stale,
    reward_agreement,
)


# ============================================================
# CONFIGURATION
# ============================================================

BROKER = "127.0.0.1"
PORT = 1883

SENSOR_TOPIC = "kerberos/sensors/#"

EXPECTED_DEVICES = {
    "door1",
    "pir1",
    "ultrasonic1",
    "camera1",
}

MIN_DEVICES_FOR_DECISION = 2

# Maximum age of a completed house snapshot.
SNAPSHOT_MAX_AGE = 15.0


# ============================================================
# RUNTIME STATE
# ============================================================

# Most recent validated message from every device.
device_state: dict[str, dict[str, Any]] = {}

# Last gateway receive time for each device.
device_last_seen: dict[str, float] = {}

# Buffered messages grouped by cycle_id.
snapshot_buffer: dict[str, dict[str, dict[str, Any]]] = {}

# Last processed cycle IDs.
processed_cycles: set[str] = set()

# Current overall house state.
house_state = SAFE


# ============================================================
# SENSOR → SECURITY VOTE
# ============================================================

def convert_to_intrusion_vote(device_id: str, state: Any) -> str | None:
    """
    Convert a physical sensor observation into a normalized security vote.

    Returns:
        "INTRUSION"
        "SAFE"
        None for an unsupported/unknown state.
    """

    normalized = str(state).strip().upper()

    if device_id == "door1":
        if normalized == "OPEN":
            return "INTRUSION"
        if normalized == "CLOSED":
            return "SAFE"

    elif device_id == "pir1":
        if normalized == "MOTION":
            return "INTRUSION"
        if normalized == "NO_MOTION":
            return "SAFE"

    elif device_id == "ultrasonic1":
        if normalized == "PERSON":
            return "INTRUSION"
        if normalized == "NO_PERSON":
            return "SAFE"

    elif device_id == "camera1":
        if normalized == "MOTION":
            return "INTRUSION"
        if normalized == "NO_MOTION":
            return "SAFE"

    return None


# ============================================================
# SNAPSHOT MANAGEMENT
# ============================================================

def get_active_devices() -> set[str]:
    """
    Return devices currently eligible for trusted house decisions.

    Quarantined devices remain observable, but are excluded from
    the trusted voting set.
    """

    return {
        device_id
        for device_id in EXPECTED_DEVICES
        if not is_quarantined(device_id)
    }


def collect_snapshot(cycle_id: str) -> dict[str, dict[str, Any]] | None:
    """
    Determine whether a complete, fresh house snapshot is available.

    A snapshot contains every currently active (non-quarantined)
    device for that cycle.

    Returns:
        Snapshot dictionary when complete and fresh.
        None when more messages are required or data is stale.
    """

    active_devices = get_active_devices()

    if len(active_devices) < MIN_DEVICES_FOR_DECISION:
        print(
            "[SNAPSHOT] ❌ Not enough active devices "
            f"({len(active_devices)}) for a security decision"
        )
        return None

    cycle = snapshot_buffer.get(cycle_id)

    if not cycle:
        return None

    missing = active_devices - set(cycle.keys())

    if missing:
        print(
            f"[SNAPSHOT] Cycle {cycle_id}: "
            f"{len(cycle)}/{len(active_devices)} active devices"
        )
        print("[GATEWAY] Waiting for complete house snapshot...")
        return None

    now = time.time()

    for device_id in active_devices:
        message = cycle[device_id]

        received_at = float(
            message.get("_received_at", now)
        )

        age = now - received_at

        if age > SNAPSHOT_MAX_AGE:
            print(
                f"[SNAPSHOT] ❌ {device_id} observation expired"
            )
            return None

    snapshot_buffer.pop(cycle_id, None)

    if cycle_id in processed_cycles:
        return None

    processed_cycles.add(cycle_id)

    return {
        device_id: cycle[device_id]
        for device_id in active_devices
    }


def cleanup_old_snapshots() -> None:
    """
    Remove stale cycle buffers to prevent memory growth.
    """

    now = time.time()

    stale_cycles: list[str] = []

    for cycle_id, cycle in snapshot_buffer.items():

        if not cycle:
            stale_cycles.append(cycle_id)
            continue

        newest_time = max(
            float(message.get("_received_at", 0))
            for message in cycle.values()
        )

        if newest_time and now - newest_time > SNAPSHOT_MAX_AGE:
            stale_cycles.append(cycle_id)

    for cycle_id in stale_cycles:
        snapshot_buffer.pop(cycle_id, None)


# ============================================================
# QUARANTINED DEVICE RECOVERY
# ============================================================

def process_quarantined_device(
    device_id: str,
    message: dict[str, Any],
) -> None:
    """
    Observe a quarantined device without allowing it to vote.

    A quarantined device can only demonstrate recovery by agreeing
    with independent trusted devices.

    For this stage we keep the device completely excluded from the
    house quorum.
    """

    print(
        f"[RECOVERY] {device_id} is currently quarantined."
    )

    trusted_votes: dict[str, str] = {}

    for trusted_device_id, trusted_message in device_state.items():

        if trusted_device_id == device_id:
            continue

        if trusted_device_id not in EXPECTED_DEVICES:
            continue

        if is_quarantined(trusted_device_id):
            continue

        vote = convert_to_intrusion_vote(
            trusted_device_id,
            trusted_message.get("state"),
        )

        if vote is not None:
            trusted_votes[trusted_device_id] = vote

    quarantined_vote = convert_to_intrusion_vote(
        device_id,
        message.get("state"),
    )

    if not trusted_votes:
        print(
            "[RECOVERY] ❌ No independent trusted reference available."
        )
        return

    trusted_result = weighted_quorum(
        trusted_votes,
        {
            dev: get_trust(dev)
            for dev in trusted_votes
        },
    )

    trusted_reference = trusted_result["decision"]

    if trusted_reference in {"UNKNOWN", "UNCERTAIN"}:
        print(
            "[RECOVERY] ❌ Trusted reference is uncertain."
        )
        return

    print(
        "[RECOVERY] Trusted reference: "
        f"{trusted_reference} "
        f"({trusted_result['confidence'] * 100:.2f}%)"
    )

    if quarantined_vote == trusted_reference:

        print(
            f"[RECOVERY] ✅ {device_id}: "
            "agrees with independent trusted devices"
        )

        # Give a small positive trust signal when the existing
        # quarantine module allows recovery to begin.
        try:
            reward_agreement(device_id)
        except Exception:
            pass

    else:

        print(
            f"[RECOVERY] ❌ {device_id}: "
            f"reported {quarantined_vote}, "
            f"trusted reference says {trusted_reference}."
        )


# ============================================================
# HOUSE EVALUATION
# ============================================================

def evaluate_house(
    snapshot: dict[str, dict[str, Any]],
) -> None:
    """
    Run the complete Kerberos decision pipeline on one house snapshot.
    """

    global house_state

    if not snapshot:
        return

    print()
    print("=" * 60)
    print("[GATEWAY] ✅ FRESH HOUSE SNAPSHOT READY")
    print("=" * 60)

    for device_id, message in snapshot.items():
        print(
            f"  {device_id:<14} → "
            f"{message.get('state')}"
        )

    # --------------------------------------------------------
    # Physical consistency
    # --------------------------------------------------------

    states = {
        device_id: message.get("state")
        for device_id, message in snapshot.items()
    }

    conflicts = check_consistency(states)

    print()

    if conflicts:

        print("[CONSISTENCY] ⚠️ PHYSICAL CONFLICT")

        for conflict in conflicts:
            print(f"  → {conflict}")

    else:

        print(
            "[CONSISTENCY] ✅ Evidence consistent"
        )

    # --------------------------------------------------------
    # Convert sensor data into votes
    # --------------------------------------------------------

    votes: dict[str, str] = {}

    for device_id, message in snapshot.items():

        vote = convert_to_intrusion_vote(
            device_id,
            message.get("state"),
        )

        if vote is not None:
            votes[device_id] = vote

    if len(votes) < MIN_DEVICES_FOR_DECISION:

        print(
            "[QUORUM] ❌ Insufficient trusted evidence"
        )

        house_state = determine_state(
            intrusion_detected=False,
            quorum_confidence=0.0,
            trusted_device_count=len(votes),
            anomalous_devices=[],
            quarantined_devices=get_quarantined_devices(),
        )

        return

    # --------------------------------------------------------
    # Current trust scores
    # --------------------------------------------------------

    trust_scores = {
        device_id: get_trust(device_id)
        for device_id in votes
    }

    # --------------------------------------------------------
    # Trust-weighted quorum
    # --------------------------------------------------------

    quorum_result = weighted_quorum(
        votes,
        trust_scores,
    )

    decision = quorum_result["decision"]
    confidence = quorum_result["confidence"]

    print()
    print("[QUORUM] TRUST-WEIGHTED DECISION")

    for device_id, vote in votes.items():

        print(
            f"  {device_id:<14} → "
            f"{vote:<10} "
            f"trust={trust_scores.get(device_id, 0)}"
        )

    print()
    print(
        f"[QUORUM] Decision   : {decision}"
    )

    print(
        f"[QUORUM] Confidence : "
        f"{confidence * 100:.2f}%"
    )

    # --------------------------------------------------------
    # Trust update
    # --------------------------------------------------------

    winning_state = decision

    for device_id, vote in votes.items():

        try:

            if winning_state in {"INTRUSION", "SAFE"}:

                if vote == winning_state:

                    reward_agreement(device_id)

                else:

                    penalize_disagreement(device_id)

        except Exception as exc:

            print(
                f"[TRUST] ⚠️ Failed to update "
                f"{device_id}: {exc}"
            )

    # --------------------------------------------------------
    # Re-read trust after update
    # --------------------------------------------------------

    updated_trust_scores = {
        device_id: get_trust(device_id)
        for device_id in votes
    }

    for device_id, score in updated_trust_scores.items():

        print(
            f"[TRUST] {device_id}: {score}"
        )

    # --------------------------------------------------------
    # Anomaly detection
    # --------------------------------------------------------

    anomalous_devices: list[str] = []

    for device_id, vote in votes.items():

        is_bad_behavior = False

        if decision in {"INTRUSION", "SAFE"}:
            if vote != decision:
                is_bad_behavior = True

        try:
            record_behavior(
                device_id,
                is_bad_behavior,
            )
        except Exception as exc:
            print(
                f"[ANOMALY] ⚠️ Failed to record "
                f"{device_id}: {exc}"
            )

        try:
            if is_anomalous(device_id):
                anomalous_devices.append(device_id)

        except Exception:
            pass

    if anomalous_devices:

        for device_id in anomalous_devices:

            print(
                f"[ANOMALY] ⚠️ {device_id} "
                "behaviour anomaly detected"
            )

    # --------------------------------------------------------
    # Quarantine unreliable devices
    # --------------------------------------------------------

    for device_id in list(votes.keys()):

        score = get_trust(device_id)

        try:

            if should_quarantine(score):

                if not is_quarantined(device_id):

                    quarantine_device(
                        device_id,
                        reason="TRUST_THRESHOLD",
                        trust_score=score,
                    )

                    print()
                    print(
                        f"[DEFENSE] 🚫 {device_id} "
                        "QUARANTINED"
                    )

                    print(
                        f"[DEFENSE] Trust: {score}"
                    )

                    # Record the quarantine event.
                    try:

                        log_event(
                            "DEVICE_QUARANTINED",
                            {
                                "device": device_id,
                                "trust": score,
                                "reason": "TRUST_THRESHOLD",
                            },
                        )

                    except Exception as exc:

                        print(
                            f"[LOGGING] ⚠️ Failed to record "
                            f"quarantine event: {exc}"
                        )

        except Exception as exc:

            print(
                f"[QUARANTINE] ⚠️ Failed to process "
                f"{device_id}: {exc}"
            )

    # --------------------------------------------------------
    # Current quarantine state
    # --------------------------------------------------------

    quarantined_devices = sorted(
        get_quarantined_devices()
    )

    active_trusted_count = sum(
        1
        for device_id in votes
        if not is_quarantined(device_id)
    )
    # --------------------------------------------------------
    # Intrusion decision
    # --------------------------------------------------------

    intrusion_detected = (
        decision == "INTRUSION"
    )

    # --------------------------------------------------------
    # FSM
    # --------------------------------------------------------

    house_state = determine_state(
        intrusion_detected=intrusion_detected,
        quorum_confidence=confidence,
        trusted_device_count=active_trusted_count,
        anomalous_devices=anomalous_devices,
        quarantined_devices=quarantined_devices,
    )

    # --------------------------------------------------------
    # Security state display
    # --------------------------------------------------------

    print()
    print("=" * 60)
    print("[KERBEROS] HOUSE SECURITY STATE")
    print("=" * 60)

    print(
        f"State       : {house_state}"
    )

    print(
        f"Trusted     : "
        f"{active_trusted_count}"
    )

    print(
        f"Anomalous   : "
        f"{anomalous_devices}"
    )

    print(
        f"Quarantined : "
        f"{quarantined_devices}"
    )

    print()

    # --------------------------------------------------------
    # Fail-safe defense decision
    # --------------------------------------------------------

    actions = decide_actions(
        house_state,
        intrusion_detected=intrusion_detected,
    )

    print(
        "[DEFENSE] ACTION PLAN"
    )

    for action in actions:

        print(
            f"  → {action}"
        )

    # --------------------------------------------------------
    # Physical actuator execution
    # --------------------------------------------------------
    # --------------------------------------------------------
    # Security audit event
    # --------------------------------------------------------

    try:
        log_event(
            "SECURITY_DECISION",
            {
                "house_state": house_state,
                "decision": decision,
                "confidence": confidence,
                "trusted_device_count": active_trusted_count,
                "anomalous_devices": anomalous_devices,
                "quarantined_devices": quarantined_devices,
                "actions": actions,
            },
        )
    except Exception as exc:
        print(
            f"[LOGGING] ⚠️ Failed to record "
            f"security decision: {exc}"
        )

    executed_actions = execute_actions(
        actions
    )

    for action in executed_actions:

        print(
            f"[ACTUATOR] ✅ Executed: "
            f"{action}"
        )
    # --------------------------------------------------------
    # Publish live gateway state for the dashboard
    # --------------------------------------------------------

    live_devices = {}

    for device_id, message in snapshot.items():

        live_devices[device_id] = {
            "state": message.get("state"),
            "trust": get_trust(device_id),
            "status": (
                "QUARANTINED"
                if is_quarantined(device_id)
                else "TRUSTED"
            ),
        }

    publish_status(
        house_state=house_state,
        decision=decision,
        confidence=confidence,
        devices=live_devices,
        anomalous_devices=anomalous_devices,
        quarantined_devices=quarantined_devices,
    )
    print("=" * 60)


# ============================================================
# MQTT CONNECTION
# ============================================================

def on_connect(
    client: mqtt.Client,
    userdata: Any,
    flags: dict[str, Any],
    rc: int,
    properties: Any = None,
) -> None:
    """
    MQTT connection callback.
    """

    if rc == 0:

        print(
            "[MQTT] Connected to broker"
        )

        client.subscribe(
            SENSOR_TOPIC,
            qos=1,
        )

        print(
            f"[MQTT] Subscribed to: "
            f"{SENSOR_TOPIC}"
        )

    else:

        print(
            f"[MQTT] ❌ Connection failed "
            f"with return code {rc}"
        )


# ============================================================
# MQTT MESSAGE HANDLER
# ============================================================

def on_message(
    client: mqtt.Client,
    userdata: Any,
    msg: mqtt.MQTTMessage,
) -> None:
    """
    Validate and process one incoming sensor message.
    """

    global house_state

    cleanup_old_snapshots()

    print()
    print("-" * 60)

    # --------------------------------------------------------
    # Decode JSON
    # --------------------------------------------------------

    try:

        payload = msg.payload.decode("utf-8")

    except UnicodeDecodeError:

        print(
            "[MESSAGE] ❌ Invalid UTF-8 payload"
        )
        return

    try:

        data = json.loads(payload)

    except json.JSONDecodeError:

        print(
            "[MESSAGE] ❌ Invalid JSON"
        )
        return

    # --------------------------------------------------------
    # Validate basic message fields
    # --------------------------------------------------------

    device_id = data.get("device")
    cycle_id = data.get("cycle_id")
    timestamp = data.get("timestamp")
    nonce = data.get("nonce")
    signature = data.get("signature")

    if not device_id:

        print(
            "[MESSAGE] ❌ Missing device ID"
        )
        return

    print(
        f"[MESSAGE] Device: {device_id}"
    )

    if device_id not in EXPECTED_DEVICES:

        print(
            f"[SECURITY] ❌ Unknown device: "
            f"{device_id}"
        )
        return

    if not cycle_id:

        print(
            "[SECURITY] ❌ Missing cycle_id"
        )
        return

    if timestamp is None:

        print(
            "[SECURITY] ❌ Missing timestamp"
        )
        return

    if not nonce:

        print(
            "[SECURITY] ❌ Missing nonce"
        )
        return

    if not signature:

        print(
            "[SECURITY] ❌ Missing signature"
        )
        return

    # --------------------------------------------------------
    # HMAC authentication
    # --------------------------------------------------------

    signed_payload = {
        key: value
        for key, value in data.items()
        if key != "signature"
    }

    if not verify_signature(
        signed_payload,
        signature,
    ):

        print(
            "[SECURITY] ❌ HMAC verification FAILED"
        )

        return

    print(
        "[SECURITY] ✅ HMAC verified"
    )

    # --------------------------------------------------------
    # Freshness + replay protection
    # --------------------------------------------------------

    try:

        timestamp_value = float(timestamp)

    except (TypeError, ValueError):

        print(
            "[SECURITY] ❌ Invalid timestamp"
        )
        return

    try:

        fresh, reason = check_freshness(
            timestamp_value,
            nonce,
        )

    except Exception as exc:

        print(
            f"[SECURITY] ❌ Freshness check error: "
            f"{exc}"
        )
        return

    if not fresh:

        print(
            f"[SECURITY] ❌ {reason}"
        )

        # Apply the appropriate trust penalty.
        try:

            if reason == "REPLAY_DETECTED":
                penalize_replay(device_id)

            elif reason == "MESSAGE_TOO_OLD":
                penalize_stale(device_id)

        except Exception as exc:

            print(
                f"[TRUST] ⚠️ Penalty failed: "
                f"{exc}"
            )

        return

    print(
        "[SECURITY] ✅ Message is fresh"
    )

    # --------------------------------------------------------
    # Internal gateway metadata
    # --------------------------------------------------------

    now = time.time()

    data["_received_at"] = now

    device_state[device_id] = data
    device_last_seen[device_id] = now

    # --------------------------------------------------------
    # Quarantined device handling
    # --------------------------------------------------------

    if is_quarantined(device_id):

        process_quarantined_device(
            device_id,
            data,
        )

        return

    # --------------------------------------------------------
    # Add message to cycle buffer
    # --------------------------------------------------------

    cycle = snapshot_buffer.setdefault(
        cycle_id,
        {},
    )

    cycle[device_id] = data

    active_devices = get_active_devices()

    print(
        f"[SNAPSHOT] Cycle {cycle_id}: "
        f"{len(cycle)}/{len(active_devices)} "
        f"active devices"
    )

    # --------------------------------------------------------
    # Only evaluate complete snapshots.
    #
    # This is important:
    # We do NOT run the entire security pipeline after every
    # individual device message.
    # --------------------------------------------------------

    snapshot = collect_snapshot(
        cycle_id
    )

    if snapshot is None:

        return

    print(
        f"[SNAPSHOT] ✅ Complete cycle: "
        f"{cycle_id}"
    )

    # --------------------------------------------------------
    # Evaluate the house exactly once for this cycle.
    # --------------------------------------------------------

    evaluate_house(
        snapshot
    )


# ============================================================
# MAIN
# ============================================================

def create_mqtt_client() -> mqtt.Client:
    """
    Create and configure the MQTT client.
    """

    client = mqtt.Client(
        mqtt.CallbackAPIVersion.VERSION2
    )

    client.on_connect = on_connect
    client.on_message = on_message

    return client


def main() -> None:
    """
    Start the Kerberos security gateway.
    """

    print()
    print("=" * 60)
    print("        KERBEROS SECURITY GATEWAY")
    print("=" * 60)
    print()
    print(
        f"MQTT Broker : {BROKER}"
    )
    print(
        f"MQTT Topic  : {SENSOR_TOPIC}"
    )
    print()

    client = create_mqtt_client()

    print(
        "[GATEWAY] Connecting..."
    )

    try:

        client.connect(
            BROKER,
            PORT,
            60,
        )

    except Exception as exc:

        print(
            f"[GATEWAY] ❌ Unable to connect "
            f"to MQTT broker: {exc}"
        )

        return

    try:

        client.loop_forever()

    except KeyboardInterrupt:

        print()
        print(
            "[GATEWAY] Shutdown requested."
        )

    finally:

        try:
            client.disconnect()
        except Exception:
            pass


if __name__ == "__main__":
    main()