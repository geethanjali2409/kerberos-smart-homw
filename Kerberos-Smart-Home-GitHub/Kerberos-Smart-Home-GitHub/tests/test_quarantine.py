from gateway.quarantine import (
    should_quarantine,
    quarantine_device,
    is_quarantined,
    release_device,
    get_quarantined_devices,
)


print("=" * 60)
print("       KERBEROS DEVICE QUARANTINE TEST")
print("=" * 60)


device = "camera1"


# ---------------------------------------------------------
# CASE 1 — TRUSTED DEVICE
# ---------------------------------------------------------

print("\n[CASE 1] Trusted device")
print("-" * 60)

trust = 85

print(f"Device : {device}")
print(f"Trust  : {trust}")

if should_quarantine(trust):
    print("Result : 🚫 QUARANTINE")
else:
    print("Result : ✅ DEVICE TRUSTED")


# ---------------------------------------------------------
# CASE 2 — LOW TRUST DEVICE
# ---------------------------------------------------------

print("\n[CASE 2] Low-trust device")
print("-" * 60)

trust = 35

print(f"Device : {device}")
print(f"Trust  : {trust}")

if should_quarantine(trust):

    quarantine_device(device)

    print("Result : 🚫 QUARANTINED")

else:
    print("Result : ✅ DEVICE TRUSTED")


# ---------------------------------------------------------
# CASE 3 — VERIFY QUARANTINE
# ---------------------------------------------------------

print("\n[CASE 3] Verify quarantine status")
print("-" * 60)

print(
    f"{device} quarantined : "
    f"{is_quarantined(device)}"
)

print(
    "Quarantined devices :",
    get_quarantined_devices()
)


# ---------------------------------------------------------
# CASE 4 — RELEASE
# ---------------------------------------------------------

print("\n[CASE 4] Release device")
print("-" * 60)

release_device(device)

print(
    f"{device} quarantined : "
    f"{is_quarantined(device)}"
)


print("\n" + "=" * 60)
print("QUARANTINE SYSTEM COMPLETE")
print("=" * 60)