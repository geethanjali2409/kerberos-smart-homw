from gateway.consistency import check_consistency


print("=" * 60)
print("       KERBEROS CONSISTENCY ENGINE TEST")
print("=" * 60)


print("\n[CASE 1] All devices agree")
print("-" * 60)

states = {
    "door1": "OPEN",
    "pir1": "MOTION",
    "ultrasonic1": "PERSON",
    "camera1": "MOTION"
}

conflicts = check_consistency(states)

print("States:")
for device, state in states.items():
    print(f"  {device:<12} → {state}")

if conflicts:
    print("\nResult: ⚠️ CONFLICT")
    for conflict in conflicts:
        print(" -", conflict)
else:
    print("\nResult: ✅ CONSISTENT")


print("\n[CASE 2] Camera lies")
print("-" * 60)

states = {
    "door1": "OPEN",
    "pir1": "MOTION",
    "ultrasonic1": "PERSON",
    "camera1": "NO_MOTION"
}

conflicts = check_consistency(states)

print("States:")
for device, state in states.items():
    print(f"  {device:<12} → {state}")

if conflicts:
    print("\nResult: ⚠️ CONFLICT DETECTED")

    for conflict in conflicts:
        print(" -", conflict)
else:
    print("\nResult: ✅ CONSISTENT")