import json
import time
import uuid

import paho.mqtt.publish as publish

from security.auth import create_signature


BROKER = "127.0.0.1"


def send_device(device_id, device_type, state, cycle_id):
    """
    Create and send one authenticated observation
    belonging to a specific house-security cycle.
    """

    message = {
        "device": device_id,
        "type": device_type,
        "state": state,
        "cycle_id": cycle_id,
        "timestamp": time.time(),
        "nonce": str(uuid.uuid4()),
    }

    # Sign the complete message before adding the signature.
    signature = create_signature(message)

    message["signature"] = signature

    topic = f"kerberos/sensors/{device_id}"

    publish.single(
        topic,
        json.dumps(message),
        hostname=BROKER,
        port=1883,
    )

    print(
        f"[HOUSE] {device_id:<12} "
        f"{device_type:<12} "
        f"state={state}"
    )


def send_house_cycle(states):
    """
    Generate one unique cycle ID and send all device
    observations belonging to that same cycle.
    """

    cycle_id = str(uuid.uuid4())

    print()
    print(f"[HOUSE] Cycle: {cycle_id}")

    for device_id, device_type, state in states:
        send_device(
            device_id,
            device_type,
            state,
            cycle_id,
        )

        time.sleep(0.1)


print("=" * 60)
print("          KERBEROS SMART HOME SIMULATOR")
print("=" * 60)

print()
print(f"[HOUSE] MQTT broker: {BROKER}")
print("[HOUSE] Starting simulated devices...")
print()


while True:

    # -----------------------------------------------------
    # NORMAL
    # -----------------------------------------------------

    print()
    print("--- HOUSE STATE: NORMAL ---")

    send_house_cycle([
        ("door1", "door", "CLOSED"),
        ("pir1", "motion", "NO_MOTION"),
        ("ultrasonic1", "distance", "NO_PERSON"),
        ("camera1", "camera", "NO_MOTION"),
    ])

    time.sleep(5)


    # -----------------------------------------------------
    # INTRUSION
    # -----------------------------------------------------

    print()
    print("--- HOUSE STATE: INTRUSION ---")

    send_house_cycle([
        ("door1", "door", "OPEN"),
        ("pir1", "motion", "MOTION"),
        ("ultrasonic1", "distance", "PERSON"),
        ("camera1", "camera", "MOTION"),
    ])

    time.sleep(5)