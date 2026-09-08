from __future__ import annotations

import copy
from pprint import pprint

from gateway.command_guardian import (
    evaluate_command,
)
from gateway.evidence_fusion import fuse_evidence
from gateway.quorum import weighted_quorum
from security.owner_auth import verify_owner_command


def print_banner(title: str) -> None:
    print()
    print("=" * 78)
    print(title)
    print("=" * 78)


def evaluate_owner_command(
    *,
    command: dict,
    votes: dict[str, str],
    trust: dict[str, float],
    behavior_anomaly: float,
    used_nonces: set[str],
) -> dict:
    """
    Complete Owner's Voice decision pipeline.

    Owner command
        ↓
    Authentication + freshness
        ↓
    Quorum
        ↓
    K-REAF evidence fusion
        ↓
    Command Guardian
    """

    # ---------------------------------------------------------
    # 1. Authenticate owner command
    # ---------------------------------------------------------

    authenticated, auth_reason = verify_owner_command(
        command,
        used_nonces=used_nonces,
    )

    print(
        f"[OWNER AUTH] "
        f"{'✅ PASS' if authenticated else '❌ FAIL'} "
        f"- {auth_reason}"
    )

    if not authenticated:
        return {
            "decision": "REFUSE",
            "reason": (
                f"Owner command authentication failed: "
                f"{auth_reason}"
            ),
        }

    # ---------------------------------------------------------
    # 2. Existing weighted quorum
    # ---------------------------------------------------------

    quorum = weighted_quorum(
        votes,
        trust,
    )

    house_state = quorum.get(
        "decision",
        "UNCERTAIN",
    )

    quorum_confidence = float(
        quorum.get(
            "confidence",
            0.0,
        )
    )

    print(
        f"[QUORUM] "
        f"Decision={house_state} "
        f"Confidence={quorum_confidence * 100:.2f}%"
    )

    # ---------------------------------------------------------
    # 3. K-REAF
    # ---------------------------------------------------------

    fusion = fuse_evidence(
        votes,
        trust,
    )

    print(
        f"[K-REAF] "
        f"Decision={fusion.decision} "
        f"SAFE={fusion.belief_safe * 100:.2f}% "
        f"INTRUSION={fusion.belief_intrusion * 100:.2f}% "
        f"Conflict={fusion.conflict * 100:.2f}% "
        f"Uncertainty={fusion.uncertainty * 100:.2f}%"
    )

    # ---------------------------------------------------------
    # 4. Command Guardian
    # ---------------------------------------------------------

    guardian = evaluate_command(
        action=command["action"],
        owner_authenticated=True,
        command_fresh=True,
        house_state=(
            "ALERT"
            if house_state == "INTRUSION"
            else house_state
        ),
        quorum_confidence=quorum_confidence,
        k_reaf_conflict=fusion.conflict,
        k_reaf_uncertainty=fusion.uncertainty,
        behavior_anomaly=behavior_anomaly,
        k_reaf_belief_intrusion=fusion.belief_intrusion,
    )

    print(
        f"[GUARDIAN] "
        f"Decision={guardian.decision} "
        f"Risk={guardian.risk * 100:.2f}%"
    )

    print(
        f"[GUARDIAN] "
        f"Reason={guardian.reason}"
    )

    return {
        "decision": guardian.decision,
        "reason": guardian.reason,
        "risk": guardian.risk,
        "house_state": house_state,
        "quorum_confidence": quorum_confidence,
        "k_reaf_decision": fusion.decision,
        "k_reaf_belief_safe": fusion.belief_safe,
        "k_reaf_belief_intrusion": fusion.belief_intrusion,
        "k_reaf_conflict": fusion.conflict,
        "k_reaf_uncertainty": fusion.uncertainty,
    }


def scenario_1_legitimate_unlock() -> None:
    """
    Scenario 1:
        Legitimate owner
        Safe house
        Normal behavior

    Expected:
        ALLOW
    """

    print_banner(
        "SCENARIO 1 — LEGITIMATE OWNER + SAFE HOUSE"
    )

    from security.owner_auth import build_owner_command

    command = build_owner_command(
        "owner1",
        "UNLOCK_DOOR",
    )

    votes = {
        "door1": "SAFE",
        "pir1": "SAFE",
        "ultrasonic1": "SAFE",
        "camera1": "SAFE",
    }

    trust = {
        "door1": 100,
        "pir1": 100,
        "ultrasonic1": 100,
        "camera1": 100,
    }

    result = evaluate_owner_command(
        command=command,
        votes=votes,
        trust=trust,
        behavior_anomaly=0.05,
        used_nonces=set(),
    )

    print(f"[RESULT] {result['decision']}")

    assert result["decision"] == "ALLOW"


def scenario_2_unlock_during_intrusion() -> None:
    """
    Scenario 2:
        Legitimate owner
        Physical evidence indicates intrusion

    Expected:
        REFUSE
    """

    print_banner(
        "SCENARIO 2 — OWNER UNLOCK DURING INTRUSION"
    )

    from security.owner_auth import build_owner_command

    command = build_owner_command(
        "owner1",
        "UNLOCK_DOOR",
    )

    votes = {
        "door1": "INTRUSION",
        "pir1": "INTRUSION",
        "ultrasonic1": "INTRUSION",
        "camera1": "INTRUSION",
    }

    trust = {
        "door1": 100,
        "pir1": 100,
        "ultrasonic1": 100,
        "camera1": 100,
    }

    result = evaluate_owner_command(
        command=command,
        votes=votes,
        trust=trust,
        behavior_anomaly=0.05,
        used_nonces=set(),
    )

    print(f"[RESULT] {result['decision']}")

    assert result["decision"] == "REFUSE"


def scenario_3_conflicting_evidence() -> None:
    """
    Scenario 3:
        Legitimate owner
        Evidence is strongly contradictory

    Expected:
        HOLD_FOR_CONFIRMATION
    """

    print_banner(
        "SCENARIO 3 — OWNER UNLOCK + CONFLICTING EVIDENCE"
    )

    from security.owner_auth import build_owner_command

    command = build_owner_command(
        "owner1",
        "UNLOCK_DOOR",
    )

    votes = {
        "door1": "SAFE",
        "pir1": "SAFE",
        "ultrasonic1": "INTRUSION",
        "camera1": "INTRUSION",
    }

    trust = {
        "door1": 100,
        "pir1": 100,
        "ultrasonic1": 100,
        "camera1": 100,
    }

    result = evaluate_owner_command(
        command=command,
        votes=votes,
        trust=trust,
        behavior_anomaly=0.05,
        used_nonces=set(),
    )

    print(f"[RESULT] {result['decision']}")

    assert result["decision"] == "HOLD_FOR_CONFIRMATION"


def scenario_4_abnormal_owner_behavior() -> None:
    """
    Scenario 4:
        Owner is authenticated
        House is otherwise safe
        Command is behaviorally unusual

    Expected:
        HOLD_FOR_CONFIRMATION
    """

    print_banner(
        "SCENARIO 4 — ABNORMAL OWNER BEHAVIOR"
    )

    from security.owner_auth import build_owner_command

    command = build_owner_command(
        "owner1",
        "UNLOCK_DOOR",
    )

    votes = {
        "door1": "SAFE",
        "pir1": "SAFE",
        "ultrasonic1": "SAFE",
        "camera1": "SAFE",
    }

    trust = {
        "door1": 100,
        "pir1": 100,
        "ultrasonic1": 100,
        "camera1": 100,
    }

    result = evaluate_owner_command(
        command=command,
        votes=votes,
        trust=trust,
        behavior_anomaly=0.90,
        used_nonces=set(),
    )

    print(f"[RESULT] {result['decision']}")

    assert result["decision"] == "HOLD_FOR_CONFIRMATION"


def scenario_5_tampered_command() -> None:
    """
    Scenario 5:
        Attacker modifies a legitimately signed command.

    Expected:
        REFUSE
    """

    print_banner(
        "SCENARIO 5 — TAMPERED OWNER COMMAND"
    )

    from security.owner_auth import build_owner_command

    command = build_owner_command(
        "owner1",
        "UNLOCK_DOOR",
    )

    # Attacker changes the command after signing.
    tampered_command = copy.deepcopy(
        command
    )

    tampered_command["action"] = "LOCK_DOOR"

    votes = {
        "door1": "SAFE",
        "pir1": "SAFE",
        "ultrasonic1": "SAFE",
        "camera1": "SAFE",
    }

    trust = {
        "door1": 100,
        "pir1": 100,
        "ultrasonic1": 100,
        "camera1": 100,
    }

    result = evaluate_owner_command(
        command=tampered_command,
        votes=votes,
        trust=trust,
        behavior_anomaly=0.05,
        used_nonces=set(),
    )

    print(f"[RESULT] {result['decision']}")

    assert result["decision"] == "REFUSE"


def scenario_6_replay_command() -> None:
    """
    Scenario 6:
        Same valid owner command is submitted twice.

    Expected:
        First  -> ALLOW
        Second -> REFUSE
    """

    print_banner(
        "SCENARIO 6 — REPLAYED OWNER COMMAND"
    )

    from security.owner_auth import build_owner_command

    command = build_owner_command(
        "owner1",
        "UNLOCK_DOOR",
    )

    votes = {
        "door1": "SAFE",
        "pir1": "SAFE",
        "ultrasonic1": "SAFE",
        "camera1": "SAFE",
    }

    trust = {
        "door1": 100,
        "pir1": 100,
        "ultrasonic1": 100,
        "camera1": 100,
    }

    used_nonces: set[str] = set()

    first = evaluate_owner_command(
        command=command,
        votes=votes,
        trust=trust,
        behavior_anomaly=0.05,
        used_nonces=used_nonces,
    )

    second = evaluate_owner_command(
        command=command,
        votes=votes,
        trust=trust,
        behavior_anomaly=0.05,
        used_nonces=used_nonces,
    )

    print(
        f"[FIRST RESULT]  {first['decision']}"
    )

    print(
        f"[SECOND RESULT] {second['decision']}"
    )

    assert first["decision"] == "ALLOW"
    assert second["decision"] == "REFUSE"


def main() -> None:

    scenario_1_legitimate_unlock()
    scenario_2_unlock_during_intrusion()
    scenario_3_conflicting_evidence()
    scenario_4_abnormal_owner_behavior()
    scenario_5_tampered_command()
    scenario_6_replay_command()

    print()
    print("=" * 78)
    print(
        "✅ ALL END-TO-END OWNER COMMAND SCENARIOS PASSED"
    )
    print("=" * 78)


if __name__ == "__main__":
    main()