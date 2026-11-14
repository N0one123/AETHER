
"""
AETHER — Dashboard Service

Collects live application data from the five cores
and prepares it for the dashboard template.
"""

from app.cores import astronaut
from app.cores import evaluation
from app.cores import tracking
from app.cores import health
from app.cores import emergency_response


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


def get_dashboard_data():

    # Retrieve data independently.
    astronauts = safe_call(astronaut.get_all_astronauts, [])
    tracking_stats = safe_call(tracking.get_statistics, {})
    evaluation_stats = safe_call(evaluation.get_statistics, {})
    health_stats = safe_call(health.get_statistics, {})
    alert_stats = safe_call(emergency_response.get_statistics, {})

    alerts = safe_call(emergency_response.get_all_alerts, [], status="Active")

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
