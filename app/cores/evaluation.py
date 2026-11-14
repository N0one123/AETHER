
"""
AETHER — Evaluation Core

Handles:
- Incoming measurement validation and storage.
- Astronaut symptom evaluation.
- Persistent evaluation statistics.
- Evaluation Core status.
"""

from app.database.connection import get_connection

from app.engines.evaluation_engine import (
    evaluate_symptoms,
    get_symptom_catalogue,
    get_engine_status,
)


# --------------------------------------------------
# MEASUREMENT VALIDATION
# --------------------------------------------------

REQUIRED_FIELDS = {
    "astronaut_id",
    "measurement",
    "value",
    "unit",
    "source",
    "timestamp"
}


def evaluate_record(record):
    """Validate a measurement record and store the result."""

    reason = None

    if not isinstance(record, dict):
        reason = "Record must be a dictionary."

    else:
        missing = REQUIRED_FIELDS - record.keys()

        if missing:
            reason = f"Missing fields: {', '.join(sorted(missing))}"

        elif (
            not isinstance(record["value"], (int, float))
            or isinstance(record["value"], bool)
        ):
            reason = "Measurement value must be numeric."

        elif not record["measurement"] or not record["unit"]:
            reason = "Measurement and unit cannot be empty."

        elif not record["astronaut_id"]:
            reason = "Astronaut ID cannot be empty."

        elif not record["source"] or not record["timestamp"]:
            reason = "Source and timestamp cannot be empty."

    valid = reason is None

    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO evaluation_records (
                astronaut_id,
                measurement,
                value,
                unit,
                source,
                timestamp,
                valid,
                reason
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                record.get("astronaut_id") if isinstance(record, dict) else None,
                record.get("measurement") if isinstance(record, dict) else None,
                (
                    record.get("value")
                    if isinstance(record, dict)
                    and isinstance(record.get("value"), (int, float))
                    and not isinstance(record.get("value"), bool)
                    else None
                ),
                record.get("unit") if isinstance(record, dict) else None,
                record.get("source") if isinstance(record, dict) else None,
                record.get("timestamp") if isinstance(record, dict) else None,
                int(valid),
                reason
            )
        )

    if valid:
        return {
            "valid": True,
            "record": record
        }

    return {
        "valid": False,
        "reason": reason
    }


# --------------------------------------------------
# SYMPTOM EVALUATION
# --------------------------------------------------

def evaluate_astronaut_symptoms(selected_symptoms):
    """
    Evaluate reported symptoms against the symptom catalogue.

    This identifies documented associations.
    It does not diagnose medical conditions.
    """

    return evaluate_symptoms(selected_symptoms)


def get_symptoms():
    """Return the available symptom catalogue."""

    return get_symptom_catalogue()


# --------------------------------------------------
# STATISTICS
# --------------------------------------------------

def get_statistics():
    """Return persistent measurement evaluation statistics."""

    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT
                COUNT(*) AS processed,
                SUM(valid) AS accepted,
                SUM(CASE WHEN valid = 0 THEN 1 ELSE 0 END) AS rejected
            FROM evaluation_records
            """
        ).fetchone()

    return {
        "processed": row["processed"],
        "accepted": row["accepted"] or 0,
        "rejected": row["rejected"] or 0
    }


# --------------------------------------------------
# CORE STATUS
# --------------------------------------------------

def get_status():
    """Return the current Evaluation Core status."""

    try:
        statistics = get_statistics()
        engine_status = get_engine_status()

        if engine_status.get("status") != "Operational":
            raise RuntimeError("Evaluation engine is unavailable.")

        return {
            "id": "evaluation",
            "name": "Evaluation",
            "status": "Operational",
            **statistics,
            "conditions": engine_status.get("conditions", 0),
            "symptoms": engine_status.get("symptoms", 0),
            "sources": engine_status.get("sources", 0)
        }

    except Exception:
        return {
            "id": "evaluation",
            "name": "Evaluation",
            "status": "Error"
        }
