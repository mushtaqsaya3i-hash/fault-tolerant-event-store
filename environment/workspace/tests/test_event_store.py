import json

import pytest

from event_store import EventStore, EventStoreError


def test_append_and_replay(tmp_path):
    store = EventStore(tmp_path / "events.log")
    store.append({"type": "created", "id": 1})
    store.append({"type": "updated", "id": 1})

    assert store.replay() == [
        {"sequence": 1, "payload": {"type": "created", "id": 1}},
        {"sequence": 2, "payload": {"type": "updated", "id": 1}},
    ]


def test_recovery_after_restart(tmp_path):
    path = tmp_path / "events.log"
    EventStore(path).append({"value": "first"})

    restarted = EventStore(path)
    restarted.append({"value": "second"})

    assert [e["sequence"] for e in restarted.replay()] == [1, 2]


def test_truncated_final_record_is_ignored_and_removed_on_append(tmp_path):
    path = tmp_path / "events.log"
    store = EventStore(path)
    store.append({"value": "committed"})

    with path.open("ab") as log:
        log.write(b'{"sequence":2,"payload":')

    assert store.replay() == [
        {"sequence": 1, "payload": {"value": "committed"}}
    ]

    store.append({"value": "next"})
    assert store.replay() == [
        {"sequence": 1, "payload": {"value": "committed"}},
        {"sequence": 2, "payload": {"value": "next"}},
    ]


def test_complete_corrupt_record_is_rejected(tmp_path):
    path = tmp_path / "events.log"
    store = EventStore(path)
    store.append({"value": "original"})

    lines = path.read_bytes().splitlines()
    record = json.loads(lines[0])
    record["payload"]["value"] = "tampered"
    path.write_bytes(
        json.dumps(record, sort_keys=True, separators=(",", ":")).encode() + b"\n"
    )

    with pytest.raises(EventStoreError, match="Checksum mismatch"):
        store.replay()


def test_corruption_in_middle_is_rejected(tmp_path):
    path = tmp_path / "events.log"
    store = EventStore(path)
    store.append({"value": 1})
    store.append({"value": 2})
    store.append({"value": 3})

    lines = path.read_bytes().splitlines()
    record = json.loads(lines[1])
    record["payload"]["value"] = 999
    lines[1] = json.dumps(
        record, sort_keys=True, separators=(",", ":")
    ).encode()
    path.write_bytes(b"\n".join(lines) + b"\n")

    with pytest.raises(EventStoreError):
        store.replay()


def test_replay_is_deterministic(tmp_path):
    store = EventStore(tmp_path / "events.log")
    store.append({"b": 2, "a": 1})
    store.append({"message": "hello"})

    assert store.replay() == store.replay()


def test_payload_must_be_an_object(tmp_path):
    store = EventStore(tmp_path / "events.log")

    with pytest.raises(ValueError, match="Payload must be a JSON object"):
        store.append(["not", "an", "object"])
