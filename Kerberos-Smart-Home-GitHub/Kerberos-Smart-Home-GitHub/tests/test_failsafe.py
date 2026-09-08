from gateway.failsafe import decide_actions
from gateway.fsm import (
    SAFE,
    ALERT,
    DEGRADED,
    LOCKDOWN,
)


print("=" * 60)
print("       KERBEROS FAIL-SAFE DEFENSE TEST")
print("=" * 60)


cases = [
    ("SAFE", SAFE, False),
    ("ALERT", ALERT, True),
    ("DEGRADED", DEGRADED, True),
    ("LOCKDOWN", LOCKDOWN, True),
]


for name, state, intrusion in cases:

    print(f"\n[{name}]")
    print("-" * 60)

    actions = decide_actions(
        state,
        intrusion_detected=intrusion
    )

    print(f"Security state : {state}")
    print("Defensive actions:")

    for action in actions:
        print(f"  → {action}")


print("\n" + "=" * 60)
print("EXPECTED DEFENSE MODEL")
print("=" * 60)

print("""
SAFE
  → Normal operation

ALERT
  → Lock door
  → Activate alarm
  → Log intrusion

DEGRADED
  → Maintain safe lock state
  → Log degraded operation

LOCKDOWN
  → Lock door
  → Activate alarm
  → Block remote unlock
  → Log lockdown
""")

print("=" * 60)