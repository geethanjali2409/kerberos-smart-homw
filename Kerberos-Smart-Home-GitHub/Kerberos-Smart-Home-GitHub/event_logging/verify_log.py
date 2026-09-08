from event_logging.event_log import verify_log


def main() -> None:

    valid, message = verify_log()

    if valid:
        print(
            f"[LOG] ✅ {message}"
        )
    else:
        print(
            f"[LOG] ❌ {message}"
        )


if __name__ == "__main__":
    main()