from __future__ import annotations

from dataclasses import dataclass


@dataclass
class SafetyDecision:
    decision: str
    risk: float
    reason: str


# -------------------------------------------------------------
# Conservative intrusion policy
# -------------------------------------------------------------

INTRUSION_THRESHOLD = 0.70
SAFE_THRESHOLD = 0.70

# Minimum difference between competing hypotheses.
MIN_BELIEF_MARGIN = 0.15

# Very strong conflict where neither side clearly dominates.
HIGH_CONFLICT_THRESHOLD = 0.80

# If intrusion evidence is this strong, allow it to dominate
# even when contradictory evidence exists.
STRONG_INTRUSION_THRESHOLD = 0.85

# If safe evidence is overwhelmingly stronger, tolerate
# moderate conflict from noisy sensors.
STRONG_SAFE_THRESHOLD = 0.85

# Conflict above this is considered severe for allowing SAFE.
SAFE_CONFLICT_LIMIT = 0.90


def safety_decision(
    belief_safe: float,
    belief_intrusion: float,
    uncertainty: float,
    conflict: float,
) -> SafetyDecision:
    """
    Convert K-REAF evidence into a conservative house-state
    decision.

    Important design principle:

        Conflict alone must NOT force UNCERTAIN.

    The policy considers:

        - dominant evidence
        - belief margin
        - uncertainty
        - conflict
        - security asymmetry

    Intrusion is intentionally easier to accept than SAFE when
    the evidence strongly supports an intrusion.
    """

    margin = abs(
        belief_safe - belief_intrusion
    )

    # =========================================================
    # 1. Strong uncertainty
    # =========================================================

    if uncertainty >= 0.35:
        return SafetyDecision(
            decision="UNCERTAIN",
            risk=0.50 + (0.25 * uncertainty),
            reason=(
                "Evidence uncertainty is too high for an "
                "automatic house-state decision."
            ),
        )

    # =========================================================
    # 2. Strong intrusion evidence
    # =========================================================
    #
    # Security is asymmetric:
    #
    # It is acceptable to trigger an alert when intrusion
    # evidence is strong, even when a sensor disagrees.
    #

    if (
        belief_intrusion >= STRONG_INTRUSION_THRESHOLD
        and margin >= MIN_BELIEF_MARGIN
    ):
        risk = min(
            1.0,
            belief_intrusion
            + (0.20 * conflict),
        )

        return SafetyDecision(
            decision="INTRUSION",
            risk=risk,
            reason=(
                "Strong intrusion evidence dominates "
                "contradictory sensor evidence."
            ),
        )

    # =========================================================
    # 3. Normal intrusion decision
    # =========================================================

    if (
        belief_intrusion >= INTRUSION_THRESHOLD
        and margin >= MIN_BELIEF_MARGIN
    ):
        risk = min(
            1.0,
            belief_intrusion
            + (0.15 * conflict),
        )

        return SafetyDecision(
            decision="INTRUSION",
            risk=risk,
            reason=(
                "Intrusion evidence exceeds the safety "
                "decision threshold."
            ),
        )

    # =========================================================
    # 4. Strong SAFE evidence
    # =========================================================
    #
    # A strong safe majority can tolerate moderate conflict.
    #

    if (
        belief_safe >= STRONG_SAFE_THRESHOLD
        and margin >= MIN_BELIEF_MARGIN
        and conflict < SAFE_CONFLICT_LIMIT
    ):
        risk = max(
            0.0,
            1.0 - belief_safe,
        )

        return SafetyDecision(
            decision="SAFE",
            risk=risk,
            reason=(
                "Strong safe evidence dominates with "
                "acceptable conflicting evidence."
            ),
        )

    # =========================================================
    # 5. Normal SAFE decision
    # =========================================================

    if (
        belief_safe >= SAFE_THRESHOLD
        and margin >= MIN_BELIEF_MARGIN
        and conflict < HIGH_CONFLICT_THRESHOLD
    ):
        risk = max(
            0.0,
            1.0 - belief_safe,
        )

        return SafetyDecision(
            decision="SAFE",
            risk=risk,
            reason=(
                "Safe evidence dominates with sufficient "
                "confidence."
            ),
        )

    # =========================================================
    # 6. Extreme conflict
    # =========================================================

    if (
        conflict >= HIGH_CONFLICT_THRESHOLD
        and margin < MIN_BELIEF_MARGIN
    ):
        return SafetyDecision(
            decision="UNCERTAIN",
            risk=0.75,
            reason=(
                "Devices strongly disagree and neither "
                "hypothesis clearly dominates."
            ),
        )

    # =========================================================
    # 7. Fallback
    # =========================================================

    return SafetyDecision(
        decision="UNCERTAIN",
        risk=0.50 + (0.25 * conflict),
        reason=(
            "Evidence does not meet the automatic "
            "decision requirements."
        ),
    )