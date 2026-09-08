from __future__ import annotations

import hashlib
import json
import os
import threading
import time
import uuid
from typing import Any


LOG_FILE = os.path.join(
    os.path.dirname(__file__),
    "security_events.jsonl",
)

GENESIS_HASH = "0" * 64

_lock = threading.Lock()


def _canonical_json(data: dict[str, Any]) -> str:
    return json.dumps(
        data,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )


def _calculate_hash(
    event: dict[str, Any],
    previous_hash: str,
) -> str:
    payload = {
        "event": event,
        "previous_hash": previous_hash,
    }

    serialized = _canonical_json(payload).encode("utf-8")

    return hashlib.sha256(serialized).hexdigest()


def _get_last_hash() -> str:
    if not os.path.exists(LOG_FILE):
        return GENESIS_HASH

    last_hash = GENESIS_HASH

    with open(
        LOG_FILE,
        "r",
        encoding="utf-8",
    ) as file:

        for line in file:
            line = line.strip()

            if not line:
                continue

            record = json.loads(line)

            last_hash = record["hash"]

    return last_hash


def log_event(
    event_type: str,
    data: dict[str, Any] | None = None,
) -> dict[str, Any]:

    if not event_type:
        raise ValueError(
            "event_type cannot be empty"
        )

    event = {
        "event_id": str(uuid.uuid4()),
        "timestamp": time.time(),
        "event_type": event_type,
        "data": data or {},
    }

    with _lock:

        previous_hash = _get_last_hash()

        event_hash = _calculate_hash(
            event,
            previous_hash,
        )

        record = {
            "event": event,
            "previous_hash": previous_hash,
            "hash": event_hash,
        }

        os.makedirs(
            os.path.dirname(LOG_FILE),
            exist_ok=True,
        )

        with open(
            LOG_FILE,
            "a",
            encoding="utf-8",
        ) as file:

            file.write(
                _canonical_json(record)
                + "\n"
            )

    return record


def verify_log() -> tuple[bool, str]:

    if not os.path.exists(LOG_FILE):
        return True, "EMPTY_LOG"

    previous_hash = GENESIS_HASH
    line_number = 0

    with open(
        LOG_FILE,
        "r",
        encoding="utf-8",
    ) as file:

        for line in file:

            line_number += 1

            line = line.strip()

            if not line:
                continue

            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                return (
                    False,
                    f"INVALID_JSON_LINE_{line_number}",
                )

            if record.get(
                "previous_hash"
            ) != previous_hash:

                return (
                    False,
                    f"CHAIN_BROKEN_LINE_{line_number}",
                )

            expected_hash = _calculate_hash(
                record["event"],
                record["previous_hash"],
            )

            if record.get("hash") != expected_hash:

                return (
                    False,
                    f"HASH_MISMATCH_LINE_{line_number}",
                )

            previous_hash = record["hash"]

    return True, "LOG_VALID"