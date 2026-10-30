import argparse
import json
import sys

from event_store import EventStore, EventStoreError


def main():
    parser = argparse.ArgumentParser(description="Append-only event store")
    parser.add_argument("--log", required=True, help="Path to the event log")

    commands = parser.add_subparsers(dest="command", required=True)

    append_cmd = commands.add_parser("append", help="Append a JSON event")
    append_cmd.add_argument("payload", help="Event payload as a JSON object")

    commands.add_parser("replay", help="Replay stored events")

    args = parser.parse_args()
    store = EventStore(args.log)

    try:
        if args.command == "append":
            try:
                payload = json.loads(args.payload)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSON payload: {exc.msg}") from exc

            event = store.append(payload)
            print(json.dumps(event, sort_keys=True))
        else:
            print(json.dumps(store.replay(), sort_keys=True))
    except (EventStoreError, OSError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
