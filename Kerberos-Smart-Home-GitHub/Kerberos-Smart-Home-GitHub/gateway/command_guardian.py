from __future__ import annotations

from dataclasses import dataclass


ALLOW = "ALLOW"
HOLD_FOR_CONFIRMATION = "HOLD_FOR_CONFIRMATION"
REFUSE = "REFUSE"


@dataclass
class CommandDecision:
    decision: str
    risk: float
    reason: str


# -------------------------------------------------------------
# Risk thresholds
# -------------------------------------------------------------

# Commands that change physical security are treated as high risk.
HIGH_RISK_ACTIONS = {
    "UNLOCK_DOOR",
}

# A known intrusion should never be overridden by an unlock command.
INTRUSION_CONFIDENCE_THRESHOLD = 0.70

# Strong evidence conflict means we should not blindly execute a
# security-sensitive command.
HIGH_CONFLICT_THRESHOLD = 0.80

# Uncertainty above this value requires confirmation.
UNCERTAINTY_THRESHOLD = 0.35

# Behavioral anomaly threshold.
ANOMALY_THRESHOLD = 0.50


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def evaluate_command(
    *,
    action: str,
    owner_authenticated: bool,
    command_fresh: bool,
    house_state: str,
    quorum_confidence: float,
    k_reaf_conflict: float,
    k_reaf_uncertainty: float,
    behavior_anomaly: float,
    k_reaf_belief_intrusion: float = 0.0,
) -> CommandDecision:
    """
    Evaluate whether an authenticated owner command should be:

        ALLOW
        HOLD_FOR_CONFIRMATION
        REFUSE

    This function performs authorization/safety reasoning.

    It does NOT authenticate the owner itself and does NOT send
    commands to actuators.
    """

    quorum_confidence = _clamp(quorum_confidence)
    k_reaf_conflict = _clamp(k_reaf_conflict)
    k_reaf_uncertainty = _clamp(k_reaf_uncertainty)
    behavior_anomaly = _clamp(behavior_anomaly)
    k_reaf_belief_intrusion = _clamp(
        k_reaf_belief_intrusion
    )

    action = str(action).upper()

    # =========================================================
    # 1. Authentication failure
    # =========================================================

    if not owner_authenticated:
        return CommandDecision(
            decision=REFUSE,
            risk=1.0,
            reason="Owner authentication failed.",
        )

    # =========================================================
    # 2. Freshness / replay failure
    # =========================================================

    if not command_fresh:
        return CommandDecision(
            decision=REFUSE,
            risk=1.0,
            reason="Owner command is stale or replayed.",
        )

    # =========================================================
    # 3. Unknown action
    # =========================================================

    known_actions = {
        "LOCK_DOOR",
        "UNLOCK_DOOR",
        "ACTIVATE_ALARM",
        "DEACTIVATE_ALARM",
    }

    if action not in known_actions:
        return CommandDecision(
            decision=REFUSE,
            risk=1.0,
            reason="Unknown or unsupported command.",
        )

    # =========================================================
    # 4. High-risk command during confirmed intrusion
    # =========================================================

    if action in HIGH_RISK_ACTIONS:

        intrusion_confirmed = (
            house_state == "ALERT"
            and quorum_confidence
            >= INTRUSION_CONFIDENCE_THRESHOLD
        )

        strong_intrusion_evidence = (
            k_reaf_belief_intrusion
            >= INTRUSION_CONFIDENCE_THRESHOLD
        )

        if (
            intrusion_confirmed
            or strong_intrusion_evidence
        ):
            return CommandDecision(
                decision=REFUSE,
                risk=1.0,
                reason=(
                    "Unlock request conflicts with trusted "
                    "intrusion evidence."
                ),
            )

    # =========================================================
    # 5. High uncertainty
    # =========================================================

    if k_reaf_uncertainty >= UNCERTAINTY_THRESHOLD:

        return CommandDecision(
            decision=HOLD_FOR_CONFIRMATION,
            risk=0.70 + (
                0.20 * k_reaf_uncertainty
            ),
            reason=(
                "Physical evidence is too uncertain for "
                "automatic execution."
            ),
        )

    # =========================================================
    # 6. Severe evidence conflict
    # =========================================================

    if (
        k_reaf_conflict >= HIGH_CONFLICT_THRESHOLD
        and action in HIGH_RISK_ACTIONS
    ):
        return CommandDecision(
            decision=HOLD_FOR_CONFIRMATION,
            risk=0.75 + (
                0.20 * k_reaf_conflict
            ),
            reason=(
                "Owner command conflicts with strongly "
                "disagreeing device evidence."
            ),
        )

    # =========================================================
    # 7. Behavioral anomaly
    # =========================================================

    if behavior_anomaly >= ANOMALY_THRESHOLD:

        if action in HIGH_RISK_ACTIONS:
            return CommandDecision(
                decision=HOLD_FOR_CONFIRMATION,
                risk=0.65 + (
                    0.25 * behavior_anomaly
                ),
                reason=(
                    "Authenticated command is behaviorally "
                    "unusual for the owner."
                ),
            )

    # =========================================================
    # 8. Degraded house state
    # =========================================================

    if house_state in {
        "DEGRADED",
        "LOCKDOWN",
    }:

        if action in HIGH_RISK_ACTIONS:

            return CommandDecision(
                decision=HOLD_FOR_CONFIRMATION,
                risk=0.80,
                reason=(
                    "High-risk command requested while the "
                    "house is operating in a degraded security state."
                ),
            )

    # =========================================================
    # 9. Safe high-confidence execution
    # =========================================================

    if (
        action in HIGH_RISK_ACTIONS
        and house_state == "SAFE"
        and quorum_confidence >= 0.60
        and k_reaf_conflict < HIGH_CONFLICT_THRESHOLD
        and behavior_anomaly < ANOMALY_THRESHOLD
    ):
        risk = max(
            0.0,
            1.0 - quorum_confidence,
        )

        return CommandDecision(
            decision=ALLOW,
            risk=risk,
            reason=(
                "Owner authenticated and trusted physical "
                "evidence does not indicate an unsafe condition."
            ),
        )

    # =========================================================
    # 10. Normal low-risk commands
    # =========================================================

    if action not in HIGH_RISK_ACTIONS:

        if house_state == "LOCKDOWN":

            return CommandDecision(
                decision=HOLD_FOR_CONFIRMATION,
                risk=0.75,
                reason=(
                    "Command requires confirmation while "
                    "the house is in lockdown."
                ),
            )

        return CommandDecision(
            decision=ALLOW,
            risk=0.10,
            reason=(
                "Authenticated low-risk command allowed."
            ),
        )

    # =========================================================
    # 11. Conservative fallback
    # =========================================================

    return CommandDecision(
        decision=HOLD_FOR_CONFIRMATION,
        risk=0.60,
        reason=(
            "Command did not satisfy automatic execution "
            "requirements."
        ),
    )