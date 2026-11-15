
"""
AETHER — Dashboard Service

Collects live application data from the five cores
and prepares it for the dashboard template.
"""

from calendar import monthrange
from datetime import datetime, timezone

from app.cores import astronaut
from app.cores import evaluation
from app.cores import tracking
from app.cores import health
from app.cores import emergency_response
from app.database.connection import get_connection
from app.services import radiation


CORE_MODULES = [
    (astronaut, "Astronaut", "Crew profiles and astronaut records.", "♙"),
    (evaluation, "Evaluation", "Collection and validation of incoming data.", "▤"),
    (tracking, "Tracking", "Monitoring astronaut and mission measurements.", "⌁"),
    (health, "Health", "Health analysis and trend identification.", "◎"),
    (emergency_response, "Emergency Response", "Alerts and emergency management.", "⚑")
]


def safe_call(function, default=None, *args, **kwargs):
    """Prevent one failed core from breaking the dashboard."""

    try:
        return function(*args, **kwargs)
    except Exception:
        return default


def _get_heart_rate_chart():
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT a.id AS astronaut_id, a.name, h.value, h.unit, h.timestamp
            FROM astronauts AS a
            JOIN health_measurements AS h
              ON h.astronaut_id = a.id
             AND h.measurement = 'heart_rate'
             AND h.id = (
                 SELECT latest.id
                 FROM health_measurements AS latest
                 WHERE latest.astronaut_id = a.id
                   AND latest.measurement = 'heart_rate'
                 ORDER BY latest.timestamp DESC, latest.id DESC
                 LIMIT 1
             )
            ORDER BY a.name, a.id
            """
        ).fetchall()

    return [dict(row) for row in rows]


def _add_months(timestamp, months):
    month_index = timestamp.month - 1 + months
    year = timestamp.year + month_index // 12
    month = month_index % 12 + 1
    day = min(timestamp.day, monthrange(year, month)[1])
    return timestamp.replace(year=year, month=month, day=day)


def _get_radiation_chart():
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT astronaut_id, astronaut_name, dose_msv, timestamp
            FROM (
                SELECT m.astronaut_id, a.name AS astronaut_name,
                       m.dose_msv, m.timestamp, m.id,
                       ROW_NUMBER() OVER (
                           PARTITION BY m.astronaut_id
                           ORDER BY m.timestamp DESC, m.id DESC
                       ) AS recency
                FROM radiation_measurements AS m
                JOIN astronauts AS a ON a.id = m.astronaut_id
            )
            WHERE recency <= 12
            ORDER BY astronaut_name, astronaut_id, timestamp, id
            """
        ).fetchall()

    grouped = {}
    for row in rows:
        series = grouped.setdefault(
            row["astronaut_id"],
            {
                "astronaut_id": row["astronaut_id"],
                "name": row["astronaut_name"],
                "actual": [],
                "predicted": []
            }
        )
        series["actual"].append({
            "timestamp": row["timestamp"],
            "dose_msv": row["dose_msv"]
        })

    for series in grouped.values():
        last_reading = series["actual"][-1]
        last_timestamp = datetime.fromisoformat(
            last_reading["timestamp"].replace("Z", "+00:00")
        )
        if last_timestamp.tzinfo is None:
            last_timestamp = last_timestamp.replace(tzinfo=timezone.utc)

        for months_ahead in (6, 12, 18, 24):
            series["predicted"].append({
                "timestamp": _add_months(
                    last_timestamp,
                    months_ahead
                ).isoformat(),
                "dose_msv": radiation.project_dose(
                    last_reading["dose_msv"],
                    months_ahead
                )["dose_msv"],
                "months_ahead": months_ahead
            })

    return list(grouped.values())


def get_dashboard_data():

    # Retrieve data independently.
    astronauts = safe_call(astronaut.get_all_astronauts, [])
    tracking_stats = safe_call(tracking.get_statistics, {})
    evaluation_stats = safe_call(evaluation.get_statistics, {})
    health_stats = safe_call(health.get_statistics, {})
    alert_stats = safe_call(emergency_response.get_statistics, {})

    alerts = safe_call(emergency_response.get_all_alerts, [], status="Active")
    heart_rate_chart = safe_call(_get_heart_rate_chart, [])
    radiation_chart = safe_call(_get_radiation_chart, [])

    # Prepare core status cards.
    cores = []

    for module, name, description, icon in CORE_MODULES:
        status_data = safe_call(module.get_status, {})

        if not status_data:
            status_data = {
                "status": "Error"
            }

        cores.append({
            "id": status_data.get("id", module.__name__.split(".")[-1]),
            "name": name,
            "description": description,
            "icon": icon,
            "status": status_data.get("status", "Unknown")
        })

    # Calculate summary metrics.
    astronaut_count = len(astronauts)
    active_alerts = alert_stats.get("active_alerts", 0)
    total_measurements = tracking_stats.get("total_measurements", 0)
    processed_records = evaluation_stats.get("processed", 0)

    return {
        "mission": {
            "name": "AETHER Mission Control",
            "description": "Central monitoring and evaluation of astronaut health and mission conditions.",
            "status": "Operational"
        },

        "metrics": [
            {
                "label": "Astronauts",
                "value": astronaut_count,
                "detail": "Registered crew members"
            },
            {
                "label": "Active Alerts",
                "value": active_alerts,
                "detail": "Unresolved emergency alerts"
            },
            {
                "label": "Data Records",
                "value": total_measurements,
                "detail": f"{processed_records} records evaluated"
            },
            {
                "label": "Core Systems",
                "value": len(cores),
                "detail": "Registered systems"
            }
        ],

        "cores": cores,

        "crew": astronauts,
        "heart_rate_chart": heart_rate_chart,
        "radiation_chart": radiation_chart,

        "health": [
            {
                "name": "Health Analyses",
                "description": "Completed astronaut health analyses.",
                "value": health_stats.get("analyses_performed", 0),
                "status": "Analysis records"
            },
            {
                "name": "Tracked Measurements",
                "description": "Measurements recorded by the Tracking Core.",
                "value": total_measurements,
                "status": "Recorded measurements"
            }
        ],

        "alerts": alerts,

        "timeline": []
    }
