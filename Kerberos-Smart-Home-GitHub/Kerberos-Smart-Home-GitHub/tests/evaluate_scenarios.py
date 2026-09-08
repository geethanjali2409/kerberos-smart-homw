from __future__ import annotations

from dataclasses import dataclass

from gateway.evidence_fusion import fuse_evidence
from gateway.policy import safety_decision
from gateway.quorum import weighted_quorum


DEVICES = [
    "door1",
    "pir1",
    "ultrasonic1",
    "camera1",
]


@dataclass
class ScenarioResult:
    truth: str
    scenario: str
    votes: dict[str, str]
    trust: dict[str, float]


def make_result(
    name: str,
    truth: str,
    votes: dict[str, str],
    trust: dict[str, float],
) -> ScenarioResult:
    return ScenarioResult(
        truth=truth,
        scenario=name,
        votes=votes,
        trust=trust,
    )


def generate_scenarios() -> list[ScenarioResult]:
    """
    Controlled scenarios.

    Each class is intentionally deterministic so we can see
    exactly which conditions cause false accepts/rejects.
    """

    scenarios: list[ScenarioResult] = []

    # =========================================================
    # SAFE STATES
    # =========================================================

    scenarios.append(
        make_result(
            "SAFE: all agree",
            "SAFE",
            {
                "door1": "SAFE",
                "pir1": "SAFE",
                "ultrasonic1": "SAFE",
                "camera1": "SAFE",
            },
            {
                "door1": 100,
                "pir1": 100,
                "ultrasonic1": 100,
                "camera1": 100,
            },
        )
    )

    scenarios.append(
        make_result(
            "SAFE: noisy PIR",
            "SAFE",
            {
                "door1": "SAFE",
                "pir1": "INTRUSION",
                "ultrasonic1": "SAFE",
                "camera1": "SAFE",
            },
            {
                "door1": 100,
                "pir1": 70,
                "ultrasonic1": 100,
                "camera1": 100,
            },
        )
    )

    scenarios.append(
        make_result(
            "SAFE: noisy ultrasonic",
            "SAFE",
            {
                "door1": "SAFE",
                "pir1": "SAFE",
                "ultrasonic1": "INTRUSION",
                "camera1": "SAFE",
            },
            {
                "door1": 100,
                "pir1": 100,
                "ultrasonic1": 70,
                "camera1": 100,
            },
        )
    )

    scenarios.append(
        make_result(
            "SAFE: weak compromised device",
            "SAFE",
            {
                "door1": "SAFE",
                "pir1": "SAFE",
                "ultrasonic1": "SAFE",
                "camera1": "INTRUSION",
            },
            {
                "door1": 100,
                "pir1": 100,
                "ultrasonic1": 100,
                "camera1": 20,
            },
        )
    )

    scenarios.append(
        make_result(
            "SAFE: high-trust liar",
            "SAFE",
            {
                "door1": "SAFE",
                "pir1": "SAFE",
                "ultrasonic1": "SAFE",
                "camera1": "INTRUSION",
            },
            {
                "door1": 100,
                "pir1": 100,
                "ultrasonic1": 100,
                "camera1": 95,
            },
        )
    )

    scenarios.append(
        make_result(
            "SAFE: one device missing",
            "SAFE",
            {
                "door1": "SAFE",
                "pir1": "SAFE",
                "ultrasonic1": "SAFE",
            },
            {
                "door1": 100,
                "pir1": 100,
                "ultrasonic1": 100,
            },
        )
    )

    scenarios.append(
        make_result(
            "SAFE: two-vs-two conflict",
            "SAFE",
            {
                "door1": "SAFE",
                "pir1": "SAFE",
                "ultrasonic1": "INTRUSION",
                "camera1": "INTRUSION",
            },
            {
                "door1": 100,
                "pir1": 100,
                "ultrasonic1": 100,
                "camera1": 100,
            },
        )
    )

    # =========================================================
    # INTRUSION STATES
    # =========================================================

    scenarios.append(
        make_result(
            "INTRUSION: all agree",
            "INTRUSION",
            {
                "door1": "INTRUSION",
                "pir1": "INTRUSION",
                "ultrasonic1": "INTRUSION",
                "camera1": "INTRUSION",
            },
            {
                "door1": 100,
                "pir1": 100,
                "ultrasonic1": 100,
                "camera1": 100,
            },
        )
    )

    scenarios.append(
        make_result(
            "INTRUSION: noisy PIR",
            "INTRUSION",
            {
                "door1": "INTRUSION",
                "pir1": "SAFE",
                "ultrasonic1": "INTRUSION",
                "camera1": "INTRUSION",
            },
            {
                "door1": 100,
                "pir1": 70,
                "ultrasonic1": 100,
                "camera1": 100,
            },
        )
    )

    scenarios.append(
        make_result(
            "INTRUSION: noisy ultrasonic",
            "INTRUSION",
            {
                "door1": "INTRUSION",
                "pir1": "INTRUSION",
                "ultrasonic1": "SAFE",
                "camera1": "INTRUSION",
            },
            {
                "door1": 100,
                "pir1": 100,
                "ultrasonic1": 70,
                "camera1": 100,
            },
        )
    )

    scenarios.append(
        make_result(
            "INTRUSION: weak compromised camera",
            "INTRUSION",
            {
                "door1": "INTRUSION",
                "pir1": "INTRUSION",
                "ultrasonic1": "INTRUSION",
                "camera1": "SAFE",
            },
            {
                "door1": 100,
                "pir1": 100,
                "ultrasonic1": 100,
                "camera1": 20,
            },
        )
    )

    scenarios.append(
        make_result(
            "INTRUSION: high-trust compromised camera",
            "INTRUSION",
            {
                "door1": "INTRUSION",
                "pir1": "INTRUSION",
                "ultrasonic1": "INTRUSION",
                "camera1": "SAFE",
            },
            {
                "door1": 100,
                "pir1": 100,
                "ultrasonic1": 100,
                "camera1": 95,
            },
        )
    )

    scenarios.append(
        make_result(
            "INTRUSION: one device missing",
            "INTRUSION",
            {
                "door1": "INTRUSION",
                "pir1": "INTRUSION",
                "ultrasonic1": "INTRUSION",
            },
            {
                "door1": 100,
                "pir1": 100,
                "ultrasonic1": 100,
            },
        )
    )

    scenarios.append(
        make_result(
            "INTRUSION: two-vs-two conflict",
            "INTRUSION",
            {
                "door1": "INTRUSION",
                "pir1": "INTRUSION",
                "ultrasonic1": "SAFE",
                "camera1": "SAFE",
            },
            {
                "door1": 100,
                "pir1": 100,
                "ultrasonic1": 100,
                "camera1": 100,
            },
        )
    )

    scenarios.append(
        make_result(
            "INTRUSION: two compromised devices",
            "INTRUSION",
            {
                "door1": "INTRUSION",
                "pir1": "INTRUSION",
                "ultrasonic1": "SAFE",
                "camera1": "SAFE",
            },
            {
                "door1": 100,
                "pir1": 100,
                "ultrasonic1": 85,
                "camera1": 85,
            },
        )
    )

    return scenarios


def print_header() -> None:
    print()
    print("=" * 125)
    print("                         KERBEROS SCENARIO ANALYSIS")
    print("=" * 125)

    print(
        f"{'SCENARIO':<42}"
        f"{'TRUTH':<12}"
        f"{'QUORUM':<14}"
        f"{'K-REAF':<14}"
        f"{'POLICY':<14}"
        f"{'CONFLICT':<12}"
        f"{'RISK':<10}"
    )

    print("-" * 125)


def classify(
    truth: str,
    decision: str,
) -> str:
    if decision == "UNCERTAIN":
        return "ABSTAIN"

    if decision == truth:
        return "CORRECT"

    if truth == "INTRUSION" and decision == "SAFE":
        return "FALSE_ACCEPT"

    if truth == "SAFE" and decision == "INTRUSION":
        return "FALSE_REJECT"

    return "OTHER"


def main() -> None:
    scenarios = generate_scenarios()

    print_header()

    summary = {
        "quorum_correct": 0,
        "quorum_false_accept": 0,
        "quorum_false_reject": 0,
        "quorum_abstain": 0,

        "fusion_correct": 0,
        "fusion_false_accept": 0,
        "fusion_false_reject": 0,
        "fusion_abstain": 0,

        "policy_correct": 0,
        "policy_false_accept": 0,
        "policy_false_reject": 0,
        "policy_abstain": 0,
    }

    for scenario in scenarios:

        quorum = weighted_quorum(
            scenario.votes,
            scenario.trust,
        )

        fusion = fuse_evidence(
            scenario.votes,
            scenario.trust,
        )

        policy = safety_decision(
            belief_safe=fusion.belief_safe,
            belief_intrusion=fusion.belief_intrusion,
            uncertainty=fusion.uncertainty,
            conflict=fusion.conflict,
        )

        quorum_decision = quorum.get(
            "decision",
            "UNCERTAIN",
        )

        fusion_decision = fusion.decision
        policy_decision = policy.decision

        quorum_class = classify(
            scenario.truth,
            quorum_decision,
        )

        fusion_class = classify(
            scenario.truth,
            fusion_decision,
        )

        policy_class = classify(
            scenario.truth,
            policy_decision,
        )

        summary[
            f"quorum_{quorum_class.lower()}"
        ] += 1

        summary[
            f"fusion_{fusion_class.lower()}"
        ] += 1

        summary[
            f"policy_{policy_class.lower()}"
        ] += 1

        print(
            f"{scenario.scenario:<42}"
            f"{scenario.truth:<12}"
            f"{quorum_decision:<14}"
            f"{fusion_decision:<14}"
            f"{policy_decision:<14}"
            f"{fusion.conflict * 100:>8.2f}%   "
            f"{policy.risk * 100:>6.2f}%"
        )

    # =========================================================
    # SUMMARY
    # =========================================================

    print()
    print("=" * 125)
    print("SUMMARY")
    print("=" * 125)

    systems = [
        (
            "BASELINE QUORUM",
            "quorum",
        ),
        (
            "RAW K-REAF",
            "fusion",
        ),
        (
            "K-REAF + POLICY",
            "policy",
        ),
    ]

    for name, prefix in systems:

        correct = summary[
            f"{prefix}_correct"
        ]

        false_accept = summary[
            f"{prefix}_false_accept"
        ]

        false_reject = summary[
            f"{prefix}_false_reject"
        ]

        abstain = summary[
            f"{prefix}_abstain"
        ]

        total = (
            correct
            + false_accept
            + false_reject
            + abstain
        )

        accuracy = (
            correct / total
            if total
            else 0.0
        )

        print()
        print(name)
        print("-" * 50)

        print(
            f"Correct:          {correct}"
        )

        print(
            f"False accepts:    {false_accept}"
        )

        print(
            f"False rejects:    {false_reject}"
        )

        print(
            f"Abstentions:      {abstain}"
        )

        print(
            f"Accuracy:         "
            f"{accuracy * 100:.2f}%"
        )

    print()
    print("=" * 125)
    print("FAILURE ANALYSIS")
    print("=" * 125)

    for scenario in scenarios:

        quorum = weighted_quorum(
            scenario.votes,
            scenario.trust,
        )

        fusion = fuse_evidence(
            scenario.votes,
            scenario.trust,
        )

        policy = safety_decision(
            belief_safe=fusion.belief_safe,
            belief_intrusion=fusion.belief_intrusion,
            uncertainty=fusion.uncertainty,
            conflict=fusion.conflict,
        )

        if (
            classify(
                scenario.truth,
                policy.decision,
            )
            in {
                "FALSE_ACCEPT",
                "FALSE_REJECT",
            }
        ):

            print()
            print(
                f"Scenario: {scenario.scenario}"
            )

            print(
                f"Truth: {scenario.truth}"
            )

            print(
                f"Quorum: {quorum.get('decision')}"
            )

            print(
                f"K-REAF: {fusion.decision}"
            )

            print(
                f"Policy: {policy.decision}"
            )

            print(
                f"Belief SAFE: "
                f"{fusion.belief_safe:.4f}"
            )

            print(
                f"Belief INTRUSION: "
                f"{fusion.belief_intrusion:.4f}"
            )

            print(
                f"Conflict: "
                f"{fusion.conflict:.4f}"
            )

            print(
                f"Uncertainty: "
                f"{fusion.uncertainty:.4f}"
            )

            print(
                f"Risk: "
                f"{policy.risk:.4f}"
            )

            print(
                f"Reason: "
                f"{policy.reason}"
            )


if __name__ == "__main__":
    main()