import json
import subprocess
import sys
from pathlib import Path

APP = Path("/app")
CLI = APP / "cli.py"
PYTHON = sys.executable


def run_cli(log, *args):
    return subprocess.run(
        [PYTHON, str(CLI), "--log", str(log), *args],
        cwd=APP,
        capture_output=True,
        text=True,
        timeout=10,
    )


def test_append_and_replay(tmp_path):
    log = tmp_path / "events.log"

    first = run_cli(log, "append", '{"type":"created","id":1}')
    second = run_cli(log, "append", '{"type":"updated","id":1}')
    replay = run_cli(log, "replay")

    assert first.returncode == 0, first.stderr
    assert second.returncode == 0, second.stderr
    assert replay.returncode == 0, replay.stderr

    events = json.loads(replay.stdout)
    assert [event["sequence"] for event in events] == [1, 2]
    assert events[0]["payload"] == {"type": "created", "id": 1}
    assert events[1]["payload"] == {"type": "updated", "id": 1}


def test_recovery_after_restart(tmp_path):
    log = tmp_path / "events.log"

    assert run_cli(log, "append", '{"value":"first"}').returncode == 0
    assert run_cli(log, "append", '{"value":"second"}').returncode == 0

    replay = run_cli(log, "replay")
    assert replay.returncode == 0, replay.stderr
    assert [e["sequence"] for e in json.loads(replay.stdout)] == [1, 2]


def test_truncated_final_record_recovery(tmp_path):
    log = tmp_path / "events.log"
    assert run_cli(log, "append", '{"value":"committed"}').returncode == 0

    with log.open("ab") as file:
        file.write(b'{"sequence":2,"payload":')

    replay = run_cli(log, "replay")
    assert replay.returncode == 0, replay.stderr
    assert len(json.loads(replay.stdout)) == 1

    append = run_cli(log, "append", '{"value":"next"}')
    assert append.returncode == 0, append.stderr

    replay = run_cli(log, "replay")
    assert replay.returncode == 0, replay.stderr
    events = json.loads(replay.stdout)
    assert [e["sequence"] for e in events] == [1, 2]
    assert events[1]["payload"] == {"value": "next"}


def test_complete_corruption_is_rejected(tmp_path):
    log = tmp_path / "events.log"
    assert run_cli(log, "append", '{"value":"original"}').returncode == 0

    record = json.loads(log.read_text(encoding="utf-8"))
    record["payload"]["value"] = "tampered"
    log.write_text(json.dumps(record) + "\n", encoding="utf-8")

    replay = run_cli(log, "replay")
    assert replay.returncode != 0
    assert replay.stderr


def test_middle_of_log_corruption_is_rejected(tmp_path):
    log = tmp_path / "events.log"
    for value in (1, 2, 3):
        result = run_cli(log, "append", json.dumps({"value": value}))
        assert result.returncode == 0, result.stderr

    lines = log.read_text(encoding="utf-8").splitlines()
    record = json.loads(lines[1])
    record["payload"]["value"] = 999
    lines[1] = json.dumps(record)
    log.write_text("\n".join(lines) + "\n", encoding="utf-8")

    replay = run_cli(log, "replay")
    assert replay.returncode != 0
    assert replay.stderr


def test_replay_is_deterministic(tmp_path):
    log = tmp_path / "events.log"
    assert run_cli(log, "append", '{"b":2,"a":1}').returncode == 0

    first = run_cli(log, "replay")
    second = run_cli(log, "replay")

    assert first.returncode == second.returncode == 0
    assert first.stdout == second.stdout


def test_invalid_payload_is_rejected(tmp_path):
    result = run_cli(tmp_path / "events.log", "append", "not-json")
    assert result.returncode != 0
    assert result.stderr
def test_complete_malformed_record_is_rejected(tmp_path):
    log = tmp_path / "events.log"
    log.write_text("{not valid json}\n", encoding="utf-8")

    replay = run_cli(log, "replay")

    assert replay.returncode != 0
    assert replay.stderr


def test_sequence_number_gap_is_rejected(tmp_path):
    log = tmp_path / "events.log"

    first = run_cli(log, "append", '{"value":1}')
    second = run_cli(log, "append", '{"value":2}')
    assert first.returncode == second.returncode == 0

    lines = log.read_text(encoding="utf-8").splitlines()
    record = json.loads(lines[1])
    record["sequence"] = 3
    lines[1] = json.dumps(record)
    log.write_text("\n".join(lines) + "\n", encoding="utf-8")

    replay = run_cli(log, "replay")

    assert replay.returncode != 0
    assert replay.stderr


def test_non_object_payload_is_rejected(tmp_path):
    log = tmp_path / "events.log"

    result = run_cli(log, "append", '["not", "an", "object"]')

    assert result.returncode != 0
    assert result.stderr
