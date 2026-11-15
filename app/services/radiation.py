"""
AETHER — Radiation Monitoring Service

Stores accumulated astronaut radiation doses and creates alerts for
measurements that meet the hardcoded dose bands. This is not a Core.
"""

import math
from datetime import datetime, timezone

from app.cores import astronaut, emergency_response
from app.database.connection import get_connection


RADIATION_THRESHOLDS = {
    "medium": 200,
    "high": 300,
    "critical": 400
}
DOSE_INCREASE_PER_SIX_MONTHS_MSV = 50
MAX_PROJECTION_MONTHS = 24
MAX_RECENT_MEASUREMENTS = 100


def _validate_dose(dose_msv):
    if (
        not isinstance(dose_msv, (int, float))
        or isinstance(dose_msv, bool)
        or not math.isfinite(dose_msv)
        or dose_msv < 0
    ):
        raise ValueError("Dose must be a finite, non-negative number of mSv.")


def get_severity(dose_msv):
    """Return the highest band reached by an accumulated dose."""

    _validate_dose(dose_msv)

    for severity in ("critical", "high", "medium"):
        if dose_msv >= RADIATION_THRESHOLDS[severity]:
            return severity

    return None


def get_current_timestamp():
    """Return the current UTC timestamp."""

    return datetime.now(timezone.utc).isoformat()


def record_measurement(astronaut_id, dose_msv, source="manual_entry", notes=""):
    """Validate and persist one accumulated dose reading."""

    if not isinstance(astronaut_id, str) or not astronaut_id.strip():
        raise ValueError("A valid astronaut ID is required.")

    _validate_dose(dose_msv)

    if not isinstance(source, str) or not source.strip():
        raise ValueError("A measurement source is required.")

    if not isinstance(notes, str):
        raise ValueError("Notes must be text.")

    astronaut_id = astronaut_id.strip()
    source = source.strip()
    notes = notes.strip() or None

    with get_connection() as connection:
        astronaut_row = connection.execute(
            "SELECT id FROM astronauts WHERE id = ?",
            (astronaut_id,)
        ).fetchone()

        if astronaut_row is None:
            raise ValueError("Astronaut does not exist.")

        cursor = connection.execute(
            """
            INSERT INTO radiation_measurements (
                astronaut_id, dose_msv, source, notes, timestamp
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                astronaut_id,
                float(dose_msv),
                source,
                notes,
                get_current_timestamp()
            )
        )
        row = connection.execute(
            """
            SELECT m.*, a.name AS astronaut_name
            FROM radiation_measurements AS m
            JOIN astronauts AS a ON a.id = m.astronaut_id
            WHERE m.id = ?
            """,
            (cursor.lastrowid,)
        ).fetchone()

    return dict(row)


def process_measurement(astronaut_id, dose_msv, source="manual_entry", notes=""):
    """Record a reading and create a fresh alert when it reaches a band."""

    measurement = record_measurement(
        astronaut_id=astronaut_id,
        dose_msv=dose_msv,
        source=source,
        notes=notes
    )
    severity = get_severity(measurement["dose_msv"])
    alert = None
    alert_error = None

    if severity:
        threshold = RADIATION_THRESHOLDS[severity]
        description = (
            f"Accumulated dose: {measurement['dose_msv']:g} mSv\n"
            f"Alert threshold: {threshold} mSv ({severity.upper()})\n"
            f"Source: {measurement['source']}\n"
            f"Recorded: {measurement['timestamp']}"
        )

        if measurement["notes"]:
            description += f"\nNotes: {measurement['notes']}"

        try:
            alert = emergency_response.create_alert(
                astronaut_id=measurement["astronaut_id"],
                title="Radiation dose threshold exceeded",
                description=description,
                severity=severity,
                source="radiation"
            )
        except Exception as error:
            alert_error = str(error)

    return {
        "measurement": measurement,
        "severity": severity,
        "alert": alert,
        "alert_error": alert_error
    }


def project_dose(baseline_msv, months_ahead):
    """Project accumulated dose using 50 mSv per six months."""

    _validate_dose(baseline_msv)

    if (
        not isinstance(months_ahead, (int, float))
        or isinstance(months_ahead, bool)
        or not math.isfinite(months_ahead)
        or not 0 <= months_ahead <= MAX_PROJECTION_MONTHS
    ):
        raise ValueError(
            f"Projection must be between 0 and {MAX_PROJECTION_MONTHS} months."
        )

    projected_dose = (
        float(baseline_msv)
        + float(months_ahead) * DOSE_INCREASE_PER_SIX_MONTHS_MSV / 6
    )

    return {
        "months_ahead": float(months_ahead),
        "dose_msv": projected_dose,
        "severity": get_severity(projected_dose)
    }


def get_radiation_page_data(selected_astronaut_id=None):
    """Assemble Radiation page readings, baselines, and summary metrics."""

    astronauts = astronaut.get_all_astronauts()

    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT m.*, a.name AS astronaut_name
            FROM radiation_measurements AS m
            JOIN astronauts AS a ON a.id = m.astronaut_id
            ORDER BY m.timestamp DESC, m.id DESC
            LIMIT ?
            """,
            (MAX_RECENT_MEASUREMENTS,)
        ).fetchall()
        baseline_rows = connection.execute(
            """
            SELECT astronaut_id, dose_msv
            FROM (
                SELECT astronaut_id, dose_msv,
                       ROW_NUMBER() OVER (
                           PARTITION BY astronaut_id
                           ORDER BY timestamp DESC, id DESC
                       ) AS recency
                FROM radiation_measurements
            )
            WHERE recency = 1
            """
        ).fetchall()
        total_readings = connection.execute(
            "SELECT COUNT(*) FROM radiation_measurements"
        ).fetchone()[0]
        monitored_astronauts = connection.execute(
            "SELECT COUNT(DISTINCT astronaut_id) FROM radiation_measurements"
        ).fetchone()[0]

    dose_baselines = {}

    for row in baseline_rows:
        dose_baselines.setdefault(row["astronaut_id"], row["dose_msv"])

    for person in astronauts:
        dose_baselines.setdefault(person["id"], 0)

    selected_ids = set(dose_baselines)
    if selected_astronaut_id not in selected_ids:
        selected_astronaut_id = next(iter(dose_baselines), "")

    active_radiation_alerts = [
        alert
        for alert in emergency_response.get_all_alerts(status="Active")
        if alert["source"] == "radiation"
    ]

    return {
        "page_title": "Radiation Monitoring",
        "page_description": (
            "Record accumulated dose and review illustrative future projections."
        ),
        "core_status": "Monitoring",
        "metrics": [
            {
                "label": "Recorded Readings",
                "value": total_readings,
                "detail": "Accumulated dose measurements"
            },
            {
                "label": "Astronauts Monitored",
                "value": monitored_astronauts,
                "detail": "With recorded dose readings"
            },
            {
                "label": "Active Radiation Alerts",
                "value": len(active_radiation_alerts),
                "detail": "Resolve from Emergency Response"
            }
        ],
        "astronauts": astronauts,
        "measurements": [dict(row) for row in rows],
        "dose_baselines": dose_baselines,
        "selected_astronaut_id": selected_astronaut_id,
        "selected_baseline_msv": dose_baselines.get(
            selected_astronaut_id,
            0
        ),
        "thresholds": RADIATION_THRESHOLDS,
        "projection_rate_per_month": (
            DOSE_INCREASE_PER_SIX_MONTHS_MSV / 6
        ),
        "max_projection_months": MAX_PROJECTION_MONTHS
    }
