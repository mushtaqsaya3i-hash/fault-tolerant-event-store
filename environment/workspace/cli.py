"""Command-line interface for the durable event store."""

import argparse
import json
import sys

from event_store import EventStore, EventStoreError


def main():
    parser = argparse.ArgumentParser(description="Append-only event store")
    parser.add_argument("--log", required=True, help="Path to the event log")
    commands = parser.add_subparsers(dest="command", required=True)

    append_cmd = commands.add_parser("append", help="Append a JSON event")
    append_cmd.add_argument("payload", help="Event payload as JSON")

    commands.add_parser("replay", help="Replay stored events")
    args = parser.parse_args()

    try:
        store = EventStore(args.log)
        if args.command == "append":
            payload = json.loads(args.payload)
            result = store.append(payload)
        else:
            result = store.replay()

        print(json.dumps(result, sort_keys=True))
        return 0
    except (EventStoreError, OSError, ValueError, NotImplementedError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
