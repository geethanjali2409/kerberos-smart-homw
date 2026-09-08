from gateway.quorum import weighted_quorum


print("=" * 60)
print("       KERBEROS TRUST-WEIGHTED QUORUM TEST")
print("=" * 60)


# ---------------------------------------------------------
# CASE 1 — ALL DEVICES AGREE
# ---------------------------------------------------------

print("\n[CASE 1] All devices agree")
print("-" * 60)

votes = {
    "door1": "INTRUSION",
    "pir1": "INTRUSION",
    "ultrasonic1": "INTRUSION",
    "camera1": "INTRUSION"
}

trust_scores = {
    "door1": 95,
    "pir1": 97,
    "ultrasonic1": 94,
    "camera1": 90
}

result = weighted_quorum(
    votes,
    trust_scores
)

print("Votes:")
for device, vote in votes.items():
    print(
        f"  {device:<12} → "
        f"{vote:<10} "
        f"trust={trust_scores[device]}"
    )

print("\nDecision   :", result["decision"])
print(
    "Confidence :",
    f"{result['confidence']:.2%}"
)


# ---------------------------------------------------------
# CASE 2 — CAMERA LIES
# ---------------------------------------------------------

print("\n[CASE 2] Camera reports SAFE while others detect intrusion")
print("-" * 60)

votes = {
    "door1": "INTRUSION",
    "pir1": "INTRUSION",
    "ultrasonic1": "INTRUSION",
    "camera1": "SAFE"
}

trust_scores = {
    "door1": 95,
    "pir1": 97,
    "ultrasonic1": 94,
    "camera1": 35
}

result = weighted_quorum(
    votes,
    trust_scores
)

print("Votes:")
for device, vote in votes.items():
    print(
        f"  {device:<12} → "
        f"{vote:<10} "
        f"trust={trust_scores[device]}"
    )

print("\nWeighted evidence:")

for state, weight in result["weighted_votes"].items():
    print(
        f"  {state:<10} → "
        f"{weight}"
    )

print("\nDecision   :", result["decision"])
print(
    "Confidence :",
    f"{result['confidence']:.2%}"
)


# ---------------------------------------------------------
# FINAL INTERPRETATION
# ---------------------------------------------------------

print("\n" + "=" * 60)

if result["decision"] == "INTRUSION":
    print("✅ TRUSTED MAJORITY OVERRIDES LOW-TRUST DEVICE")

else:
    print("⚠️ NO STRONG QUORUM")

print("=" * 60)