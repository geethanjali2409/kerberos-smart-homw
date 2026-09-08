import json
import time
import uuid

import paho.mqtt.publish as publish

from security.auth import create_signature


BROKER = "test.mosquitto.org"

DEVICE_ID = "door1"

TOPIC = f"kerberos/sensors/{DEVICE_ID}"


def send_door_state(is_open):

    # Create the message
    message = {
        "device": DEVICE_ID,
        "type": "door",
        "doorOpen": is_open,
        "timestamp": time.time(),
        "nonce": str(uuid.uuid4())
    }

    # Sign the complete message
    signature = create_signature(message)

    # Add the signature
    message["signature"] = signature

    payload = json.dumps(message)

    print()
    print("[DEVICE] Sending authenticated message:")
    print(payload)

    publish.single(
        TOPIC,
        payload,
        hostname=BROKER
    )


print("=" * 50)
print("       KERBEROS DEVICE SIMULATOR")
print("=" * 50)

print()

print(f"Device : {DEVICE_ID}")
print(f"Topic  : {TOPIC}")

print()

print("[DEVICE] Starting...")


while True:

    send_door_state(True)

    time.sleep(3)

    send_door_state(False)

    time.sleep(3)