"""
AETHER — Tracking Core

Collects eligible Health records into provenance-separated astronaut
timelines and produces numeric forecasts for sufficiently populated series.
"""

from datetime import datetime, timedelta, timezone

from app.database.connection import get_connection
from app.cores.evaluation import evaluate_record
from app.cores import health


SIM_LAB_SOURCE = "sim_lab"
DEFAULT_FORECAST_HOURS = 24
MIN_FORECAST_HOURS = 1
MAX_FORECAST_HOURS = 720
MINIMUM_FORECAST_POINTS = 3

STREAMS = {
    "real_health": {
        "label": "Real Health Data",
        "description": "Non-simulated measurements recorded by Health."
    },
    "sim_lab": {
        "label": "Sim Lab Data",
        "description": "Simulated measurements explicitly tagged as Sim Lab."
    }
}


def validate_forecast_horizon(horizon_hours):
    """Validate a forecast horizon expressed in whole hours."""

    if (
        isinstance(horizon_hours, bool)
        or not isinstance(horizon_hours, int)
        or not MIN_FORECAST_HOURS <= horizon_hours <= MAX_FORECAST_HOURS
    ):
        raise ValueError(
            f"Forecast horizon must be between {MIN_FORECAST_HOURS} "
            f"and {MAX_FORECAST_HOURS} hours."
        )

    return horizon_hours


def parse_timestamp(timestamp):
    """Parse an ISO timestamp and normalize it to UTC."""

    if not isinstance(timestamp, str) or not timestamp.strip():
        raise ValueError("A valid measurement timestamp is required.")

    try:
        parsed = datetime.fromisoformat(timestamp.strip().replace("Z", "+00:00"))
    except ValueError as error:
        raise ValueError("Measurement timestamps must be valid ISO 8601.") from error

    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)

    return parsed.astimezone(timezone.utc)


def record_measurement(record):
    """Validate a record and store it in Health's shared measurement stream."""

    evaluation = evaluate_record(record)

    if not evaluation["valid"]:
        raise ValueError(evaluation["reason"])

    return health.record_measurement(record)


def get_measurements(astronaut_id=None, measurement=None, stream=None):
    """Retrieve Health measurements from approved, separate source streams."""

    if astronaut_id is not None and (
        not isinstance(astronaut_id, str) or not astronaut_id.strip()
    ):
        raise ValueError("Invalid astronaut ID.")

    if measurement is not None and (
        not isinstance(measurement, str) or not measurement.strip()
    ):
        raise ValueError("Invalid measurement name.")

    if stream is not None and stream not in STREAMS:
        raise ValueError("Invalid Tracking data stream.")

    query = """
        SELECT
            id,
            astronaut_id,
            measurement,
            value,
            unit,
            source,
            simulated,
            timestamp,
            CASE
                WHEN simulated = 0 THEN 'real_health'
                ELSE 'sim_lab'
            END AS stream
        FROM health_measurements
        WHERE (
            simulated = 0
            OR (simulated = 1 AND LOWER(TRIM(source)) = ?)
        )
    """
    parameters = [SIM_LAB_SOURCE]

    if astronaut_id is not None:
        query += " AND astronaut_id = ?"
        parameters.append(astronaut_id.strip())

    if measurement is not None:
        query += " AND measurement = ?"
        parameters.append(measurement.strip().lower())

    if stream == "real_health":
        query += " AND simulated = 0"
    elif stream == "sim_lab":
        query += " AND simulated = 1 AND LOWER(TRIM(source)) = ?"
        parameters.append(SIM_LAB_SOURCE)

    query += " ORDER BY timestamp DESC, id DESC"

    with get_connection() as connection:
        rows = connection.execute(query, parameters).fetchall()

    results = []

    for row in rows:
        item = dict(row)
        item["simulated"] = bool(item["simulated"])
        item["stream_label"] = STREAMS[item["stream"]]["label"]
        results.append(item)

    return results


def get_latest_measurement(astronaut_id, measurement, stream="real_health"):
    """Retrieve the latest eligible measurement from one source stream."""

    results = get_measurements(
        astronaut_id=astronaut_id,
        measurement=measurement,
        stream=stream
    )

    return results[0] if results else None


def get_forecasts(records, horizon_hours=DEFAULT_FORECAST_HOURS):
    """Project separate timestamp-based trends per astronaut, stream and type."""

    validate_forecast_horizon(horizon_hours)
    series = {}

    for record in records:
        stream = record.get("stream")
        if stream not in STREAMS:
            continue

        key = (
            record["astronaut_id"],
            stream,
            record["measurement"],
            record["unit"]
        )
        series.setdefault(key, []).append({
            **record,
            "_parsed_timestamp": parse_timestamp(record["timestamp"])
        })

    forecasts = []

    for (astronaut_id, stream, measurement, unit), points in series.items():
        points.sort(key=lambda point: point["_parsed_timestamp"])
        if len(points) < MINIMUM_FORECAST_POINTS:
            continue

        first_timestamp = points[0]["_parsed_timestamp"]
        x_values = [
            (point["_parsed_timestamp"] - first_timestamp).total_seconds() / 3600
            for point in points
        ]
        y_values = [float(point["value"]) for point in points]
        mean_x = sum(x_values) / len(x_values)
        mean_y = sum(y_values) / len(y_values)
        variance = sum((x_value - mean_x) ** 2 for x_value in x_values)

        latest_timestamp = points[-1]["_parsed_timestamp"]
        observed_span_hours = x_values[-1] - x_values[0]
        effective_horizon_hours = min(horizon_hours, observed_span_hours)
        target_timestamp = latest_timestamp + timedelta(
            hours=effective_horizon_hours
        )
        horizon_capped = effective_horizon_hours < horizon_hours

        if variance == 0:
            forecasts.append({
                "astronaut_id": astronaut_id,
                "stream": stream,
                "stream_label": STREAMS[stream]["label"],
                "measurement": measurement,
                "unit": unit,
                "sample_count": len(points),
                "latest_timestamp": latest_timestamp.isoformat(),
                "forecast_timestamp": target_timestamp.isoformat(),
                "horizon_hours": horizon_hours,
                "effective_horizon_hours": effective_horizon_hours,
                "effective_horizon_minutes": effective_horizon_hours * 60,
                "horizon_capped": horizon_capped,
                "predicted_value": None,
                "trend_per_hour": None,
                "reason": (
                    "Measurements need at least two distinct timestamps "
                    "to estimate a trend."
                )
            })
            continue

        covariance = sum(
            (x_value - mean_x) * (y_value - mean_y)
            for x_value, y_value in zip(x_values, y_values)
        )
        trend_per_hour = covariance / variance
        target_x = (
            (target_timestamp - first_timestamp).total_seconds() / 3600
        )
        predicted_value = mean_y + trend_per_hour * (target_x - mean_x)

        forecasts.append({
            "astronaut_id": astronaut_id,
            "stream": stream,
            "stream_label": STREAMS[stream]["label"],
            "measurement": measurement,
            "unit": unit,
            "sample_count": len(points),
            "latest_timestamp": latest_timestamp.isoformat(),
            "forecast_timestamp": target_timestamp.isoformat(),
            "horizon_hours": horizon_hours,
            "effective_horizon_hours": effective_horizon_hours,
            "effective_horizon_minutes": effective_horizon_hours * 60,
            "horizon_capped": horizon_capped,
            "predicted_value": predicted_value,
            "trend_per_hour": trend_per_hour,
            "reason": None
        })

    return forecasts


def get_statistics():
    """Return statistics for eligible Health and Sim Lab records."""

    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT
                COUNT(*) AS total_measurements,
                COUNT(DISTINCT astronaut_id) AS astronauts_tracked,
                COUNT(DISTINCT measurement) AS measurement_types
            FROM health_measurements
            WHERE simulated = 0
               OR (simulated = 1 AND LOWER(TRIM(source)) = ?)
            """,
            (SIM_LAB_SOURCE,)
        ).fetchone()

    return dict(row)


def get_status():
    """Return Tracking Core availability and statistics."""

    try:
        return {
            "id": "tracking",
            "name": "Tracking",
            "status": "Operational",
            **get_statistics()
        }

    except Exception as error:
        return {
            "id": "tracking",
            "name": "Tracking",
            "status": "Error",
            "error": str(error)
        }
