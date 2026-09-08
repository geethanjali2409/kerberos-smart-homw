from __future__ import annotations

from dataclasses import dataclass
from typing import Any


SAFE = "SAFE"
INTRUSION = "INTRUSION"
UNKNOWN = "UNKNOWN"


@dataclass
class EvidenceResult:
    """
    Result of multi-device evidence fusion.

    belief_safe:
        Final belief specifically supporting SAFE.

    belief_intrusion:
        Final belief specifically supporting INTRUSION.

    uncertainty:
        Remaining unresolved evidence.

    conflict:
        Direct contradiction between SAFE and INTRUSION evidence.

    decision:
        SAFE / INTRUSION / UNCERTAIN

    confidence:
        Strength of the selected decision.
    """

    belief_safe: float
    belief_intrusion: float
    uncertainty: float
    conflict: float
    decision: str
    confidence: float

    def as_dict(self) -> dict[str, Any]:
        return {
            "belief_safe": self.belief_safe,
            "belief_intrusion": self.belief_intrusion,
            "uncertainty": self.uncertainty,
            "conflict": self.conflict,
            "decision": self.decision,
            "confidence": self.confidence,
        }


def clamp(
    value: float,
    minimum: float = 0.0,
    maximum: float = 1.0,
) -> float:
    return max(
        minimum,
        min(maximum, float(value)),
    )


def normalize_trust(
    trust_score: float,
) -> float:
    """
    Convert trust from 0-100 to 0-1.
    """

    return clamp(
        float(trust_score) / 100.0
    )


def observation_to_mass(
    observation: str,
    trust_score: float,
) -> dict[str, float]:
    """
    Convert one observation into a basic belief assignment.

    Higher trust:
        stronger committed evidence.

    Lower trust:
        more uncertainty.

    The residual UNKNOWN mass represents the fact that even a
    reliable physical sensor is not absolute truth.
    """

    trust = normalize_trust(
        trust_score
    )

    normalized = (
        str(observation)
        .strip()
        .upper()
    )

    if normalized not in {
        SAFE,
        INTRUSION,
    }:

        return {
            SAFE: 0.0,
            INTRUSION: 0.0,
            UNKNOWN: 1.0,
        }

    # Keep a non-zero uncertainty floor.
    commitment = (
        0.50
        + (0.47 * trust)
    )

    uncertainty = (
        1.0 - commitment
    )

    if normalized == SAFE:

        return {
            SAFE: commitment,
            INTRUSION: 0.0,
            UNKNOWN: uncertainty,
        }

    return {
        SAFE: 0.0,
        INTRUSION: commitment,
        UNKNOWN: uncertainty,
    }


def combine_dempster(
    left: dict[str, float],
    right: dict[str, float],
) -> tuple[dict[str, float], float]:
    """
    Combine two belief assignments using Dempster's rule.

    IMPORTANT:
        UNKNOWN combined with SAFE becomes SAFE.
        UNKNOWN combined with INTRUSION becomes INTRUSION.

    Direct SAFE vs INTRUSION combinations produce conflict.

    Returns:
        normalized combined mass
        generated conflict
    """

    raw = {
        SAFE: 0.0,
        INTRUSION: 0.0,
        UNKNOWN: 0.0,
    }

    conflict = 0.0

    for left_state, left_mass in left.items():

        for right_state, right_mass in right.items():

            product = (
                left_mass * right_mass
            )

            if product <= 0.0:
                continue

            # Direct contradiction.
            if (
                left_state == SAFE
                and right_state == INTRUSION
            ) or (
                left_state == INTRUSION
                and right_state == SAFE
            ):

                conflict += product
                continue

            # Unknown carries through the other evidence.
            if left_state == UNKNOWN:

                raw[right_state] += product
                continue

            if right_state == UNKNOWN:

                raw[left_state] += product
                continue

            # Same hypothesis reinforces itself.
            if left_state == right_state:

                raw[left_state] += product
                continue

    remaining_mass = sum(
        raw.values()
    )

    # Total contradiction.
    if remaining_mass <= 0.0:

        return (
            {
                SAFE: 0.0,
                INTRUSION: 0.0,
                UNKNOWN: 1.0,
            },
            1.0,
        )

    # Normalize the non-conflicting evidence.
    combined = {
        SAFE: raw[SAFE] / remaining_mass,
        INTRUSION:
            raw[INTRUSION] / remaining_mass,
        UNKNOWN:
            raw[UNKNOWN] / remaining_mass,
    }

    return combined, clamp(conflict)


def fuse_evidence(
    votes: dict[str, str],
    trust_scores: dict[str, float],
    decision_threshold: float = 0.60,
    uncertainty_threshold: float = 0.35,
    conflict_threshold: float = 0.80,
) -> EvidenceResult:
    """
    Fuse trusted device observations.

    The algorithm explicitly tracks:

        belief
        uncertainty
        conflict

    High conflict does not automatically erase strong evidence.

    Very high conflict still causes an abstention.
    """

    if not votes:

        return EvidenceResult(
            belief_safe=0.0,
            belief_intrusion=0.0,
            uncertainty=1.0,
            conflict=0.0,
            decision="UNCERTAIN",
            confidence=0.0,
        )

    # --------------------------------------------------------
    # Convert all observations into belief assignments.
    # --------------------------------------------------------

    masses = []

    for device_id, vote in votes.items():

        trust = trust_scores.get(
            device_id,
            0.0,
        )

        masses.append(
            observation_to_mass(
                vote,
                trust,
            )
        )

    # --------------------------------------------------------
    # Combine evidence sequentially.
    # --------------------------------------------------------

    combined = masses[0]

    conflict_values = []

    for next_mass in masses[1:]:

        combined, pair_conflict = (
            combine_dempster(
                combined,
                next_mass,
            )
        )

        conflict_values.append(
            pair_conflict
        )

    # --------------------------------------------------------
    # Summarize total conflict.
    #
    # We preserve the maximum pairwise conflict rather than
    # repeatedly adding conflict until it reaches 1.
    # --------------------------------------------------------

    total_conflict = (
        max(conflict_values)
        if conflict_values
        else 0.0
    )

    belief_safe = clamp(
        combined[SAFE]
    )

    belief_intrusion = clamp(
        combined[INTRUSION]
    )

    uncertainty = clamp(
        combined[UNKNOWN]
    )

    # --------------------------------------------------------
    # Decision logic
    # --------------------------------------------------------

    if (
        total_conflict >= conflict_threshold
        and uncertainty >= uncertainty_threshold
    ):

        decision = "UNCERTAIN"

        confidence = max(
            belief_safe,
            belief_intrusion,
        )

    elif (
        belief_intrusion >= decision_threshold
        and belief_intrusion > belief_safe
    ):

        decision = INTRUSION
        confidence = belief_intrusion

    elif (
        belief_safe >= decision_threshold
        and belief_safe > belief_intrusion
    ):

        decision = SAFE
        confidence = belief_safe

    else:

        decision = "UNCERTAIN"

        confidence = max(
            belief_safe,
            belief_intrusion,
        )

    return EvidenceResult(
        belief_safe=belief_safe,
        belief_intrusion=belief_intrusion,
        uncertainty=uncertainty,
        conflict=total_conflict,
        decision=decision,
        confidence=confidence,
    )