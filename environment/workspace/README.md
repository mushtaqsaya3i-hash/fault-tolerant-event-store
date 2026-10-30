# Durable Event Store

A local append-only event log implemented in Python.

## Append an event
python cli.py --log events.jsonl append '{"type":"user_created","user_id":42}'

## Replay events
python cli.py --log events.jsonl replay

Each complete line stores a sequence number, payload, and SHA-256 checksum. Sequence numbers start at 1 and increase by one.

Replay ignores an incomplete final record without a newline. Complete malformed records and checksum mismatches produce errors. Appending removes an incomplete final tail before writing the next record.
