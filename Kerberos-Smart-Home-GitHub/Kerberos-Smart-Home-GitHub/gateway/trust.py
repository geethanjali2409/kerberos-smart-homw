MIN_TRUST = 0
MAX_TRUST = 100

TRUST_START = 100

# Trust penalties
PENALTY_INVALID_AUTH = 20
PENALTY_REPLAY = 30
PENALTY_STALE = 10
PENALTY_DISAGREEMENT = 10

# Trust rewards
REWARD_AGREEMENT = 2

# Device is considered unreliable below this value
QUARANTINE_THRESHOLD = 40


device_trust = {}


def get_trust(device_id):
    """
    Get the current trust score for a device.
    New devices start with full trust.
    """

    if device_id not in device_trust:
        device_trust[device_id] = TRUST_START

    return device_trust[device_id]


def update_trust(device_id, change):
    """
    Change a device's trust score while keeping it
    between 0 and 100.
    """

    current = get_trust(device_id)

    new_score = current + change

    new_score = max(MIN_TRUST, new_score)
    new_score = min(MAX_TRUST, new_score)

    device_trust[device_id] = new_score

    return new_score


def reward_agreement(device_id):
    """
    Reward a device when its observation agrees
    with the trusted evidence.
    """

    return update_trust(
        device_id,
        REWARD_AGREEMENT
    )


def penalize_disagreement(device_id):
    """
    Penalize a device when it disagrees with
    trusted evidence.
    """

    return update_trust(
        device_id,
        -PENALTY_DISAGREEMENT
    )


def penalize_replay(device_id):
    """
    Strong penalty for a replay attempt.
    """

    return update_trust(
        device_id,
        -PENALTY_REPLAY
    )


def penalize_stale(device_id):
    """
    Penalize stale messages.
    """

    return update_trust(
        device_id,
        -PENALTY_STALE
    )


def is_quarantined(device_id):
    """
    Determine whether a device's trust score
    has fallen below the quarantine threshold.
    """

    return get_trust(device_id) < QUARANTINE_THRESHOLD