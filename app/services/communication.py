
"""
AETHER — Core Communication Bus

Distributes events between cores with fault isolation
and persistent event history.
"""

import copy
import json

from app.database.connection import get_connection


SUBSCRIBERS = {}
EVENT_HISTORY = []

EVENTS_PUBLISHED = 0
DELIVERY_ERRORS = 0
STORAGE_ERRORS = 0


def subscribe(event_name, callback, core=None):
    """Subscribe a core or callback to an event."""

    if not isinstance(event_name, str) or not event_name.strip():
        raise ValueError("Event name must be a non-empty string.")

    if not callable(callback):
        raise TypeError("Callback must be callable.")

    if core is not None and (
        not isinstance(core, str) or not core.strip()
    ):
        raise ValueError("Core name must be a non-empty string.")

    listeners = SUBSCRIBERS.setdefault(event_name, [])

    for listener in listeners:
        if listener["callback"] == callback:
            return True

    listeners.append({
        "callback": callback,
        "core": core or getattr(callback, "__module__", "unknown")
    })

    return True


def unsubscribe(event_name, callback):
    """Remove a function from an event."""

    listeners = SUBSCRIBERS.get(event_name, [])

    for listener in listeners:
        if listener["callback"] == callback:
            listeners.remove(listener)

            if not listeners:
                del SUBSCRIBERS[event_name]

            return True

    return False


def publish(event_name, payload=None):
    """Publish an event with isolated subscriber failures."""

    global EVENTS_PUBLISHED
    global DELIVERY_ERRORS
    global STORAGE_ERRORS

    if not isinstance(event_name, str) or not event_name.strip():
        raise ValueError("Event name must be a non-empty string.")

    try:
        event_payload = copy.deepcopy(payload)
    except Exception:
        event_payload = payload

    event = {
        "name": event_name,
        "payload": event_payload
    }

    EVENTS_PUBLISHED += 1
    EVENT_HISTORY.append(event)

    try:
        with get_connection() as connection:
            connection.execute(
                """
                INSERT INTO events (event_name, payload)
                VALUES (?, ?)
                """,
                (
                    event_name,
                    json.dumps(event_payload, default=str)
                )
            )
    except Exception:
        STORAGE_ERRORS += 1

    delivered = 0
    errors = []

    for listener in list(SUBSCRIBERS.get(event_name, [])):
        try:
            listener["callback"](copy.deepcopy(event_payload))
            delivered += 1

        except Exception as error:
            DELIVERY_ERRORS += 1
            errors.append(str(error))

    return {
        "event": event_name,
        "delivered": delivered,
        "errors": errors
    }


def get_event_history(limit=100):
    """Retrieve recent events from SQLite."""

    if not isinstance(limit, int) or isinstance(limit, bool):
        raise TypeError("Limit must be an integer.")

    if limit < 0:
        raise ValueError("Limit cannot be negative.")

    if limit == 0:
        return []

    try:
        with get_connection() as connection:
            rows = connection.execute(
                """
                SELECT id, event_name, payload, timestamp
                FROM events
                ORDER BY id DESC
                LIMIT ?
                """,
                (limit,)
            ).fetchall()

        return [
            {
                "id": row["id"],
                "name": row["event_name"],
                "payload": json.loads(row["payload"]),
                "timestamp": row["timestamp"]
            }
            for row in reversed(rows)
        ]

    except Exception:
        return EVENT_HISTORY[-limit:]


def get_statistics():
    """Return communication statistics."""

    connected_cores = {
        listener["core"]
        for listeners in SUBSCRIBERS.values()
        for listener in listeners
    }

    try:
        with get_connection() as connection:
            total_events = connection.execute(
                "SELECT COUNT(*) FROM events"
            ).fetchone()[0]
    except Exception:
        total_events = EVENTS_PUBLISHED

    return {
        "events_published": total_events,
        "subscribers": len(connected_cores),
        "event_types": len(SUBSCRIBERS),
        "delivery_errors": DELIVERY_ERRORS,
        "storage_errors": STORAGE_ERRORS
    }


def get_status():
    """Return the current communication bus status."""

    if DELIVERY_ERRORS or STORAGE_ERRORS:
        current_status = "Degraded"
    elif not SUBSCRIBERS:
        current_status = "Awaiting connections"
    else:
        current_status = "Operational"

    return {
        "id": "communication",
        "name": "Core Communication Bus",
        "status": current_status,
        **get_statistics()
    }
