
"""
AETHER — Tracking Page

Prepares measurement data for the Tracking Core interface.
"""

from app.cores import tracking


def get_tracking_page_data(
    horizon_hours=tracking.DEFAULT_FORECAST_HOURS
):

    measurements = tracking.get_measurements()
    statistics = tracking.get_statistics()
    status = tracking.get_status()
    forecasts = tracking.get_forecasts(measurements, horizon_hours)

    astronauts_by_id = {}

    for measurement in measurements:
        astronaut_id = measurement["astronaut_id"]
        astronaut = astronauts_by_id.setdefault(
            astronaut_id,
            {
                "astronaut_id": astronaut_id,
                "streams": {
                    stream_key: {
                        "key": stream_key,
                        **stream_info,
                        "measurements": [],
                        "forecasts": [],
                        "series": {}
                    }
                    for stream_key, stream_info in tracking.STREAMS.items()
                }
            }
        )
        astronaut["streams"][measurement["stream"]]["measurements"].append(
            measurement
        )
        series_key = (measurement["measurement"], measurement["unit"])
        stream_series = astronaut["streams"][measurement["stream"]]["series"]
        series = stream_series.setdefault(
            series_key,
            {
                "measurement": measurement["measurement"],
                "unit": measurement["unit"],
                "sample_count": 0,
                "forecast": None
            }
        )
        series["sample_count"] += 1

    for astronaut in astronauts_by_id.values():
        for stream in astronaut["streams"].values():
            stream["measurements"].sort(
                key=lambda item: (
                    tracking.parse_timestamp(item["timestamp"]),
                    item["id"]
                ),
                reverse=True
            )

    for forecast in forecasts:
        stream = astronauts_by_id[forecast["astronaut_id"]]["streams"][
            forecast["stream"]
        ]
        stream["forecasts"].append(forecast)
        stream["series"][
            (forecast["measurement"], forecast["unit"])
        ]["forecast"] = forecast

    for astronaut in astronauts_by_id.values():
        for stream in astronaut["streams"].values():
            stream["series"] = sorted(
                stream["series"].values(),
                key=lambda item: (item["measurement"], item["unit"])
            )

    astronauts = sorted(
        astronauts_by_id.values(),
        key=lambda item: item["astronaut_id"].casefold()
    )

    return {
        "page_title": "Tracking Core",
        "page_description": (
            "Review time-ordered astronaut measurements and separate "
            "real-data and Sim Lab trend projections."
        ),
        "core_status": status.get("status", "Unknown"),
        "tracking_astronauts": astronauts,
        "forecast_horizon_hours": horizon_hours,

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
        "forecasts": forecasts,

        "content_title": "Astronaut Timelines",
        "content_description": (
            "Real Health and Sim Lab records are displayed and forecast "
            "in separate data streams."
        )
    }
