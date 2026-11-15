
"""
AETHER — Emergency Response Core

Manages persistent alerts using SQLite.
"""

from app.database.connection import get_connection


ALLOWED_SEVERITIES = {
    "low",
    "medium",
    "high",
    "critical"
}


def create_alert(
    astronaut_id,
    title,
    description,
    severity="medium",
    source="system"
):
    """Create and store a new alert."""

    if not astronaut_id:
        raise ValueError("Astronaut ID is required.")

    if not title or not title.strip():
        raise ValueError("Alert title is required.")

    severity = severity.lower().strip()

    if severity not in ALLOWED_SEVERITIES:
        raise ValueError(f"Invalid alert severity: {severity}")

    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO alerts (
                id,
                astronaut_id,
                title,
                description,
                severity,
                source
            )
            VALUES (
                lower(hex(randomblob(16))),
                ?, ?, ?, ?, ?
            )
            """,
            (
                astronaut_id,
                title.strip(),
                description,
                severity,
                source
            )
        )

        alert_id = cursor.lastrowid

        alert = connection.execute(
            "SELECT * FROM alerts WHERE rowid = ?",
            (alert_id,)
        ).fetchone()

    return dict(alert)


def get_alert(alert_id):
    """Retrieve a specific alert."""

    with get_connection() as connection:
        row = connection.execute(
            "SELECT * FROM alerts WHERE id = ?",
            (alert_id,)
        ).fetchone()

    return dict(row) if row else None


def get_all_alerts(status=None):
    """Retrieve alerts, optionally filtered by status."""

    query = "SELECT * FROM alerts"
    parameters = []

    if status is not None:
        query += " WHERE status = ?"
        parameters.append(status)

    query += " ORDER BY created_at DESC, rowid DESC"

    with get_connection() as connection:
        rows = connection.execute(
            query, parameters
        ).fetchall()

    return [dict(row) for row in rows]


def get_active_health_alert(
    astronaut_id,
    title,
    alert_source,
    measurement_source,
    simulation_session_id=None
):
    """Find an active Health alert for the exact measurement identity."""

    if alert_source not in {"health", "health_simulation"}:
        raise ValueError("Only Health-generated alerts can be queried.")

    conditions = [
        "astronaut_id = ?",
        "title = ?",
        "source = ?",
        "status = 'Active'",
        "instr(COALESCE(description, ''), ?) > 0"
    ]
    parameters = [
        astronaut_id,
        title,
        alert_source,
        f"Source: {measurement_source}\n"
    ]

    if simulation_session_id:
        conditions.append("instr(COALESCE(description, ''), ?) > 0")
        parameters.append(
            f"Simulation Session: {simulation_session_id}"
        )

    with get_connection() as connection:
        row = connection.execute(
            f"""
            SELECT * FROM alerts
            WHERE {" AND ".join(conditions)}
            ORDER BY created_at DESC, rowid DESC
            LIMIT 1
            """,
            parameters
        ).fetchone()

    return dict(row) if row else None


def resolve_alert(alert_id):
    """Mark an alert as resolved."""

    with get_connection() as connection:
        cursor = connection.execute(
            """
            UPDATE alerts
            SET status = 'Resolved',
                resolved_at = CURRENT_TIMESTAMP
            WHERE id = ? AND status = 'Active'
            """,
            (alert_id,)
        )

    return cursor.rowcount > 0


def resolve_matching_health_alerts(
    astronaut_id,
    title,
    alert_source,
    measurement_source,
    simulation_session_id=None
):
    """Resolve active Health alerts matching one measurement identity."""

    if alert_source not in {"health", "health_simulation"}:
        raise ValueError("Only Health-generated alerts can be auto-resolved.")

    source_marker = f"Source: {measurement_source}\n"
    session_marker = (
        f"Simulation Session: {simulation_session_id}"
        if simulation_session_id
        else None
    )

    with get_connection() as connection:
        cursor = connection.execute(
            """
            UPDATE alerts
            SET status = 'Resolved',
                resolved_at = CURRENT_TIMESTAMP
            WHERE astronaut_id = ?
              AND title = ?
              AND source = ?
              AND status = 'Active'
              AND instr(COALESCE(description, ''), ?) > 0
              AND (
                    ? IS NULL
                    OR instr(COALESCE(description, ''), ?) > 0
              )
            """,
            (
                astronaut_id,
                title,
                alert_source,
                source_marker,
                session_marker,
                session_marker
            )
        )

    return cursor.rowcount


def get_statistics():
    """Return emergency response statistics."""

    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT
                COUNT(*) AS total_alerts,

                SUM(
                    CASE WHEN status = 'Active'
                    THEN 1 ELSE 0 END
                ) AS active_alerts,

                SUM(
                    CASE WHEN status = 'Resolved'
                    THEN 1 ELSE 0 END
                ) AS resolved_alerts,

                SUM(
                    CASE WHEN status = 'Active'
                    AND severity = 'critical'
                    THEN 1 ELSE 0 END
                ) AS critical_alerts,

                SUM(
                    CASE WHEN status = 'Active'
                    AND severity = 'high'
                    THEN 1 ELSE 0 END
                ) AS high_alerts,

                SUM(
                    CASE WHEN status = 'Active'
                    AND severity = 'medium'
                    THEN 1 ELSE 0 END
                ) AS medium_alerts,

                SUM(
                    CASE WHEN status = 'Active'
                    AND severity = 'low'
                    THEN 1 ELSE 0 END
                ) AS low_alerts

            FROM alerts
            """
        ).fetchone()

    return {
        key: value or 0
        for key, value in dict(row).items()
    }


def get_status():
    """Check database access and return core status."""

    try:
        statistics = get_statistics()

        return {
            "id": "emergency",
            "name": "Emergency Response",
            "status": "Operational",
            **statistics
        }

    except Exception as error:
        return {
            "id": "emergency",
            "name": "Emergency Response",
            "status": "Error",
            "error": str(error)
        }
