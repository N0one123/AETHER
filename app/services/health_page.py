
"""
AETHER — Health Page

Prepares health monitoring data for the interface.
"""

from app.cores import health


def get_health_page_data():

    statistics = health.get_statistics()
    status = health.get_status()

    measurements = health.get_measurements(limit=100)
    rules = health.get_monitoring_rules()

    return {
        "page_title": "Health Monitoring",
        "page_description": (
            "Monitor astronaut health measurements "
            "and detect abnormalities."
        ),

        "core_status": status.get("status", "Unknown"),

        "metrics": [
            {
                "label": "Measurements",
                "value": statistics["total_measurements"],
                "detail": "Total health measurements"
            },
            {
                "label": "Astronauts Monitored",
                "value": statistics["astronauts_monitored"],
                "detail": "Astronauts with health data"
            },
            {
                "label": "Measurement Types",
                "value": statistics["measurement_types"],
                "detail": "Distinct health indicators"
            },
            {
                "label": "Abnormalities",
                "value": statistics["abnormal_measurements"],
                "detail": "Outside configured monitoring rules"
            }
        ],

        "measurements": measurements,
        "monitoring_rules": rules,
        "default_rules_enabled": health.get_default_monitoring_rules_enabled(),

        "simulated_measurements": statistics[
            "simulated_measurements"
        ],

        "real_measurements": statistics[
            "non_simulated_measurements"
        ],

        "content_title": "Health Monitoring",
        "content_description": (
            "Health measurements and monitoring configuration."
        )
    }
