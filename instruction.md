# Durable Event Store and Recovery

Implement a small, local, append-only event store in Python.

## Requirements

1. Append events to a durable on-disk log. Each event must have a stable sequence number and payload.
2. Detect incomplete or corrupted records using a documented record format.
3. Recover valid records in order after restarting the application.
4. Handle a truncated final record without losing previously committed events.
5. Detect corruption in the middle of the log instead of silently accepting invalid data.
6. Replay the same valid log deterministically.
7. Report malformed input and I/O failures clearly, using a non-zero exit status when appropriate.
8. Document the record format, recovery behavior, and command-line usage.
9. Each event payload must be a JSON object. Reject other JSON value types with a clear error.
10. Event sequence numbers must start at 1 and increase consecutively by 1. Reject unexpected sequence numbers during recovery.

## Constraints

* Use local files only; no external services are required.
* Keep the implementation maintainable and understandable.
* Do not hard-code expected test outputs.

## Deliverables

Provide the implementation, a README with usage examples, and tests covering normal operation, restart recovery, a truncated final record, middle-of-log corruption, and deterministic replay.

