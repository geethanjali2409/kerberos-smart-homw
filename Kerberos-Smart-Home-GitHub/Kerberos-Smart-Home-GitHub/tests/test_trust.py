from gateway.trust import (
    get_trust,
    reward_agreement,
    penalize_disagreement,
    penalize_replay,
    is_quarantined
)


DEVICE = "door1"


print("=" * 50)
print("       KERBEROS TRUST SYSTEM TEST")
print("=" * 50)


print("\nInitial trust:")

print(
    DEVICE,
    "→",
    get_trust(DEVICE)
)


print("\nGood behavior:")

reward_agreement(DEVICE)

print(
    DEVICE,
    "→",
    get_trust(DEVICE)
)


print("\nDisagreement:")

penalize_disagreement(DEVICE)

print(
    DEVICE,
    "→",
    get_trust(DEVICE)
)


print("\nReplay attack:")

penalize_replay(DEVICE)

print(
    DEVICE,
    "→",
    get_trust(DEVICE)
)


print("\nQuarantine status:")

print(
    DEVICE,
    "→",
    is_quarantined(DEVICE)
)