from gateway.fsm import (
    SAFE,
    ALERT,
    DEGRADED,
    LOCKDOWN,
    determine_state,
)


print("=" * 60)
print("       KERBEROS SECURITY FSM TEST")
print("=" * 60)


# ---------------------------------------------------------
# CASE 1 — NORMAL
# ---------------------------------------------------------

print("\n[CASE 1] Normal house")
print("-" * 60)

state = determine_state(
    intrusion_detected=False,
    quorum_confidence=0.0,
    trusted_device_count=4,
    anomalous_devices=[],
    quarantined_devices=[],
)

print("State:", state)


# ---------------------------------------------------------
# CASE 2 — STRONG INTRUSION
# ---------------------------------------------------------

print("\n[CASE 2] Strong trusted intrusion evidence")
print("-" * 60)

state = determine_state(
    intrusion_detected=True,
    quorum_confidence=0.89,
    trusted_device_count=4,
    anomalous_devices=[],
    quarantined_devices=[],
)

print("State:", state)


# ---------------------------------------------------------
# CASE 3 — ANOMALOUS CAMERA
# ---------------------------------------------------------

print("\n[CASE 3] Camera becomes anomalous")
print("-" * 60)

state = determine_state(
    intrusion_detected=False,
    quorum_confidence=0.0,
    trusted_device_count=3,
    anomalous_devices=["camera1"],
    quarantined_devices=[],
)

print("State:", state)


# ---------------------------------------------------------
# CASE 4 — INTRUSION + ANOMALOUS CAMERA
# ---------------------------------------------------------

print("\n[CASE 4] Intrusion confirmed despite anomalous camera")
print("-" * 60)

state = determine_state(
    intrusion_detected=True,
    quorum_confidence=0.89,
    trusted_device_count=3,
    anomalous_devices=["camera1"],
    quarantined_devices=["camera1"],
)

print("State:", state)


# ---------------------------------------------------------
# CASE 5 — MULTIPLE COMPROMISED DEVICES
# ---------------------------------------------------------

print("\n[CASE 5] Multiple devices quarantined")
print("-" * 60)

state = determine_state(
    intrusion_detected=True,
    quorum_confidence=0.65,
    trusted_device_count=2,
    anomalous_devices=["camera1", "pir1"],
    quarantined_devices=["camera1", "pir1"],
)

print("State:", state)


# ---------------------------------------------------------
# CASE 6 — ONLY ONE TRUSTED DEVICE LEFT
# ---------------------------------------------------------

print("\n[CASE 6] Only one trusted device remains")
print("-" * 60)

state = determine_state(
    intrusion_detected=True,
    quorum_confidence=0.60,
    trusted_device_count=1,
    anomalous_devices=["camera1", "pir1"],
    quarantined_devices=["camera1", "pir1"],
)

print("State:", state)


print("\n" + "=" * 60)
print("EXPECTED MODEL")
print("=" * 60)

print("""
SAFE       → Normal operation
ALERT      → Strong trusted intrusion evidence
DEGRADED   → Suspicious/conflicting evidence
LOCKDOWN   → Severe compromise / insufficient trust
""")

print("=" * 60)