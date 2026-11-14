
"""
AETHER — Tracking Page

Prepares measurement data for the Tracking Core interface.
"""

from app.cores import tracking


def get_tracking_page_data():

    measurements = tracking.get_measurements()
    statistics = tracking.get_statistics()
    status = tracking.get_status()

    return {
        "page_title": "Tracking Core",
        "page_description": "Monitor and retrieve astronaut measurements.",
        "core_status": status.get("status", "Unknown"),

        "metrics": [
            {
                "label": "Measurements",
                "value": statistics["total_measurements"],
                "detail": "Total recorded measurements"
            },
            {
                "label": "Astronauts Tracked",
                "value": statistics["astronauts_tracked"],
                "detail": "Astronauts with recorded data"
            },
            {
                "label": "Measurement Types",
                "value": statistics["measurement_types"],
                "detail": "Distinct measurement categories"
            }
        ],

        "actions": [
            {
                "id": "record-measurement",
                "label": "Record Measurement"
            }
        ],

        "measurements": measurements,

        "content_title": "Recorded Measurements",
        "content_description": "Measurement records currently stored in AETHER."
    }
