
"""
AETHER — Emergency Response Page

Prepares incident and alert data for the Emergency Response interface.
"""

from app.cores import emergency_response


def get_emergency_page_data():

    alerts = emergency_response.get_all_alerts()
    status = emergency_response.get_status()

    active_alerts = [
        alert for alert in alerts
        if str(alert.get("status", "")).lower() == "active"
    ]

    resolved_alerts = [
        alert for alert in alerts
        if str(alert.get("status", "")).lower() == "resolved"
    ]

    severity_levels = [
        "Critical",
        "High",
        "Medium",
        "Low"
    ]

    severity_counts = {
        level: sum(
            1 for alert in active_alerts
            if str(alert.get("severity", "")).lower() == level.lower()
        )
        for level in severity_levels
    }

    severity_priority = {
        "low": 1,
        "medium": 2,
        "high": 3,
        "critical": 4
    }

    highest_alert = max(
        active_alerts,
        key=lambda alert: severity_priority.get(
            str(alert.get("severity", "")).lower(), 0
        ),
        default=None
    )

    highest_severity = (
        str(highest_alert.get("severity", "")).lower()
        if highest_alert else "none"
    )

    pulse_class = (
        f"pulse-{highest_severity}"
        if highest_alert else "pulse-none"
    )

    return {
        "page_title": "Emergency Response",

        "page_description": (
            "Incident monitoring, alert management "
            "and response coordination."
        ),

        "core_status": status.get("status", "Unknown"),
        "highest_severity": highest_severity,
        "pulse_class": pulse_class,

        "metrics": [
            {
                "label": "Active Incidents",
                "value": len(active_alerts),
                "detail": "Currently unresolved"
            },
            {
                "label": "Critical Alerts",
                "value": severity_counts["Critical"],
                "detail": "Highest severity"
            },
            {
                "label": "Resolved Incidents",
                "value": len(resolved_alerts),
                "detail": "Successfully closed"
            },
            {
                "label": "Total Alerts",
                "value": len(alerts),
                "detail": "All recorded incidents"
            }
        ],

        "actions": [
            {
                "id": "create-alert",
                "label": "Create Alert"
            },
            {
                "id": "view-active",
                "label": "View Active Incidents"
            }
        ],

        "alerts": alerts,
        "active_alerts": active_alerts,
        "resolved_alerts": resolved_alerts,
        "severity_counts": severity_counts
    }
