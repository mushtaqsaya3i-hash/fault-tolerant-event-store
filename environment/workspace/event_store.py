"""Append-only event store starter implementation."""

from pathlib import Path


class EventStoreError(Exception):
    """Raised when the event log is invalid or cannot be recovered safely."""


class EventStore:
    def __init__(self, path):
        self.path = Path(path)
        # TODO: Initialize the durable event log.

    def append(self, payload):
        """Validate and append one event; return the stored event."""
        raise NotImplementedError("Implement event append and durability")

    def replay(self):
        """Recover and return valid events in sequence order."""
        raise NotImplementedError("Implement recovery and deterministic replay")
