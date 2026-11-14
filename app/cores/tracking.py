
"""
AETHER — Tracking Core

Stores and retrieves validated astronaut measurements using SQLite.
"""

from app.database.connection import get_connection
from app.cores.evaluation import evaluate_record


def record_measurement(record):
    """Validate and store a measurement."""

    evaluation = evaluate_record(record)

    if not evaluation["valid"]:
        raise ValueError(evaluation["reason"])

    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO measurements (
                astronaut_id,
                measurement,
                value,
                unit,
                source,
                simulated,
                timestamp
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                record["astronaut_id"],
                record["measurement"],
                record["value"],
                record["unit"],
                record["source"],
                int(bool(record.get("simulated", False))),
                record["timestamp"]
            )
        )

        measurement_id = cursor.lastrowid

    return {
        "id": measurement_id,
        **record,
        "simulated": bool(record.get("simulated", False))
    }


def get_measurements(astronaut_id=None, measurement=None):
    """Retrieve measurements with optional filters."""

    query = "SELECT * FROM measurements WHERE 1=1"
    parameters = []

    if astronaut_id is not None:
        query += " AND astronaut_id = ?"
        parameters.append(astronaut_id)

    if measurement is not None:
        query += " AND measurement = ?"
        parameters.append(measurement)

    query += " ORDER BY id ASC"

    with get_connection() as connection:
        rows = connection.execute(
            query, parameters
        ).fetchall()

    results = []

    for row in rows:
        item = dict(row)
        item["simulated"] = bool(item["simulated"])
        results.append(item)

    return results


def get_latest_measurement(astronaut_id, measurement):
    """Retrieve the latest recorded measurement."""

    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT * FROM measurements
            WHERE astronaut_id = ? AND measurement = ?
            ORDER BY id DESC
            LIMIT 1
            """,
            (astronaut_id, measurement)
        ).fetchone()

    if row is None:
        return None

    result = dict(row)
    result["simulated"] = bool(result["simulated"])

    return result


def get_statistics():
    """Return Tracking Core statistics."""

    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT
                COUNT(*) AS total_measurements,
                COUNT(DISTINCT astronaut_id) AS astronauts_tracked,
                COUNT(DISTINCT measurement) AS measurement_types
            FROM measurements
            """
        ).fetchone()

    return dict(row)


def get_status():
    """Check database access and return Tracking Core status."""

    return {"id": "tracking", "name": "Tracking", "status": "INOP (Manually Set)"}

    try:
        statistics = get_statistics()

        return {
            "id": "tracking",
            "name": "Tracking",
            "status": "Operational",
            **statistics
        }

    except Exception as error:
        return {
            "id": "tracking",
            "name": "Tracking",
            "status": "Error",
            "error": str(error)
        }
