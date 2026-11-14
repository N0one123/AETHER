
"""
AETHER — Astronaut Core

Manages astronaut profiles using SQLite.
"""

from app.database.connection import get_connection


def register_astronaut(astronaut_id, name, mission=None):
    """Register a new astronaut."""

    if not astronaut_id or not name:
        raise ValueError("Astronaut ID and name are required.")

    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO astronauts (id, name, mission)
            VALUES (?, ?, ?)
            """,
            (astronaut_id, name, mission)
        )

    return get_astronaut(astronaut_id)


def get_astronaut(astronaut_id):
    """Retrieve an astronaut by ID."""

    with get_connection() as connection:
        row = connection.execute(
            "SELECT * FROM astronauts WHERE id = ?",
            (astronaut_id,)
        ).fetchone()

    return dict(row) if row else None


def get_all_astronauts():
    """Return all registered astronauts."""

    with get_connection() as connection:
        rows = connection.execute(
            "SELECT * FROM astronauts ORDER BY created_at"
        ).fetchall()

    return [dict(row) for row in rows]


def update_astronaut(astronaut_id, **updates):
    """Update an astronaut's profile."""

    allowed_fields = {"name", "mission", "status"}

    invalid_fields = set(updates) - allowed_fields

    if invalid_fields:
        raise ValueError(
            f"Cannot update fields: {', '.join(sorted(invalid_fields))}"
        )

    if not updates:
        return get_astronaut(astronaut_id)

    if "name" in updates and not updates["name"]:
        raise ValueError("Astronaut name cannot be empty.")

    fields = list(updates)
    assignments = ", ".join(
        f"{field} = ?" for field in fields
    )

    values = [updates[field] for field in fields]
    values.append(astronaut_id)

    with get_connection() as connection:
        cursor = connection.execute(
            f"UPDATE astronauts SET {assignments} WHERE id = ?",
            values
        )

        if cursor.rowcount == 0:
            raise ValueError(
                f"Astronaut '{astronaut_id}' was not found."
            )

    return get_astronaut(astronaut_id)


def remove_astronaut(astronaut_id):
    """Remove an astronaut from the registry."""

    with get_connection() as connection:
        cursor = connection.execute(
            "DELETE FROM astronauts WHERE id = ?",
            (astronaut_id,)
        )

    return cursor.rowcount > 0


def get_status():
    """Return the current Astronaut Core status."""

    try:
        with get_connection() as connection:
            count = connection.execute(
                "SELECT COUNT(*) FROM astronauts"
            ).fetchone()[0]

        return {
            "id": "astronaut",
            "name": "Astronaut",
            "status": "Operational",
            "records": count
        }

    except Exception:
        return {
            "id": "astronaut",
            "name": "Astronaut",
            "status": "Error",
            "records": None
        }
