import time
from dataclasses import dataclass, field
from typing import Dict, List


# =========================================================
# POLICY
# =========================================================

QUARANTINE_THRESHOLD = 40

RECOVERY_TRUST_THRESHOLD = 70

RECOVERY_OBSERVATIONS_REQUIRED = 10

PROBATION_OBSERVATIONS_REQUIRED = 5


# =========================================================
# DEVICE QUARANTINE RECORD
# =========================================================

@dataclass
class QuarantineRecord:
    device_id: str

    quarantined_at: float

    reason: str

    trust_at_quarantine: int

    failed_events: List[str] = field(default_factory=list)

    recovery_observations: int = 0

    probation_observations: int = 0

    recovery_started: bool = False

    probation_started: bool = False

    admitted: bool = False

    last_recovery_state: str | None = None

    last_clean_timestamp: float | None = None


# =========================================================
# RUNTIME STORE
# =========================================================

quarantine_records: Dict[str, QuarantineRecord] = {}


# =========================================================
# QUARANTINE DECISION
# =========================================================

def should_quarantine(trust_score: int) -> bool:
    """
    A device becomes eligible for quarantine when its
    trust score falls below the quarantine threshold.
    """

    return trust_score < QUARANTINE_THRESHOLD


# =========================================================
# CREATE QUARANTINE
# =========================================================

def quarantine_device(
    device_id: str,
    trust_score: int,
    reason: str,
) -> QuarantineRecord:
    """
    Place a device into quarantine.

    The device remains observable but is excluded from
    trusted quorum decisions.
    """

    existing = quarantine_records.get(device_id)

    if existing is not None:

        if reason not in existing.failed_events:
            existing.failed_events.append(reason)

        return existing


    record = QuarantineRecord(
        device_id=device_id,
        quarantined_at=time.time(),
        reason=reason,
        trust_at_quarantine=trust_score,
        failed_events=[reason],
    )

    quarantine_records[device_id] = record

    return record


# =========================================================
# STATUS
# =========================================================

def is_quarantined(device_id: str) -> bool:
    """
    Return True when the device is currently excluded
    from trusted operation.
    """

    record = quarantine_records.get(device_id)

    if record is None:
        return False

    return not record.admitted


# =========================================================
# SECURITY FAILURE RECORDING
# =========================================================

def record_failure(
    device_id: str,
    reason: str,
) -> None:
    """
    Record a security failure for a quarantined device.

    Any new failure cancels current recovery progress.
    """

    record = quarantine_records.get(device_id)

    if record is None:
        return


    if reason not in record.failed_events:
        record.failed_events.append(reason)


    # A recovery failure means the device must prove
    # itself again from a clean baseline.
    record.recovery_observations = 0

    record.probation_observations = 0

    record.recovery_started = False

    record.probation_started = False

    record.last_recovery_state = None

    record.last_clean_timestamp = None


# =========================================================
# RECORD CLEAN RECOVERY OBSERVATION
# =========================================================

def record_clean_observation(
    device_id: str,
    observed_state: str,
    timestamp: float,
) -> bool:
    """
    Record a recovery observation only after the gateway
    has independently established that the observation
    agrees with trusted evidence.
    """

    record = quarantine_records.get(device_id)

    if record is None:
        return False

    if record.admitted:
        return False


    record.recovery_observations += 1

    record.last_recovery_state = observed_state

    record.last_clean_timestamp = timestamp

    return True


# =========================================================
# START RECOVERY
# =========================================================

def start_recovery(
    device_id: str,
    trust_score: int,
) -> bool:
    """
    Transition a quarantined device into recovery/probation
    only after sufficient clean observations and trust.
    """

    record = quarantine_records.get(device_id)

    if record is None:
        return False

    if record.admitted:
        return False

    if record.recovery_started:
        return True


    if record.recovery_observations < RECOVERY_OBSERVATIONS_REQUIRED:
        return False

    if trust_score < RECOVERY_TRUST_THRESHOLD:
        return False


    record.recovery_started = True

    record.probation_started = True

    record.probation_observations = 0

    return True


# =========================================================
# RECORD PROBATION OBSERVATION
# =========================================================

def record_probation_observation(
    device_id: str,
) -> bool:
    """
    Count a clean observation during the probation phase.
    """

    record = quarantine_records.get(device_id)

    if record is None:
        return False

    if record.admitted:
        return False

    if not record.probation_started:
        return False


    record.probation_observations += 1

    return True


# =========================================================
# ATTEMPT REINSTATEMENT
# =========================================================

def attempt_reinstatement(
    device_id: str,
    trust_score: int,
) -> bool:
    """
    Re-admit a device only when both recovery and probation
    requirements are satisfied.
    """

    record = quarantine_records.get(device_id)

    if record is None:
        return False

    if record.admitted:
        return True


    if not record.recovery_started:
        return False

    if not record.probation_started:
        return False


    if record.probation_observations < PROBATION_OBSERVATIONS_REQUIRED:
        return False

    if trust_score < RECOVERY_TRUST_THRESHOLD:
        return False


    record.admitted = True

    return True


# =========================================================
# QUARANTINE INFORMATION
# =========================================================

def get_quarantine_record(
    device_id: str,
) -> dict | None:
    """
    Return a safe serializable representation of a device's
    quarantine state.
    """

    record = quarantine_records.get(device_id)

    if record is None:
        return None


    return {
        "device_id": record.device_id,
        "quarantined_at": record.quarantined_at,
        "reason": record.reason,
        "trust_at_quarantine": record.trust_at_quarantine,
        "failed_events": list(record.failed_events),
        "recovery_observations": record.recovery_observations,
        "probation_observations": record.probation_observations,
        "recovery_started": record.recovery_started,
        "probation_started": record.probation_started,
        "admitted": record.admitted,
        "last_recovery_state": record.last_recovery_state,
        "last_clean_timestamp": record.last_clean_timestamp,
    }


def get_quarantined_devices() -> list[str]:
    """
    Return devices that are currently excluded from
    trusted security decisions.
    """

    return [
        device_id
        for device_id, record in quarantine_records.items()
        if not record.admitted
    ]