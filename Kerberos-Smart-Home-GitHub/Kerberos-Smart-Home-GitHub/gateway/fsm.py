SAFE = "SAFE"
OCCUPIED = "OCCUPIED"
ALERT = "ALERT"
DEGRADED = "DEGRADED"
LOCKDOWN = "LOCKDOWN"


def determine_state(
    intrusion_detected,
    quorum_confidence,
    trusted_device_count,
    anomalous_devices,
    quarantined_devices,
):
    """
    Determine the security state of the house.

    Anomaly detection is an input signal.
    It is NOT itself a security state.
    """

    # No reliable devices left
    if trusted_device_count == 0:
        return LOCKDOWN

    # Severe compromise:
    # multiple devices quarantined or very little
    # trusted evidence remains.
    if len(quarantined_devices) >= 2:
        return LOCKDOWN

    if trusted_device_count == 1 and intrusion_detected:
        return LOCKDOWN

    # Strong trusted evidence of intrusion
    if intrusion_detected and quorum_confidence >= 0.60:
        return ALERT

    # System has suspicious/unreliable devices but
    # does not have enough evidence for a confident alert
    if anomalous_devices or quarantined_devices:
        return DEGRADED

    # Intrusion evidence exists but quorum is uncertain
    if intrusion_detected:
        return DEGRADED

    return SAFE