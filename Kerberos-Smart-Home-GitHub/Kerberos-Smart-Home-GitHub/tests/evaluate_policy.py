from __future__ import annotations

import random

from gateway.evidence_fusion import fuse_evidence
from gateway.policy import safety_decision
from gateway.quorum import weighted_quorum


DEVICES = [
    "door1",
    "pir1",
    "ultrasonic1",
    "camera1",
]


def generate_scenario() -> tuple[
    str,
    dict[str, str],
    dict[str, float],
    bool,
]:
    """
    Generate a synthetic smart-home security scenario.

    Returns:
        truth
        votes
        trust
        conflict_expected
    """

    truth = random.choice(
        ["SAFE", "INTRUSION"]
    )

    votes = {
        device: truth
        for device in DEVICES
    }

    trust = {
        device: random.uniform(55.0, 100.0)
        for device in DEVICES
    }

    # ---------------------------------------------------------
    # Sensor noise
    # ---------------------------------------------------------
    noise_probability = random.uniform(
        0.0,
        0.20,
    )

    for device in DEVICES:
        if random.random() < noise_probability:
            votes[device] = (
                "SAFE"
                if truth == "INTRUSION"
                else "INTRUSION"
            )

    # ---------------------------------------------------------
    # One compromised device
    # ---------------------------------------------------------
    if random.random() < 0.25:

        attacker = random.choice(DEVICES)

        votes[attacker] = (
            "SAFE"
            if truth == "INTRUSION"
            else "INTRUSION"
        )

        trust[attacker] = random.uniform(
            5.0,
            100.0,
        )

    # ---------------------------------------------------------
    # Two-device collusion
    # ---------------------------------------------------------
    if random.random() < 0.10:

        attackers = random.sample(
            DEVICES,
            2,
        )

        for attacker in attackers:

            votes[attacker] = (
                "SAFE"
                if truth == "INTRUSION"
                else "INTRUSION"
            )

            trust[attacker] = random.uniform(
                20.0,
                100.0,
            )

    # ---------------------------------------------------------
    # Device outage
    # ---------------------------------------------------------
    if random.random() < 0.10:

        missing = random.choice(
            DEVICES
        )

        votes.pop(
            missing,
            None,
        )

        trust.pop(
            missing,
            None,
        )

    # ---------------------------------------------------------
    # Explicit high-conflict scenario
    # ---------------------------------------------------------
    conflict_expected = False

    if random.random() < 0.12:

        conflict_expected = True

        ordered = random.sample(
            DEVICES,
            len(DEVICES),
        )

        midpoint = len(ordered) // 2

        opposite = (
            "SAFE"
            if truth == "INTRUSION"
            else "INTRUSION"
        )

        for index, device in enumerate(
            ordered
        ):
            votes[device] = (
                truth
                if index < midpoint
                else opposite
            )

            trust[device] = random.uniform(
                80.0,
                100.0,
            )

    return (
        truth,
        votes,
        trust,
        conflict_expected,
    )


def evaluate_decision(
    truth: str,
    decision: str,
    stats: dict[str, int],
) -> None:

    stats["total"] += 1

    if decision == "UNCERTAIN":

        stats["abstentions"] += 1
        return

    if decision == truth:

        stats["correct"] += 1

        if truth == "INTRUSION":
            stats["correct_intrusion"] += 1
        else:
            stats["correct_safe"] += 1

        return

    stats["incorrect"] += 1

    if (
        truth == "INTRUSION"
        and decision == "SAFE"
    ):
        stats["false_accept"] += 1

    elif (
        truth == "SAFE"
        and decision == "INTRUSION"
    ):
        stats["false_reject"] += 1


def finalize_rates(
    stats: dict[str, int],
) -> dict[str, float]:

    total = stats["total"]

    decided = (
        total
        - stats["abstentions"]
    )

    intrusion_cases = (
        stats["false_accept"]
        + stats["correct_intrusion"]
    )

    safe_cases = (
        stats["false_reject"]
        + stats["correct_safe"]
    )

    return {
        "accuracy": (
            stats["correct"] / total
            if total
            else 0.0
        ),
        "decision_accuracy": (
            stats["correct"] / decided
            if decided
            else 0.0
        ),
        "false_accept_rate": (
            stats["false_accept"]
            / intrusion_cases
            if intrusion_cases
            else 0.0
        ),
        "false_reject_rate": (
            stats["false_reject"]
            / safe_cases
            if safe_cases
            else 0.0
        ),
        "abstention_rate": (
            stats["abstentions"]
            / total
            if total
            else 0.0
        ),
    }


def new_stats() -> dict[str, int]:

    return {
        "total": 0,
        "correct": 0,
        "incorrect": 0,
        "false_accept": 0,
        "false_reject": 0,
        "abstentions": 0,
        "correct_intrusion": 0,
        "correct_safe": 0,
    }


def print_metrics(
    name: str,
    stats: dict[str, int],
) -> None:

    rates = finalize_rates(
        stats
    )

    print()
    print("=" * 72)
    print(name)
    print("=" * 72)

    print(
        f"Total scenarios:          "
        f"{stats['total']}"
    )

    print(
        f"Overall accuracy:         "
        f"{rates['accuracy'] * 100:.2f}%"
    )

    print(
        f"Decision accuracy:        "
        f"{rates['decision_accuracy'] * 100:.2f}%"
    )

    print(
        f"False accept rate:        "
        f"{rates['false_accept_rate'] * 100:.2f}%"
    )

    print(
        f"False reject rate:        "
        f"{rates['false_reject_rate'] * 100:.2f}%"
    )

    print(
        f"Abstention rate:          "
        f"{rates['abstention_rate'] * 100:.2f}%"
    )

    print(
        f"False accepts:            "
        f"{stats['false_accept']}"
    )

    print(
        f"False rejects:            "
        f"{stats['false_reject']}"
    )

    print(
        f"Abstentions:              "
        f"{stats['abstentions']}"
    )


def main() -> None:

    random.seed(42)

    scenario_count = 5000

    baseline = new_stats()
    raw_fusion = new_stats()
    policy_fusion = new_stats()

    for _ in range(
        scenario_count
    ):

        (
            truth,
            votes,
            trust,
            _conflict_expected,
        ) = generate_scenario()

        # =====================================================
        # 1. Existing weighted quorum
        # =====================================================

        quorum_result = weighted_quorum(
            votes,
            trust,
        )

        quorum_decision = quorum_result.get(
            "decision",
            "UNCERTAIN",
        )

        evaluate_decision(
            truth,
            quorum_decision,
            baseline,
        )

        # =====================================================
        # 2. Raw K-REAF
        # =====================================================

        fusion = fuse_evidence(
            votes,
            trust,
        )

        evaluate_decision(
            truth,
            fusion.decision,
            raw_fusion,
        )

        # =====================================================
        # 3. K-REAF + Safety Policy
        # =====================================================

        policy = safety_decision(
            belief_safe=fusion.belief_safe,
            belief_intrusion=fusion.belief_intrusion,
            uncertainty=fusion.uncertainty,
            conflict=fusion.conflict,
        )

        evaluate_decision(
            truth,
            policy.decision,
            policy_fusion,
        )

    # =========================================================
    # RESULTS
    # =========================================================

    print()
    print()
    print("#" * 72)
    print(
        "          KERBEROS THREE-WAY SECURITY EVALUATION"
    )
    print("#" * 72)

    print(
        f"\nRandomized scenarios evaluated: "
        f"{scenario_count}"
    )

    print_metrics(
        "1. BASELINE: TRUST-WEIGHTED QUORUM",
        baseline,
    )

    print_metrics(
        "2. RAW K-REAF",
        raw_fusion,
    )

    print_metrics(
        "3. K-REAF + SAFETY POLICY",
        policy_fusion,
    )

    # =========================================================
    # Comparison table
    # =========================================================

    baseline_rates = finalize_rates(
        baseline
    )

    fusion_rates = finalize_rates(
        raw_fusion
    )

    policy_rates = finalize_rates(
        policy_fusion
    )

    print()
    print("=" * 90)
    print("COMPARISON")
    print("=" * 90)

    header = (
        f"{'METRIC':<25}"
        f"{'QUORUM':<15}"
        f"{'K-REAF':<15}"
        f"{'K-REAF+POLICY':<20}"
    )

    print(header)
    print("-" * 90)

    rows = [
        (
            "Accuracy",
            baseline_rates["accuracy"],
            fusion_rates["accuracy"],
            policy_rates["accuracy"],
        ),
        (
            "Decision accuracy",
            baseline_rates["decision_accuracy"],
            fusion_rates["decision_accuracy"],
            policy_rates["decision_accuracy"],
        ),
        (
            "False accept rate",
            baseline_rates["false_accept_rate"],
            fusion_rates["false_accept_rate"],
            policy_rates["false_accept_rate"],
        ),
        (
            "False reject rate",
            baseline_rates["false_reject_rate"],
            fusion_rates["false_reject_rate"],
            policy_rates["false_reject_rate"],
        ),
        (
            "Abstention rate",
            baseline_rates["abstention_rate"],
            fusion_rates["abstention_rate"],
            policy_rates["abstention_rate"],
        ),
    ]

    for (
        metric,
        quorum_value,
        fusion_value,
        policy_value,
    ) in rows:

        print(
            f"{metric:<25}"
            f"{quorum_value * 100:>10.2f}%     "
            f"{fusion_value * 100:>10.2f}%     "
            f"{policy_value * 100:>14.2f}%"
        )

    # =========================================================
    # Security improvement
    # =========================================================

    print()
    print("=" * 90)
    print("SECURITY-FOCUSED COMPARISON")
    print("=" * 90)

    baseline_fa = (
        baseline_rates["false_accept_rate"]
    )

    policy_fa = (
        policy_rates["false_accept_rate"]
    )

    reduction = (
        baseline_fa - policy_fa
    )

    print(
        f"Baseline false-accept rate: "
        f"{baseline_fa * 100:.2f}%"
    )

    print(
        f"K-REAF + policy false-accept rate: "
        f"{policy_fa * 100:.2f}%"
    )

    print(
        f"Security delta: "
        f"{reduction * 100:+.2f} percentage points"
    )

    if reduction > 0:
        print(
            "\n✅ Safety policy reduced unsafe "
            "false-accept decisions."
        )
    elif reduction < 0:
        print(
            "\n⚠️ Safety policy increased "
            "false-accept decisions."
        )
    else:
        print(
            "\n➖ Safety policy produced no "
            "change in false-accept rate."
        )


if __name__ == "__main__":
    main()