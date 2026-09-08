from gateway.evidence_fusion import fuse_evidence


def run_test(
    name: str,
    votes: dict[str, str],
    trust: dict[str, float],
) -> None:

    result = fuse_evidence(
        votes,
        trust,
    )

    print()
    print("=" * 60)
    print(name)
    print("=" * 60)

    print(
        f"Belief SAFE       : "
        f"{result.belief_safe:.4f}"
    )

    print(
        f"Belief INTRUSION  : "
        f"{result.belief_intrusion:.4f}"
    )

    print(
        f"Uncertainty       : "
        f"{result.uncertainty:.4f}"
    )

    print(
        f"Conflict          : "
        f"{result.conflict:.4f}"
    )

    print(
        f"Decision           : "
        f"{result.decision}"
    )

    print(
        f"Confidence         : "
        f"{result.confidence:.4f}"
    )


def main() -> None:

    # --------------------------------------------------------
    # Test 1: Everyone agrees SAFE
    # --------------------------------------------------------

    run_test(
        "ALL DEVICES AGREE SAFE",
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

    # --------------------------------------------------------
    # Test 2: Everyone agrees INTRUSION
    # --------------------------------------------------------

    run_test(
        "ALL DEVICES AGREE INTRUSION",
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

    # --------------------------------------------------------
    # Test 3: Compromised camera
    # --------------------------------------------------------

    run_test(
        "COMPROMISED CAMERA",
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
    )

    # --------------------------------------------------------
    # Test 4: Equal conflict
    # --------------------------------------------------------

    run_test(
        "HIGH-CONFLICT EVIDENCE",
        {
            "pir1": "INTRUSION",
            "camera1": "SAFE",
        },
        {
            "pir1": 100,
            "camera1": 100,
        },
    )


if __name__ == "__main__":
    main()