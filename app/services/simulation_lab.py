"""
AETHER — Simulation Lab

Runs one persistent astronaut simulation through Health and Radiation.
"""

import asyncio
import json
import math
import random
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from app.cores import astronaut, health
from app.database.connection import get_connection
from app.services import radiation


SIMULATION_ASTRONAUT_ID = "sim_lab_ast"
SIMULATION_ASTRONAUT_NAME = "Simulation Astronaut"
SIMULATION_SOURCE = "sim_lab"
MIN_SIMULATION_SPEED = 1
MAX_SIMULATION_SPEED = 10
SIMULATION_SPEEDS = tuple(
    range(MIN_SIMULATION_SPEED, MAX_SIMULATION_SPEED + 1)
)
HEALTH_UNITS = {
    "heart_rate": "bpm",
    "blood_oxygen": "%",
    "body_temperature": "°C",
    "respiratory_rate": "breaths/min",
    "systolic_blood_pressure": "mmHg",
    "diastolic_blood_pressure": "mmHg"
}
HEALTH_VARIATION = {
    "heart_rate": {
        "spread": 2.5,
        "minimum": 35,
        "maximum": 180,
        "low_excursion": 42,
        "high_excursion": 155
    },
    "blood_oxygen": {
        "spread": 0.8,
        "minimum": 70,
        "maximum": 100,
        "low_excursion": 77,
        "high_excursion": 100
    },
    "body_temperature": {
        "spread": 0.15,
        "minimum": 33,
        "maximum": 41,
        "low_excursion": 33.5,
        "high_excursion": 40.5
    },
    "respiratory_rate": {
        "spread": 1,
        "minimum": 3,
        "maximum": 35,
        "low_excursion": 3.5,
        "high_excursion": 32
    },
    "systolic_blood_pressure": {
        "spread": 3,
        "minimum": 65,
        "maximum": 190,
        "low_excursion": 68,
        "high_excursion": 185
    },
    "diastolic_blood_pressure": {
        "spread": 2,
        "minimum": 35,
        "maximum": 120,
        "low_excursion": 38,
        "high_excursion": 115
    }
}
HEALTH_START_RANGES = {
    "heart_rate": (1, 300),
    "blood_oxygen": (0, 100),
    "body_temperature": (20, 45),
    "respiratory_rate": (1, 100),
    "systolic_blood_pressure": (1, 350),
    "diastolic_blood_pressure": (1, 250)
}
SIMULATED_MINUTES_PER_MONTH = 30 * 24 * 60
DOSE_INCREASE_PER_SIX_MONTHS_MSV = 50
EXCURSION_PROBABILITY = 0.015

_background_task = None
_lifecycle_lock = asyncio.Lock()


def _now():
    return datetime.now(timezone.utc).isoformat()


def _get_state():
    with get_connection() as connection:
        row = connection.execute(
            "SELECT * FROM simulation_lab_state WHERE id = 1"
        ).fetchone()

    if row is None:
        raise RuntimeError("Simulation Lab state has not been initialized.")

    state = dict(row)
    state["running"] = bool(state["running"])
    state["baseline"] = (
        json.loads(state["baseline_json"])
        if state["baseline_json"] else {}
    )
    state["current"] = (
        json.loads(state["current_json"])
        if state["current_json"] else {}
    )
    return state


def get_simulation_status():
    """Return the persisted simulator status and latest generated values."""

    state = _get_state()
    abnormal_measurements = []
    for measurement, value in state["current"].items():
        evaluation = health.evaluate_measurement({
            "measurement": measurement,
            "value": value,
            "unit": HEALTH_UNITS[measurement]
        })
        if evaluation["abnormal"]:
            abnormal_measurements.append(measurement)

    radiation_severity = (
        radiation.get_severity(state["current_dose_msv"])
        if state["current_dose_msv"] is not None
        else None
    )

    return {
        "running": state["running"],
        "speed": state["speed"],
        "simulated_seconds_per_real_second": state["speed"],
        "retention": state["retention"],
        "baseline": state["baseline"],
        "current": state["current"],
        "abnormal_measurements": abnormal_measurements,
        "radiation_severity": radiation_severity,
        "current_dose_msv": state["current_dose_msv"],
        "started_at": state["started_at"],
        "simulation_time": state["simulation_time"],
        "session_id": state["session_id"],
        "last_error": state["last_error"],
        "astronaut_id": SIMULATION_ASTRONAUT_ID,
        "astronaut_name": SIMULATION_ASTRONAUT_NAME
    }


def get_simulation_page_data():
    """Return UI context for the Simulation Lab page."""

    simulation = get_simulation_status()
    initial_values = simulation["current"] or {
        "heart_rate": 80,
        "blood_oxygen": 98,
        "body_temperature": 36.8,
        "respiratory_rate": 16,
        "systolic_blood_pressure": 120,
        "diastolic_blood_pressure": 80
    }

    return {
        "page_title": "Simulation Lab",
        "page_description": (
            "Generate isolated simulated Health, Tracking, alert, and Radiation data."
        ),
        "core_status": "Running" if simulation["running"] else "Ready",
        "simulation": simulation,
        "initial_values": initial_values,
        "initial_dose_msv": simulation["current_dose_msv"] or 0,
        "health_units": HEALTH_UNITS,
        "simulation_speeds": SIMULATION_SPEEDS,
    }


def _validate_start_values(initial_values, dose_msv, speed, retention):
    if not isinstance(initial_values, dict):
        raise ValueError("Starting Health values are required.")

    if set(initial_values) != set(HEALTH_UNITS):
        raise ValueError("Provide a starting value for each Health measurement.")

    for measurement, value in initial_values.items():
        health.validate_measurement({
            "astronaut_id": SIMULATION_ASTRONAUT_ID,
            "measurement": measurement,
            "value": value,
            "unit": HEALTH_UNITS[measurement],
            "source": SIMULATION_SOURCE,
            "simulated": True
        })
        minimum, maximum = HEALTH_START_RANGES[measurement]
        if not minimum <= value <= maximum:
            raise ValueError(
                f"Starting {measurement.replace('_', ' ')} is outside "
                "the supported simulation input range."
            )

    radiation.project_dose(dose_msv, 0)

    if (
        isinstance(speed, bool)
        or not isinstance(speed, int)
        or speed not in SIMULATION_SPEEDS
    ):
        raise ValueError("Simulation speed must be an integer from 1x to 10x.")

    if retention not in {"retain", "clear"}:
        raise ValueError("Choose whether to retain or clear generated data.")


def _ensure_simulation_astronaut():
    existing = astronaut.get_astronaut(SIMULATION_ASTRONAUT_ID)

    if existing is None:
        try:
            astronaut.register_astronaut(
                SIMULATION_ASTRONAUT_ID,
                SIMULATION_ASTRONAUT_NAME,
                mission="Simulation"
            )
        except Exception:
            existing = astronaut.get_astronaut(SIMULATION_ASTRONAUT_ID)
            if existing is None:
                raise
    else:
        if existing["name"] != SIMULATION_ASTRONAUT_NAME:
            raise ValueError(
                f"Astronaut ID {SIMULATION_ASTRONAUT_ID} is already in use."
            )

    return astronaut.get_astronaut(SIMULATION_ASTRONAUT_ID)


def _record_health_values(values, timestamp, session_id):
    for measurement, value in values.items():
        result = health.process_measurement(
            {
                "astronaut_id": SIMULATION_ASTRONAUT_ID,
                "measurement": measurement,
                "value": value,
                "unit": HEALTH_UNITS[measurement],
                "source": SIMULATION_SOURCE,
                "simulated": True,
                "timestamp": timestamp,
                "simulation_session_id": session_id
            },
            update_existing=True,
            deduplicate_active_alerts=True
        )

        if result["alert_error"]:
            print(
                "SIMULATION HEALTH ALERT ERROR:",
                result["alert_error"]
            )


def _record_radiation_dose(
    dose_msv,
    timestamp,
    session_id,
    initial=False
):
    result = radiation.process_measurement(
        astronaut_id=SIMULATION_ASTRONAUT_ID,
        dose_msv=dose_msv,
        source=SIMULATION_SOURCE,
        notes="Simulation Lab starting dose" if initial else "",
        timestamp=timestamp,
        simulation_session_id=session_id
    )

    if result["alert_error"]:
        print("SIMULATION RADIATION ALERT ERROR:", result["alert_error"])


async def start_simulation(initial_values, dose_msv, speed, retention):
    """Start one simulation with required baselines and retention settings."""

    global _background_task

    _validate_start_values(initial_values, dose_msv, speed, retention)

    async with _lifecycle_lock:
        state = _get_state()

        if state["running"]:
            raise ValueError("A simulation is already running.")

        _ensure_simulation_astronaut()

        baselines = {
            measurement: float(value)
            for measurement, value in initial_values.items()
        }
        dose_msv = float(dose_msv)
        started_at = _now()
        session_id = uuid4().hex

        _record_health_values(
            baselines,
            timestamp=started_at,
            session_id=session_id
        )
        _record_radiation_dose(
            dose_msv,
            timestamp=started_at,
            session_id=session_id,
            initial=True
        )

        with get_connection() as connection:
            connection.execute(
                """
                UPDATE simulation_lab_state
                SET running = 1,
                    speed = ?,
                    retention = ?,
                    baseline_json = ?,
                    current_json = ?,
                    current_dose_msv = ?,
                    started_at = ?,
                    simulation_time = ?,
                    session_id = ?,
                    updated_at = CURRENT_TIMESTAMP,
                    last_error = NULL
                WHERE id = 1
                """,
                (
                    speed,
                    retention,
                    json.dumps(baselines),
                    json.dumps(baselines),
                    dose_msv,
                    started_at,
                    started_at,
                    session_id
                )
            )

        _background_task = asyncio.create_task(_run_simulation())

    return get_simulation_status()


async def set_simulation_speed(speed):
    """Change the speed used by the next one-second simulation tick."""

    if (
        isinstance(speed, bool)
        or not isinstance(speed, int)
        or speed not in SIMULATION_SPEEDS
    ):
        raise ValueError("Simulation speed must be an integer from 1x to 10x.")

    async with _lifecycle_lock:
        state = _get_state()
        if not state["running"]:
            raise RuntimeError("Simulation speed can only change while running.")

        with get_connection() as connection:
            connection.execute(
                """
                UPDATE simulation_lab_state
                SET speed = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = 1 AND running = 1
                """,
                (speed,)
            )

    return get_simulation_status()


def _next_health_values(
    baseline,
    current,
    rng=None,
    simulated_seconds=60
):
    """Move values toward their baselines with occasional abnormal excursions."""

    rng = rng or random
    values = {}
    simulated_minutes = simulated_seconds / 60
    excursion_probability = (
        1 - (1 - EXCURSION_PROBABILITY) ** simulated_minutes
    )
    reversion_factor = 1 - (1 - 0.25) ** simulated_minutes
    variation_scale = math.sqrt(simulated_minutes)

    for measurement, baseline_value in baseline.items():
        configuration = HEALTH_VARIATION[measurement]

        if rng.random() < excursion_probability:
            value = rng.choice((
                configuration["low_excursion"],
                configuration["high_excursion"]
            ))
        else:
            previous = current[measurement]
            value = (
                previous
                + (baseline_value - previous) * reversion_factor
                + rng.uniform(
                    -configuration["spread"] * variation_scale,
                    configuration["spread"] * variation_scale
                )
            )
            value = min(
                configuration["maximum"],
                max(configuration["minimum"], value)
            )

        values[measurement] = round(value, 2)

    return values


async def _run_simulation():
    """Persist Health and Radiation readings once per real-time second."""

    global _background_task

    try:
        while True:
            state = _get_state()
            if not state["running"]:
                return

            await asyncio.sleep(1)

            state = _get_state()
            if not state["running"]:
                return

            simulated_seconds = state["speed"]
            current = state["current"]
            baseline = state["baseline"]
            values = _next_health_values(
                baseline,
                current,
                simulated_seconds=simulated_seconds
            )
            simulation_time = (
                datetime.fromisoformat(state["simulation_time"])
                + timedelta(seconds=simulated_seconds)
            ).isoformat()
            dose_increment = (
                DOSE_INCREASE_PER_SIX_MONTHS_MSV
                * simulated_seconds
                / (6 * SIMULATED_MINUTES_PER_MONTH * 60)
            )
            dose_msv = state["current_dose_msv"] + dose_increment

            _record_health_values(
                values,
                timestamp=simulation_time,
                session_id=state["session_id"]
            )
            _record_radiation_dose(
                dose_msv,
                timestamp=simulation_time,
                session_id=state["session_id"]
            )

            with get_connection() as connection:
                connection.execute(
                    """
                    UPDATE simulation_lab_state
                    SET current_json = ?,
                        current_dose_msv = ?,
                        simulation_time = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = 1 AND running = 1
                    """,
                    (json.dumps(values), dose_msv, simulation_time)
                )
    except asyncio.CancelledError:
        raise
    except Exception as error:
        print("SIMULATION LAB BACKGROUND ERROR:", repr(error))
        with get_connection() as connection:
            connection.execute(
                """
                UPDATE simulation_lab_state
                SET running = 0,
                    last_error = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = 1
                """,
                (str(error),)
            )
    finally:
        if _background_task is asyncio.current_task():
            _background_task = None


def _clear_simulation_data(session_id):
    if not session_id:
        return

    with get_connection() as connection:
        connection.execute(
            """
            DELETE FROM alerts
            WHERE astronaut_id = ?
              AND instr(COALESCE(description, ''), ?) > 0
              AND (
                    (
                        source = 'health_simulation'
                    )
                    OR
                    (
                        source = 'radiation'
                    )
              )
            """,
            (
                SIMULATION_ASTRONAUT_ID,
                f"Simulation Session: {session_id}"
            )
        )
        connection.execute(
            """
            DELETE FROM health_measurements
            WHERE astronaut_id = ?
              AND simulated = 1
              AND source = ?
              AND simulation_session_id = ?
            """,
            (SIMULATION_ASTRONAUT_ID, SIMULATION_SOURCE, session_id)
        )
        connection.execute(
            """
            DELETE FROM radiation_measurements
            WHERE astronaut_id = ?
              AND source = ?
              AND simulation_session_id = ?
            """,
            (SIMULATION_ASTRONAUT_ID, SIMULATION_SOURCE, session_id)
        )


async def stop_simulation():
    """Stop generation and apply the retention policy selected at start."""

    global _background_task

    async with _lifecycle_lock:
        state = _get_state()

        if state["running"]:
            with get_connection() as connection:
                connection.execute(
                    """
                    UPDATE simulation_lab_state
                    SET running = 0, updated_at = CURRENT_TIMESTAMP
                    WHERE id = 1
                    """
                )

            task = _background_task
            if task is not None and not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

        if state["retention"] == "clear":
            _clear_simulation_data(state["session_id"])
            with get_connection() as connection:
                connection.execute(
                    """
                    UPDATE simulation_lab_state
                    SET current_json = baseline_json,
                        current_dose_msv = NULL,
                        started_at = NULL,
                        simulation_time = NULL,
                        session_id = NULL,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = 1
                    """
                )

    return get_simulation_status()


async def resume_simulation():
    """Resume a persisted running simulation after application startup."""

    global _background_task

    async with _lifecycle_lock:
        state = _get_state()
        if state["running"] and (
            _background_task is None or _background_task.done()
        ):
            _background_task = asyncio.create_task(_run_simulation())


async def shutdown_simulation():
    """Cancel the process-local task while preserving persisted run state."""

    global _background_task

    task = _background_task
    _background_task = None
    if task is not None and not task.done():
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass
