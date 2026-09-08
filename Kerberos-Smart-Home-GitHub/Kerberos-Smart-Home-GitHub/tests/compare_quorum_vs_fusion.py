from __future__ import annotations

from gateway.evidence_fusion import fuse_evidence
from gateway.quorum import weighted_quorum


def evaluate(
    name: str,
    votes: dict[str, str],
    trust: dict[str, float],
) -> dict[str, str]:
    """
    Run the same scenario through:
        1. Existing weighted quorum
        2. K-REAF evidence fusion
    """

    quorum = weighted_quorum(
        votes,
        trust,
    )

    fusion = fuse_evidence(
        votes,
        trust,
    )

    return {
        "scenario": name,
        "quorum": str(
            quorum.get(
                "decision",
                "UNKNOWN",
            )
        ),
        "quorum_conf": f"{quorum.get('confidence', 0.0) * 100:.2f}%",
        "k_reaf": fusion.decision,
        "k_reaf_conf": f"{fusion.confidence * 100:.2f}%",
        "k_reaf_conflict": f"{fusion.conflict * 100:.2f}%",
        "k_reaf_uncertainty": f"{fusion.uncertainty * 100:.2f}%",
    }


def print_results(results: list[dict[str, str]]) -> None:
    print()
    print("=" * 112)
    print("                 BASELINE QUORUM vs K-REAF")
    print("=" * 112)

    header = (
        f"{'SCENARIO':<30}"
        f"{'QUORUM':<16}"
        f"{'Q CONF':<10}"
        f"{'K-REAF':<16}"
        f"{'KR CONF':<10}"
        f"{'CONFLICT':<12}"
        f"{'UNCERTAINTY':<14}"
    )

    print(header)
    print("-" * 112)

    for result in results:

        print(
            f"{result['scenario']:<30}"
            f"{result['quorum']:<16}"
            f"{result['quorum_conf']:<10}"
            f"{result['k_reaf']:<16}"
            f"{result['k_reaf_conf']:<10}"
            f"{result['k_reaf_conflict']:<12}"
            f"{result['k_reaf_uncertainty']:<14}"
        )

    print("-" * 112)


def main() -> None:

    scenarios = [

        (
            "All devices SAFE",
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
        ),

        (
            "All devices INTRUSION",
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
        ),

        (
            "Compromised camera",
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
                "camera1": 40,
            },
        ),

        (
            "Low-trust camera lies",
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
                "camera1": 10,
            },
        ),

        (
            "Two vs two conflict",
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
        ),

        (
            "Single-device conflict",
            {
                "pir1": "INTRUSION",
                "camera1": "SAFE",
            },
            {
                "pir1": 100,
                "camera1": 100,
            },
        ),

        (
            "Missing camera",
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
        ),

        (
            "One trusted device vs weak liar",
            {
                "door1": "INTRUSION",
                "pir1": "INTRUSION",
                "ultrasonic1": "INTRUSION",
                "camera1": "SAFE",
            },
            {
                "door1": 90,
                "pir1": 90,
                "ultrasonic1": 90,
                "camera1": 20,
            },
        ),

        (
            "All devices disagree pairwise",
            {
                "door1": "INTRUSION",
                "pir1": "SAFE",
                "ultrasonic1": "INTRUSION",
                "camera1": "SAFE",
            },
            {
                "door1": 100,
                "pir1": 100,
                "ultrasonic1": 100,
                "camera1": 100,
            },
        ),

    ]

    results = []

    for name, votes, trust in scenarios:

        results.append(
            evaluate(
                name,
                votes,
                trust,
            )
        )

    print_results(results)


if __name__ == "__main__":
    main()