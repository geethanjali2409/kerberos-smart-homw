import time


MAX_MESSAGE_AGE = 10  # seconds

used_nonces = set()


def check_freshness(timestamp, nonce):
    """
    Check whether a message is recent and its nonce
    has not already been used.
    """

    current_time = time.time()

    # Check timestamp
    age = abs(current_time - timestamp)

    if age > MAX_MESSAGE_AGE:
        return False, "MESSAGE_TOO_OLD"

    # Check replayed nonce
    if nonce in used_nonces:
        return False, "REPLAY_DETECTED"

    # Remember nonce
    used_nonces.add(nonce)

    return True, "FRESH"