from gateway.command_guardian import (
    ALLOW,
    HOLD_FOR_CONFIRMATION,
    REFUSE,
    evaluate_command,
)


def test_valid_owner_unlock_safe_house():
    result = evaluate_command(
        action="UNLOCK_DOOR",
        owner_authenticated=True,
        command_fresh=True,
        house_state="SAFE",
        quorum_confidence=0.95,
        k_reaf_conflict=0.05,
        k_reaf_uncertainty=0.02,
        behavior_anomaly=0.05,
        k_reaf_belief_intrusion=0.01,
    )

    assert result.decision == ALLOW


def test_owner_unlock_during_intrusion():
    result = evaluate_command(
        action="UNLOCK_DOOR",
        owner_authenticated=True,
        command_fresh=True,
        house_state="ALERT",
        quorum_confidence=0.95,
        k_reaf_conflict=0.60,
        k_reaf_uncertainty=0.02,
        behavior_anomaly=0.05,
        k_reaf_belief_intrusion=0.95,
    )

    assert result.decision == REFUSE


def test_unauthenticated_owner_command():
    result = evaluate_command(
        action="UNLOCK_DOOR",
        owner_authenticated=False,
        command_fresh=True,
        house_state="SAFE",
        quorum_confidence=0.95,
        k_reaf_conflict=0.01,
        k_reaf_uncertainty=0.01,
        behavior_anomaly=0.01,
        k_reaf_belief_intrusion=0.01,
    )

    assert result.decision == REFUSE


def test_replayed_or_stale_owner_command():
    result = evaluate_command(
        action="UNLOCK_DOOR",
        owner_authenticated=True,
        command_fresh=False,
        house_state="SAFE",
        quorum_confidence=0.95,
        k_reaf_conflict=0.01,
        k_reaf_uncertainty=0.01,
        behavior_anomaly=0.01,
        k_reaf_belief_intrusion=0.01,
    )

    assert result.decision == REFUSE


def test_high_conflict_unlock_requires_confirmation():
    result = evaluate_command(
        action="UNLOCK_DOOR",
        owner_authenticated=True,
        command_fresh=True,
        house_state="SAFE",
        quorum_confidence=0.75,
        k_reaf_conflict=0.90,
        k_reaf_uncertainty=0.10,
        behavior_anomaly=0.05,
        k_reaf_belief_intrusion=0.20,
    )

    assert result.decision == HOLD_FOR_CONFIRMATION


def test_high_uncertainty_unlock_requires_confirmation():
    result = evaluate_command(
        action="UNLOCK_DOOR",
        owner_authenticated=True,
        command_fresh=True,
        house_state="SAFE",
        quorum_confidence=0.75,
        k_reaf_conflict=0.40,
        k_reaf_uncertainty=0.60,
        behavior_anomaly=0.05,
        k_reaf_belief_intrusion=0.20,
    )

    assert result.decision == HOLD_FOR_CONFIRMATION


def test_unusual_owner_unlock_requires_confirmation():
    result = evaluate_command(
        action="UNLOCK_DOOR",
        owner_authenticated=True,
        command_fresh=True,
        house_state="SAFE",
        quorum_confidence=0.90,
        k_reaf_conflict=0.05,
        k_reaf_uncertainty=0.02,
        behavior_anomaly=0.90,
        k_reaf_belief_intrusion=0.01,
    )

    assert result.decision == HOLD_FOR_CONFIRMATION


def test_lock_command_is_allowed():
    result = evaluate_command(
        action="LOCK_DOOR",
        owner_authenticated=True,
        command_fresh=True,
        house_state="SAFE",
        quorum_confidence=0.50,
        k_reaf_conflict=0.90,
        k_reaf_uncertainty=0.20,
        behavior_anomaly=0.05,
        k_reaf_belief_intrusion=0.01,
    )

    assert result.decision == ALLOW


def test_unknown_command_is_refused():
    result = evaluate_command(
        action="OPEN_GARAGE",
        owner_authenticated=True,
        command_fresh=True,
        house_state="SAFE",
        quorum_confidence=0.95,
        k_reaf_conflict=0.01,
        k_reaf_uncertainty=0.01,
        behavior_anomaly=0.01,
        k_reaf_belief_intrusion=0.01,
    )

    assert result.decision == REFUSE


if __name__ == "__main__":
    tests = [
        test_valid_owner_unlock_safe_house,
        test_owner_unlock_during_intrusion,
        test_unauthenticated_owner_command,
        test_replayed_or_stale_owner_command,
        test_high_conflict_unlock_requires_confirmation,
        test_high_uncertainty_unlock_requires_confirmation,
        test_unusual_owner_unlock_requires_confirmation,
        test_lock_command_is_allowed,
        test_unknown_command_is_refused,
    ]

    for test in tests:
        test()
        print(f"[PASS] {test.__name__}")

    print()
    print("✅ ALL COMMAND GUARDIAN TESTS PASSED")