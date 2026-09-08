from event_logging.event_log import log_event

from gateway.fsm import (
    SAFE,
    ALERT,
    DEGRADED,
    LOCKDOWN,
)


def decide_actions(
    state,
    intrusion_detected=False,
):
    actions = []

    if state == SAFE:

        actions.append(
            "NORMAL_OPERATION"
        )

    elif state == ALERT:

        actions += [
            "LOCK_DOOR",
            "ACTIVATE_ALARM",
        ]

        if intrusion_detected:
            actions.append(
                "LOG_INTRUSION"
            )

    elif state == DEGRADED:

        actions += [
            "MAINTAIN_SAFE_LOCK_STATE",
            "LOG_DEGRADED_MODE",
        ]

    elif state == LOCKDOWN:

        actions += [
            "LOCK_DOOR",
            "ACTIVATE_ALARM",
            "BLOCK_REMOTE_UNLOCK",
            "LOG_LOCKDOWN",
        ]

    # --------------------------------------------------------
    # Security audit event
    # --------------------------------------------------------

    try:

        log_event(
            "DEFENSE_DECISION",
            {
                "state": state,
                "intrusion_detected": intrusion_detected,
                "actions": actions,
            },
        )

    except Exception as exc:

        print(
            f"[LOGGING] ⚠️ Failed to record "
            f"defense decision: {exc}"
        )

    return actions