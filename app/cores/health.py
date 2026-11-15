
"""
AETHER — Health Core

Receives, stores and monitors astronaut health measurements.

Supports:
- Real/manual measurements
- Synthetic demonstration measurements
- Configurable monitoring rules
- Automatic Emergency Response alerts

IMPORTANT:
This Core does not communicate with Tracking.
Synthetic measurements are stored separately from Tracking's
historical analysis workflow.
"""

from datetime import datetime, timezone
import math
from uuid import uuid4

from app.database.connection import get_connection
from app.cores import emergency_response


CORE_ID = "health"
CORE_NAME = "Health"

ALLOWED_SEVERITIES = {
    "low",
    "medium",
    "high",
    "critical"
}

DEFAULT_RULES_VERSION = 3

DEFAULT_SEVERITY_BANDS = {
    "heart_rate": {
        "label": "Heart rate",
        "unit": "bpm",
        "bands": {
            "medium": (60, 100),
            "high": (50, 130),
            "critical": (40, 150)
        }
    },
    "blood_oxygen": {
        "label": "Blood oxygen",
        "unit": "%",
        "bands": {
            "medium": (90, None),
            "high": (85, None),
            "critical": (80, None)
        }
    },
    "body_temperature": {
        "label": "Body temperature",
        "unit": "°C",
        "bands": {
            "medium": (35, 38),
            "high": (34, 39),
            "critical": (32, 40)
        }
    },
    "respiratory_rate": {
        "label": "Respiratory rate",
        "unit": "breaths/min",
        "bands": {
            "medium": (8, 20),
            "high": (6, 25),
            "critical": (4, 30)
        }
    },
    "systolic_blood_pressure": {
        "label": "Systolic blood pressure",
        "unit": "mmHg",
        "bands": {
            "medium": (90, 140),
            "high": (80, 160),
            "critical": (70, 180)
        }
    },
    "diastolic_blood_pressure": {
        "label": "Diastolic blood pressure",
        "unit": "mmHg",
        "bands": {
            "medium": (60, 90),
            "high": (50, 100),
            "critical": (40, 110)
        }
    }
}


def _build_default_monitoring_rules():
    """Build one independent configurable default rule per severity band."""

    rules = []

    for measurement, configuration in DEFAULT_SEVERITY_BANDS.items():
        for severity, (minimum, maximum) in configuration["bands"].items():
            boundaries = []

            if minimum is not None:
                boundaries.append(f"below {minimum}")
            if maximum is not None:
                boundaries.append(f"above {maximum}")

            rules.append({
                "rule_id": (
                    measurement
                    if severity == "medium"
                    else f"{measurement}_{severity}"
                ),
                "measurement": measurement,
                "minimum": minimum,
                "maximum": maximum,
                "severity": severity,
                "description": (
                    f"{severity.title()} alert for "
                    f"{configuration['label'].lower()} "
                    f"{' or '.join(boundaries)} "
                    f"{configuration['unit']}. These example thresholds "
                    "should be confirmed against mission medical protocols."
                )
            })

    return tuple(rules)


DEFAULT_MONITORING_RULES = _build_default_monitoring_rules()


# ---------------------------------------------------------
# TIME
# ---------------------------------------------------------

def get_current_timestamp():
    """Return the current UTC timestamp."""

    return datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------
# VALIDATION
# ---------------------------------------------------------

def validate_measurement(record):
    """Validate an incoming health measurement."""

    if not isinstance(record, dict):
        raise ValueError("Measurement must be a dictionary.")

    required_fields = {
        "astronaut_id",
        "measurement",
        "value",
        "unit",
        "source"
    }

    missing = required_fields - record.keys()

    if missing:
        raise ValueError(
            f"Missing fields: {', '.join(sorted(missing))}"
        )

    astronaut_id = record["astronaut_id"]
    measurement = record["measurement"]
    value = record["value"]
    unit = record["unit"]
    source = record["source"]

    if not isinstance(astronaut_id, str) or not astronaut_id.strip():
        raise ValueError("A valid astronaut ID is required.")

    if not isinstance(measurement, str) or not measurement.strip():
        raise ValueError("Measurement name cannot be empty.")

    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise ValueError("Measurement value must be numeric.")

    if not math.isfinite(value):
        raise ValueError("Measurement value must be finite.")

    if not isinstance(unit, str) or not unit.strip():
        raise ValueError("Measurement unit cannot be empty.")

    if not isinstance(source, str) or not source.strip():
        raise ValueError("Measurement source cannot be empty.")

    simulated = record.get("simulated", False)

    if not isinstance(simulated, bool):
        raise ValueError("Simulated must be True or False.")

    timestamp = record.get(
        "timestamp",
        get_current_timestamp()
    )

    if not isinstance(timestamp, str) or not timestamp.strip():
        raise ValueError("A valid timestamp is required.")

    try:
        datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    except ValueError:
        raise ValueError("Timestamp must be valid ISO 8601.")

    return {
        "astronaut_id": astronaut_id.strip(),
        "measurement": measurement.strip().lower(),
        "value": float(value),
        "unit": unit.strip(),
        "source": source.strip(),
        "simulated": simulated,
        "timestamp": timestamp
    }


# ---------------------------------------------------------
# MONITORING RULES
# ---------------------------------------------------------

def configure_monitoring_rule(
    measurement,
    severity,
    minimum=None,
    maximum=None,
    description="",
    rule_id=None
):
    """Create a rule or update one independently identified rule."""

    if not isinstance(measurement, str) or not measurement.strip():
        raise ValueError("Measurement name is required.")

    normalized_measurement = measurement.strip().lower()

    if rule_id is not None:
        if not isinstance(rule_id, str) or not rule_id.strip():
            raise ValueError("Rule ID is required.")
        rule_id = rule_id.strip()

    if severity not in ALLOWED_SEVERITIES:
        raise ValueError("Invalid severity.")

    if minimum is not None:
        if (
            not isinstance(minimum, (int, float))
            or isinstance(minimum, bool)
            or not math.isfinite(minimum)
        ):
            raise ValueError("Minimum must be a finite number.")

    if maximum is not None:
        if (
            not isinstance(maximum, (int, float))
            or isinstance(maximum, bool)
            or not math.isfinite(maximum)
        ):
            raise ValueError("Maximum must be a finite number.")

    if minimum is None and maximum is None:
        raise ValueError("At least one boundary is required.")

    if minimum is not None and maximum is not None:
        if minimum >= maximum:
            raise ValueError("Minimum must be below maximum.")

    rule_id = rule_id or uuid4().hex

    with get_connection() as connection:
        connection.execute(
            """
            DELETE FROM health_default_rule_backups
            WHERE rule_id = ?
            """,
            (rule_id,)
        )
        connection.execute(
            """
            INSERT INTO health_monitoring_rules (
                rule_id,
                measurement,
                minimum,
                maximum,
                severity,
                description,
                enabled,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, 1, CURRENT_TIMESTAMP)

            ON CONFLICT(rule_id)
            DO UPDATE SET
                measurement = excluded.measurement,
                minimum = excluded.minimum,
                maximum = excluded.maximum,
                severity = excluded.severity,
                description = excluded.description,
                enabled = 1,
                updated_at = CURRENT_TIMESTAMP
            """,
            (
                rule_id,
                normalized_measurement,
                minimum,
                maximum,
                severity,
                description
            )
        )

    return get_monitoring_rule(rule_id)


def get_monitoring_rule(rule_id):
    """Retrieve one monitoring rule."""

    if not isinstance(rule_id, str) or not rule_id.strip():
        raise ValueError("Rule ID is required.")

    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT r.*,
                   (b.rule_id IS NOT NULL) AS is_default
            FROM health_monitoring_rules AS r
            LEFT JOIN health_default_rule_backups AS b
                ON b.rule_id = r.rule_id
            WHERE r.rule_id = ?
            """,
            (rule_id.strip(),)
        ).fetchone()

    if row is None:
        return None

    result = dict(row)
    result["enabled"] = bool(result["enabled"])
    result["is_default"] = bool(result["is_default"])

    return result


def get_monitoring_rules(measurement=None):
    """Retrieve all monitoring rules."""

    _ensure_default_monitoring_rules_current()

    with get_connection() as connection:
        query = """
            SELECT r.*, (b.rule_id IS NOT NULL) AS is_default
            FROM health_monitoring_rules AS r
            LEFT JOIN health_default_rule_backups AS b
                ON b.rule_id = r.rule_id
        """
        parameters = ()

        if measurement is not None:
            if not isinstance(measurement, str) or not measurement.strip():
                raise ValueError("Measurement name is required.")
            query += " WHERE r.measurement = ?"
            parameters = (measurement.strip().lower(),)

        query += " ORDER BY r.measurement, r.severity, r.rule_id"
        rows = connection.execute(query, parameters).fetchall()

    results = []

    for row in rows:
        item = dict(row)
        item["enabled"] = bool(item["enabled"])
        item["is_default"] = bool(item["is_default"])
        results.append(item)

    return results


def remove_monitoring_rule(rule_id):
    """Remove a monitoring rule."""

    if not isinstance(rule_id, str) or not rule_id.strip():
        raise ValueError("Rule ID is required.")

    with get_connection() as connection:
        cursor = connection.execute(
            """
            DELETE FROM health_monitoring_rules
            WHERE rule_id = ?
            """,
            (rule_id.strip(),)
        )
        connection.execute(
            """
            DELETE FROM health_default_rule_backups
            WHERE rule_id = ?
            """,
            (rule_id.strip(),)
        )

    return cursor.rowcount > 0


def get_default_monitoring_rules_enabled():
    """Return whether the configurable default rule set is enabled."""

    _ensure_default_monitoring_rules_current()

    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT enabled
            FROM health_default_rule_state
            WHERE id = 1
            """
        ).fetchone()

    return bool(row["enabled"]) if row else False


def _apply_default_monitoring_rules(connection):
    """Back up pre-existing rules and apply each default rule by its own ID."""

    for rule in DEFAULT_MONITORING_RULES:
        backup = connection.execute(
            """
            SELECT rule_id
            FROM health_default_rule_backups
            WHERE rule_id = ?
            """,
            (rule["rule_id"],)
        ).fetchone()

        if backup is None:
            previous = connection.execute(
                """
                SELECT measurement, minimum, maximum, severity, description,
                       enabled, updated_at
                FROM health_monitoring_rules
                WHERE rule_id = ?
                """,
                (rule["rule_id"],)
            ).fetchone()

            if previous:
                connection.execute(
                    """
                    INSERT INTO health_default_rule_backups (
                        rule_id, measurement, had_previous,
                        minimum, maximum, severity,
                        description, enabled, updated_at
                    )
                    VALUES (?, ?, 1, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        rule["rule_id"],
                        previous["measurement"],
                        previous["minimum"],
                        previous["maximum"],
                        previous["severity"],
                        previous["description"],
                        previous["enabled"],
                        previous["updated_at"]
                    )
                )
            else:
                connection.execute(
                    """
                    INSERT INTO health_default_rule_backups (
                        rule_id, measurement, had_previous
                    )
                    VALUES (?, ?, 0)
                    """,
                    (rule["rule_id"], rule["measurement"])
                )

        connection.execute(
            """
            INSERT INTO health_monitoring_rules (
                rule_id, measurement, minimum, maximum, severity,
                description, enabled, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, 1, CURRENT_TIMESTAMP)
            ON CONFLICT(rule_id)
            DO UPDATE SET
                measurement = excluded.measurement,
                minimum = excluded.minimum,
                maximum = excluded.maximum,
                severity = excluded.severity,
                description = excluded.description,
                enabled = 1,
                updated_at = CURRENT_TIMESTAMP
            """,
            (
                rule["rule_id"],
                rule["measurement"],
                rule["minimum"],
                rule["maximum"],
                rule["severity"],
                rule["description"]
            )
        )


def _ensure_default_monitoring_rules_current():
    """Upgrade an already-enabled default set once when its definitions change."""

    with get_connection() as connection:
        state = connection.execute(
            """
            SELECT enabled, rules_version
            FROM health_default_rule_state
            WHERE id = 1
            """
        ).fetchone()

        if state is None or not state["enabled"]:
            return

        if state["rules_version"] >= DEFAULT_RULES_VERSION:
            return

        _apply_default_monitoring_rules(connection)
        connection.execute(
            """
            UPDATE health_default_rule_state
            SET rules_version = ?
            WHERE id = 1
            """,
            (DEFAULT_RULES_VERSION,)
        )


def set_default_monitoring_rules_enabled(enabled):
    """Enable or remove only rules managed by the default rule set."""

    if not isinstance(enabled, bool):
        raise ValueError("Enabled must be True or False.")

    with get_connection() as connection:
        current = connection.execute(
            """
            SELECT enabled, rules_version
            FROM health_default_rule_state
            WHERE id = 1
            """
        ).fetchone()

        if current is None:
            raise RuntimeError("Default monitoring rule state is not initialized.")

        if bool(current["enabled"]) == enabled:
            if enabled and current["rules_version"] < DEFAULT_RULES_VERSION:
                _apply_default_monitoring_rules(connection)
                connection.execute(
                    """
                    UPDATE health_default_rule_state
                    SET rules_version = ?
                    WHERE id = 1
                    """,
                    (DEFAULT_RULES_VERSION,)
                )
            return bool(enabled)

        if enabled:
            _apply_default_monitoring_rules(connection)
        else:
            backups = connection.execute(
                """
                SELECT *
                FROM health_default_rule_backups
                """
            ).fetchall()

            for backup in backups:
                connection.execute(
                    """
                    DELETE FROM health_monitoring_rules
                    WHERE rule_id = ?
                    """,
                    (backup["rule_id"],)
                )

                if backup["had_previous"]:
                    connection.execute(
                        """
                        INSERT INTO health_monitoring_rules (
                            rule_id, measurement, minimum, maximum, severity,
                            description, enabled, updated_at
                        )
                        VALUES (?, ?, ?, ?, ?, ?, ?, COALESCE(?, CURRENT_TIMESTAMP))
                        """,
                        (
                            backup["rule_id"],
                            backup["measurement"],
                            backup["minimum"],
                            backup["maximum"],
                            backup["severity"],
                            backup["description"],
                            backup["enabled"],
                            backup["updated_at"]
                        )
                    )

            connection.execute("DELETE FROM health_default_rule_backups")

        connection.execute(
            """
            UPDATE health_default_rule_state
            SET enabled = ?, rules_version = ?
            WHERE id = 1
            """,
            (int(enabled), DEFAULT_RULES_VERSION)
        )

    return enabled


# ---------------------------------------------------------
# MEASUREMENT STORAGE
# ---------------------------------------------------------

def record_measurement(record):
    """Validate and store a health measurement."""

    measurement = validate_measurement(record)

    with get_connection() as connection:

        astronaut = connection.execute(
            """
            SELECT id
            FROM astronauts
            WHERE id = ?
            """,
            (measurement["astronaut_id"],)
        ).fetchone()

        if astronaut is None:
            raise ValueError("Astronaut does not exist.")

        cursor = connection.execute(
            """
            INSERT INTO health_measurements (
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
                measurement["astronaut_id"],
                measurement["measurement"],
                measurement["value"],
                measurement["unit"],
                measurement["source"],
                int(measurement["simulated"]),
                measurement["timestamp"]
            )
        )

        measurement_id = cursor.lastrowid

    return {
        "id": measurement_id,
        **measurement
    }


def get_measurements(
    astronaut_id=None,
    measurement=None,
    simulated=None,
    limit=None
):
    """Retrieve Health measurements with optional filters."""

    if astronaut_id is not None:
        if not isinstance(astronaut_id, str) or not astronaut_id.strip():
            raise ValueError("Invalid astronaut ID.")

    if measurement is not None:
        if not isinstance(measurement, str) or not measurement.strip():
            raise ValueError("Invalid measurement name.")

    if simulated is not None and not isinstance(simulated, bool):
        raise ValueError("Simulated filter must be True or False.")

    if limit is not None:
        if isinstance(limit, bool) or not isinstance(limit, int) or limit < 1:
            raise ValueError("Limit must be a positive integer.")

    query = """
        SELECT *
        FROM health_measurements
        WHERE 1 = 1
    """

    parameters = []

    if astronaut_id is not None:
        query += " AND astronaut_id = ?"
        parameters.append(astronaut_id.strip())

    if measurement is not None:
        query += " AND measurement = ?"
        parameters.append(measurement.strip().lower())

    if simulated is not None:
        query += " AND simulated = ?"
        parameters.append(int(simulated))

    query += " ORDER BY timestamp DESC, id DESC"

    if limit is not None:
        query += " LIMIT ?"
        parameters.append(limit)

    with get_connection() as connection:
        rows = connection.execute(
            query,
            parameters
        ).fetchall()

    results = []

    for row in rows:
        item = dict(row)
        item["simulated"] = bool(item["simulated"])
        results.append(item)

    return results


def get_latest_measurement(astronaut_id, measurement):
    """Retrieve the latest measurement for an astronaut."""

    results = get_measurements(
        astronaut_id=astronaut_id,
        measurement=measurement,
        limit=1
    )

    return results[0] if results else None


# ---------------------------------------------------------
# MEASUREMENT EVALUATION
# ---------------------------------------------------------

def evaluate_measurement(record):
    """Compare a measurement against its configured rule."""

    measurement = record["measurement"]
    value = record["value"]
    rules = [
        rule
        for rule in get_monitoring_rules(measurement)
        if rule["enabled"]
    ]

    if not rules:
        return {
            "monitored": False,
            "abnormal": False,
            "reason": "No active monitoring rule."
        }

    triggered_rules = []

    for rule in rules:
        below_minimum = (
            rule["minimum"] is not None
            and value < rule["minimum"]
        )
        above_maximum = (
            rule["maximum"] is not None
            and value > rule["maximum"]
        )

        if below_minimum or above_maximum:
            triggered_rules.append((rule, below_minimum))

    if triggered_rules:
        severity_order = {
            severity: index
            for index, severity in enumerate(
                ("low", "medium", "high", "critical")
            )
        }
        selected_rule, below_minimum = max(
            triggered_rules,
            key=lambda entry: severity_order[entry[0]["severity"]]
        )
        boundary_value = (
            selected_rule["minimum"]
            if below_minimum
            else selected_rule["maximum"]
        )
        direction = "below" if below_minimum else "above"
        unit = record.get("unit", "")
        reason = (
            f"Measurement is {direction} the configured boundary "
            f"({boundary_value} {unit}); triggering a "
            f"{selected_rule['severity']} alert."
        )
        selected_severity = selected_rule["severity"]
        description = selected_rule["description"]
        abnormal = True
    else:
        reason = "Measurement is within configured boundaries."
        selected_severity = None
        description = rules[0]["description"]
        abnormal = False

    return {
        "monitored": True,
        "abnormal": abnormal,
        "severity": selected_severity,
        "description": description,
        "reason": reason
    }


# ---------------------------------------------------------
# EMERGENCY RESPONSE
# ---------------------------------------------------------

def trigger_emergency_response(record, evaluation):
    """Create an incident for each abnormal Health measurement."""

    if not evaluation["abnormal"]:
        return None

    simulated = record["simulated"]

    label = "[SIMULATED] " if simulated else ""

    title = (
        f"{label}{record['measurement'].replace('_', ' ').title()} "
        f"outside configured range"
    )

    source = (
        "health_simulation"
        if simulated
        else "health"
    )

    description = (
        f"Measurement: {record['measurement']}\n"
        f"Value: {record['value']} {record['unit']}\n"
        f"Timestamp: {record['timestamp']}\n"
        f"Source: {record['source']}\n"
        f"Simulated: {simulated}\n"
        f"Reason: {evaluation['reason']}\n"
        f"Details: {evaluation.get('description') or 'No additional details.'}"
    )

    alert = emergency_response.create_alert(
        astronaut_id=record["astronaut_id"],
        title=title,
        description=description,
        severity=evaluation["severity"],
        source=source
    )

    return {
        "created": True,
        "duplicate": False,
        "alert_id": alert["id"]
    }


def resolve_health_alerts_for_measurement(record):
    """Resolve matching Health alerts when a monitored value returns in range."""

    simulated = record["simulated"]
    title = (
        f"{'[SIMULATED] ' if simulated else ''}"
        f"{record['measurement'].replace('_', ' ').title()} "
        "outside configured range"
    )
    alert_source = "health_simulation" if simulated else "health"

    return emergency_response.resolve_matching_health_alerts(
        astronaut_id=record["astronaut_id"],
        title=title,
        alert_source=alert_source,
        measurement_source=record["source"]
    )


# ---------------------------------------------------------
# COMPLETE MEASUREMENT PROCESSING
# ---------------------------------------------------------

def process_measurement(record):
    """
    Store, evaluate and process one health measurement.

    This function does not call Tracking.
    """

    stored = record_measurement(record)

    evaluation = evaluate_measurement(stored)

    alert = None
    alert_error = None
    resolved_alerts = 0

    if evaluation["abnormal"]:
        try:
            alert = trigger_emergency_response(
                stored,
                evaluation
            )

        except Exception as error:
            # The measurement is already stored.
            # Report the alert failure rather than silently
            # pretending that the alert was created.
            alert_error = str(error)

    elif evaluation["monitored"]:
        try:
            resolved_alerts = resolve_health_alerts_for_measurement(stored)

        except Exception as error:
            alert_error = str(error)

    return {
        "measurement": stored,
        "evaluation": evaluation,
        "alert": alert,
        "resolved_alerts": resolved_alerts,
        "alert_error": alert_error
    }


# ---------------------------------------------------------
# STATISTICS
# ---------------------------------------------------------

def get_statistics():
    """Return Health Core statistics."""

    _ensure_default_monitoring_rules_current()

    with get_connection() as connection:

        row = connection.execute(
            """
            SELECT
                COUNT(*) AS total_measurements,
                COUNT(DISTINCT astronaut_id) AS astronauts_monitored,
                COUNT(DISTINCT measurement) AS measurement_types,

                SUM(CASE WHEN simulated = 1
                    THEN 1 ELSE 0 END) AS simulated_measurements,

                SUM(CASE WHEN simulated = 0
                    THEN 1 ELSE 0 END) AS non_simulated_measurements

            FROM health_measurements
            """
        ).fetchone()

        abnormal = connection.execute(
            """
            SELECT COUNT(DISTINCT m.id)
            FROM health_measurements AS m
            JOIN health_monitoring_rules AS r
                ON r.measurement = m.measurement
            WHERE r.enabled = 1
              AND (
                    (r.minimum IS NOT NULL AND m.value < r.minimum)
                    OR
                    (r.maximum IS NOT NULL AND m.value > r.maximum)
              )
            """
        ).fetchone()[0]

    return {
        key: value or 0
        for key, value in dict(row).items()
    } | {
        "abnormal_measurements": abnormal or 0
    }

# ---------------------------------------------------------
# CORE STATUS
# ---------------------------------------------------------

def get_status():
    """Return Health Core operational status."""

    try:
        statistics = get_statistics()

        return {
            "id": CORE_ID,
            "name": CORE_NAME,
            "status": "Operational",
            **statistics
        }

    except Exception as error:
        return {
            "id": CORE_ID,
            "name": CORE_NAME,
            "status": "Error",
            "error": str(error)
        }
