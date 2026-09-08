from __future__ import annotations

import random
from dataclasses import dataclass

from gateway.evidence_fusion import fuse_evidence
from gateway.quorum import weighted_quorum


DEVICES = [
    "door1",
    "pir1",
    "ultrasonic1",
    "camera1",
]

STATES = {
    "SAFE",
    "INTRUSION",
}


@dataclass
class Scenario:
    truth: str
    votes: dict[str, str]
    trust: dict[str, float]
    conflict_expected: bool


@dataclass
class Metrics:
    total: int = 0
    correct: int = 0
    incorrect: int = 0
    false_accept: int = 0
    false_reject: int = 0
    abstentions: int = 0
    conflicts: int = 0
    conflict_detected: int = 0

    def accuracy(self) -> float:
        if self.total == 0:
            return 0.0
        return self.correct / self.total

    def false_accept_rate(self) -> float:
        intrusion_cases = self.false_accept + self.correct_intrusion_cases()
        if intrusion_cases == 0:
            return 0.0
        return self.false_accept / intrusion_cases

    def false_reject_rate(self) -> float:
        safe_cases = self.false_reject + self.correct_safe_cases()
        if safe_cases == 0:
            return 0.0
        return self.false_reject / safe_cases

    def correct_intrusion_cases(self) -> int:
        return getattr(self, "_correct_intrusion", 0)

    def correct_safe_cases(self) -> int:
        return getattr(self, "_correct_safe", 0)

    def abstention_rate(self) -> float:
        if self.total == 0:
            return 0.0
        return self.abstentions / self.total

    def decided_accuracy(self) -> float:
        decided = self.total - self.abstentions
        if decided == 0:
            return 0.0
        return self.correct / decided

    def conflict_detection_rate(self) -> float:
        if self.conflicts == 0:
            return 0.0
        return self.conflict_detected / self.conflicts


def clamp(value: float, low: float = 5.0, high: float = 100.0) -> float:
    return max(low, min(high, value))


def random_trust() -> float:
    return round(random.uniform(55.0, 100.0), 2)


def make_base_trust() -> dict[str, float]:
    return {
        device: random_trust()
        for device in DEVICES
    }


def generate_scenario() -> Scenario:
    """
    Generate realistic synthetic smart-home evidence.

    The generator deliberately includes:
      - normal operation
      - genuine intrusion
      - noisy sensors
      - one compromised device
      - two compromised devices
      - missing devices
      - low-trust attackers
      - high-trust attackers
      - conflicting evidence
    """

    truth = random.choice(["SAFE", "INTRUSION"])

    trust = make_base_trust()

    votes: dict[str, str] = {}

    # ---------------------------------------------------------
    # 1. Start with mostly honest evidence.
    # ---------------------------------------------------------
    for device in DEVICES:
        votes[device] = truth

    # ---------------------------------------------------------
    # 2. Sensor noise.
    # ---------------------------------------------------------
    noise_probability = random.uniform(0.0, 0.20)

    for device in DEVICES:
        if random.random() < noise_probability:
            votes[device] = (
                "INTRUSION"
                if truth == "SAFE"
                else "SAFE"
            )

    # ---------------------------------------------------------
    # 3. Single compromised device.
    # ---------------------------------------------------------
    if random.random() < 0.25:
        attacker = random.choice(DEVICES)

        votes[attacker] = (
            "SAFE"
            if truth == "INTRUSION"
            else "INTRUSION"
        )

        attacker_mode = random.choice(
            [
                "low_trust",
                "medium_trust",
                "high_trust",
            ]
        )

        if attacker_mode == "low_trust":
            trust[attacker] = random.uniform(5.0, 35.0)
        elif attacker_mode == "medium_trust":
            trust[attacker] = random.uniform(35.0, 65.0)
        else:
            trust[attacker] = random.uniform(80.0, 100.0)

    # ---------------------------------------------------------
    # 4. Two compromised devices / collusion.
    # ---------------------------------------------------------
    if random.random() < 0.10:
        attackers = random.sample(DEVICES, 2)

        for attacker in attackers:
            votes[attacker] = (
                "SAFE"
                if truth == "INTRUSION"
                else "INTRUSION"
            )

            # Sometimes attackers have artificially high trust.
            trust[attacker] = random.uniform(30.0, 100.0)

    # ---------------------------------------------------------
    # 5. Random device outage.
    # ---------------------------------------------------------
    if random.random() < 0.10:
        missing = random.choice(DEVICES)
        votes.pop(missing, None)
        trust.pop(missing, None)

    # ---------------------------------------------------------
    # 6. Explicit high-conflict cases.
    # ---------------------------------------------------------
    conflict_expected = False

    if random.random() < 0.12:

        conflict_expected = True

        shuffled_devices = random.sample(
            DEVICES,
            len(DEVICES),
        )

        half = len(shuffled_devices) // 2

        for index, device in enumerate(shuffled_devices):
            votes[device] = (
                truth
                if index < half
                else (
                    "SAFE"
                    if truth == "INTRUSION"
                    else "INTRUSION"
                )
            )

            trust[device] = random.uniform(
                80.0,
                100.0,
            )

    return Scenario(
        truth=truth,
        votes=votes,
        trust=trust,
        conflict_expected=conflict_expected,
    )


def update_metrics_baseline(
    metrics: Metrics,
    truth: str,
    decision: str,
) -> None:

    metrics.total += 1

    if decision == "UNCERTAIN":
        metrics.abstentions += 1
        return

    if decision not in STATES:
        metrics.abstentions += 1
        return

    if decision == truth:

        metrics.correct += 1

        if truth == "INTRUSION":
            metrics._correct_intrusion = (
                getattr(metrics, "_correct_intrusion", 0) + 1
            )
        else:
            metrics._correct_safe = (
                getattr(metrics, "_correct_safe", 0) + 1
            )

        return

    metrics.incorrect += 1

    if truth == "INTRUSION" and decision == "SAFE":
        metrics.false_accept += 1

    elif truth == "SAFE" and decision == "INTRUSION":
        metrics.false_reject += 1


def update_metrics_fusion(
    metrics: Metrics,
    truth: str,
    decision: str,
    conflict: float,
    conflict_expected: bool,
) -> None:

    update_metrics_baseline(
        metrics,
        truth,
        decision,
    )

    # Only count conflict detection on scenarios intentionally
    # generated with conflicting evidence.
    if conflict_expected:
        metrics.conflicts += 1

        if conflict >= 0.50:
            metrics.conflict_detected += 1


def print_metrics(
    name: str,
    metrics: Metrics,
) -> None:

    print()
    print("=" * 72)
    print(name)
    print("=" * 72)

    print(
        f"Total scenarios:          {metrics.total}"
    )

    print(
        f"Overall accuracy:         "
        f"{metrics.accuracy() * 100:.2f}%"
    )

    print(
        f"Decision accuracy:        "
        f"{metrics.decided_accuracy() * 100:.2f}%"
    )

    print(
        f"False accept rate:        "
        f"{metrics.false_accept_rate() * 100:.2f}%"
    )

    print(
        f"False reject rate:        "
        f"{metrics.false_reject_rate() * 100:.2f}%"
    )

    print(
        f"Abstention rate:          "
        f"{metrics.abstention_rate() * 100:.2f}%"
    )

    if metrics.conflicts > 0:
        print(
            f"Conflict detection rate:  "
            f"{metrics.conflict_detection_rate() * 100:.2f}%"
        )

    print(
        f"False accepts:            {metrics.false_accept}"
    )

    print(
        f"False rejects:            {metrics.false_reject}"
    )

    print(
        f"Abstentions:              {metrics.abstentions}"
    )


def main() -> None:

    random.seed(42)

    scenario_count = 5000

    baseline_metrics = Metrics()
    fusion_metrics = Metrics()

    for _ in range(scenario_count):

        scenario = generate_scenario()

        # -----------------------------------------------------
        # Existing trust-weighted quorum
        # -----------------------------------------------------
        quorum_result = weighted_quorum(
            scenario.votes,
            scenario.trust,
        )

        quorum_decision = quorum_result.get(
            "decision",
            "UNCERTAIN",
        )

        update_metrics_baseline(
            baseline_metrics,
            scenario.truth,
            quorum_decision,
        )

        # -----------------------------------------------------
        # K-REAF
        # -----------------------------------------------------
        fusion_result = fuse_evidence(
            scenario.votes,
            scenario.trust,
        )

        fusion_decision = fusion_result.decision
        fusion_conflict = float(
            fusion_result.conflict
        )

        update_metrics_fusion(
            fusion_metrics,
            scenario.truth,
            fusion_decision,
            fusion_conflict,
            scenario.conflict_expected,
        )

    print()
    print()
    print("#" * 72)
    print("              KERBEROS SECURITY EVALUATION")
    print("#" * 72)
    print()
    print(
        f"Randomized scenarios evaluated: {scenario_count}"
    )

    print_metrics(
        "BASELINE: TRUST-WEIGHTED QUORUM",
        baseline_metrics,
    )

    print_metrics(
        "K-REAF: EVIDENCE FUSION",
        fusion_metrics,
    )

    print()
    print("=" * 72)
    print("COMPARISON")
    print("=" * 72)

    accuracy_delta = (
        fusion_metrics.accuracy()
        - baseline_metrics.accuracy()
    )

    fa_delta = (
        fusion_metrics.false_accept_rate()
        - baseline_metrics.false_accept_rate()
    )

    fr_delta = (
        fusion_metrics.false_reject_rate()
        - baseline_metrics.false_reject_rate()
    )

    abstention_delta = (
        fusion_metrics.abstention_rate()
        - baseline_metrics.abstention_rate()
    )

    print(
        f"Accuracy delta:          "
        f"{accuracy_delta * 100:+.2f} percentage points"
    )

    print(
        f"False accept delta:      "
        f"{fa_delta * 100:+.2f} percentage points"
    )

    print(
        f"False reject delta:      "
        f"{fr_delta * 100:+.2f} percentage points"
    )

    print(
        f"Abstention delta:        "
        f"{abstention_delta * 100:+.2f} percentage points"
    )

    print()
    print(
        "Interpretation:"
    )
    print(
        "  Lower false-accept rate is better for security."
    )
    print(
        "  Lower false-reject rate is better for usability."
    )
    print(
        "  Abstention is not automatically a failure:"
    )
    print(
        "  it represents cases where the system refuses"
    )
    print(
        "  to make an unsafe forced decision."
    )


if __name__ == "__main__":
    main()