import hashlib
import json
import os
from pathlib import Path


class EventStoreError(Exception):
    """Raised when the event log is invalid or cannot be read safely."""


def _canonical_json(value):
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")


def _make_record(sequence, payload):
    body = {"sequence": sequence, "payload": payload}
    checksum = hashlib.sha256(_canonical_json(body)).hexdigest()
    return _canonical_json({**body, "checksum": checksum}) + b"\n"


class EventStore:
    """Append-only JSON-lines event store with checksummed records."""

    def __init__(self, path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.touch(exist_ok=True)

    def _read_records(self):
        data = self.path.read_bytes()
        lines = data.splitlines(keepends=True)
        events = []
        valid_bytes = 0

        for index, raw in enumerate(lines):
            complete = raw.endswith(b"\n")

            if not complete and index == len(lines) - 1:
                # Ignore a torn final record during recovery.
                break

            try:
                record = json.loads(raw.decode("utf-8"))
                sequence = record["sequence"]
                payload = record["payload"]
                checksum = record["checksum"]
            except (UnicodeDecodeError, json.JSONDecodeError, KeyError, TypeError) as exc:
                raise EventStoreError(
                    f"Invalid record at line {index + 1}"
                ) from exc

            if not isinstance(sequence, int) or isinstance(sequence, bool):
                raise EventStoreError(f"Invalid sequence at line {index + 1}")

            if sequence != len(events) + 1:
                raise EventStoreError(f"Unexpected sequence at line {index + 1}")

            expected = hashlib.sha256(
                _canonical_json({"sequence": sequence, "payload": payload})
            ).hexdigest()

            if not isinstance(checksum, str) or checksum != expected:
                raise EventStoreError(f"Checksum mismatch at line {index + 1}")

            events.append({"sequence": sequence, "payload": payload})
            valid_bytes += len(raw)

        return events, valid_bytes

    def replay(self):
        events, _ = self._read_records()
        return events

    def append(self, payload):
        if not isinstance(payload, dict):
            raise ValueError("Payload must be a JSON object")

        events, valid_bytes = self._read_records()

        # Remove any incomplete tail before writing the next complete record.
        with self.path.open("r+b") as log:
            log.truncate(valid_bytes)
            log.seek(valid_bytes)
            record = _make_record(len(events) + 1, payload)
            log.write(record)
            log.flush()
            os.fsync(log.fileno())

        return {"sequence": len(events) + 1, "payload": payload}
