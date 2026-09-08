def check_consistency(states):
    """
    Check whether the devices are giving physically
    consistent evidence.
    """

    door_state = states.get("door1")
    pir_state = states.get("pir1")
    ultrasonic_state = states.get("ultrasonic1")
    camera_state = states.get("camera1")

    conflicts = []

    if (
        door_state == "OPEN"
        and pir_state == "NO_MOTION"
        and ultrasonic_state == "NO_PERSON"
    ):
        conflicts.append(
            "Door is OPEN but no motion/presence detected"
        )

    if (
        ultrasonic_state == "PERSON"
        and camera_state == "NO_MOTION"
    ):
        conflicts.append(
            "Ultrasonic detects PERSON but camera reports NO_MOTION"
        )

    if (
        pir_state == "MOTION"
        and camera_state == "NO_MOTION"
    ):
        conflicts.append(
            "PIR detects MOTION but camera reports NO_MOTION"
        )

    return conflicts