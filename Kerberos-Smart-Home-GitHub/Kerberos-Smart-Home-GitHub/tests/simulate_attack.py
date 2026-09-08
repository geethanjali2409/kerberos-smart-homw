import json
import time
import uuid

import paho.mqtt.publish as publish

from security.auth import create_signature


BROKER = "127.0.0.1"

ATTACK_CYCLES = 8

DEVICES = [
    "door1",
    "pir1",
    "ultrasonic1",
    "camera1",
]


def send_device(device_id, device_type, state, cycle_id):
    """
    Send an authenticated device observation.

    The attack simulator intentionally gives camera1 a false
    observation while still generating a valid HMAC using the
    legitimate camera credential.
    """

    message = {
        "device": device_id,
        "type": device_type,
        "state": state,
        "cycle_id": cycle_id,
        "timestamp": time.time(),
        "nonce": str(uuid.uuid4()),
    }

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
        f"[ATTACK] {device_id:<12}"
        f"state={state:<12}"
        f"HMAC=VALID"
    )


def send_attack_cycle():
    """
    Send one intrusion cycle in which the camera lies.
    """

    cycle_id = str(uuid.uuid4())

    print()
    print("=" * 60)
    print("[ATTACK] COMPROMISED CAMERA SCENARIO")
    print("=" * 60)

    print(f"Cycle: {cycle_id}")
    print()

    # Trusted physical evidence:
    send_device(
        "door1",
        "door",
        "OPEN",
        cycle_id,
    )

    send_device(
        "pir1",
        "motion",
        "MOTION",
        cycle_id,
    )

    send_device(
        "ultrasonic1",
        "distance",
        "PERSON",
        cycle_id,
    )

    # Malicious camera:
    # physically there is motion, but camera claims there is none.
    send_device(
        "camera1",
        "camera",
        "NO_MOTION",
        cycle_id,
    )


print("=" * 60)
print("       KERBEROS ATTACK SIMULATOR")
print("=" * 60)

print()
print("Attack: compromised camera")
print("Camera credential: VALID")
print("Camera observation: FALSE")
print()

for cycle_number in range(1, ATTACK_CYCLES + 1):

    print(
        f"\n[ATTACK] Cycle "
        f"{cycle_number}/{ATTACK_CYCLES}"
    )

    send_attack_cycle()

    time.sleep(3)


print()
print("=" * 60)
print("ATTACK SIMULATION COMPLETE")
print("=" * 60)