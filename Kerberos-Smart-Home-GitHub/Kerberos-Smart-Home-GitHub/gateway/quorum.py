QUORUM_THRESHOLD = 0.60


def weighted_quorum(votes, trust_scores):
    """
    Decide between competing states using device trust.

    votes:
        {
            "door1": "INTRUSION",
            "pir1": "INTRUSION",
            "ultrasonic1": "INTRUSION",
            "camera1": "SAFE"
        }

    trust_scores:
        {
            "door1": 95,
            "pir1": 97,
            "ultrasonic1": 94,
            "camera1": 35
        }
    """

    total_trust = 0
    weighted_votes = {}

    # Calculate total available trust
    for device, state in votes.items():
        trust = trust_scores.get(device, 0)

        total_trust += trust

        weighted_votes[state] = (
            weighted_votes.get(state, 0) + trust
        )

    if total_trust == 0:
        return {
            "decision": "UNKNOWN",
            "confidence": 0.0,
            "weighted_votes": {}
        }

    # Find the state with the strongest trusted evidence
    winning_state = max(
        weighted_votes,
        key=weighted_votes.get
    )

    winning_weight = weighted_votes[winning_state]

    confidence = winning_weight / total_trust

    if confidence >= QUORUM_THRESHOLD:
        decision = winning_state
    else:
        decision = "UNCERTAIN"

    return {
        "decision": decision,
        "confidence": confidence,
        "weighted_votes": weighted_votes
    }