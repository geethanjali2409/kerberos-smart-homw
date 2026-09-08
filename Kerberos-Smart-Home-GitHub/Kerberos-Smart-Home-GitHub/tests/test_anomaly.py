from gateway.anomaly import (
    record_behavior,
    is_anomalous,
)


DEVICE = "camera1"


print("=" * 60)
print("       KERBEROS ANOMALY DETECTION TEST")
print("=" * 60)


print("\n[PHASE 1] Normal behavior")
print("-" * 60)

for i in range(5):

    rate = record_behavior(
        DEVICE,
        False
    )

    print(
        f"Message {i + 1}: "
        f"bad_behavior_rate={rate:.2f}"
    )


print(
    "\nAnomalous:",
    is_anomalous(DEVICE)
)


print("\n[PHASE 2] Device starts behaving badly")
print("-" * 60)

for i in range(10):

    rate = record_behavior(
        DEVICE,
        True
    )

    print(
        f"Attack {i + 1}: "
        f"bad_behavior_rate={rate:.2f}"
    )

    if is_anomalous(DEVICE):

        print(
            "⚠️ ANOMALY THRESHOLD EXCEEDED"
        )

        break


print("\nFinal status:")
print(
    f"Device     : {DEVICE}"
)

print(
    f"Anomalous  : "
    f"{'YES 🚨' if is_anomalous(DEVICE) else 'NO ✅'}"
)

print("=" * 60)