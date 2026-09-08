ALPHA = 0.3

ANOMALY_THRESHOLD = 0.5


device_rates = {}


def ewma(previous, current):
    """
    Exponentially Weighted Moving Average.
    """

    if previous is None:
        return current

    return (
        ALPHA * current
        + (1 - ALPHA) * previous
    )


def record_behavior(device_id, is_bad):

    current = device_rates.get(device_id, 0.0)

    value = 1.0 if is_bad else 0.0

    updated = ewma(current, value)

    device_rates[device_id] = updated

    return updated


def is_anomalous(device_id):

    rate = device_rates.get(device_id, 0.0)

    return rate >= ANOMALY_THRESHOLD