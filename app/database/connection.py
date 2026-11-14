
"""
AETHER — Database Connection Manager

Provides isolated SQLite connections for AETHER components.
"""

import sqlite3
from contextlib import contextmanager
from pathlib import Path


# Store the database in the main AETHER project folder.
DATABASE_PATH = Path(__file__).resolve().parents[2] / "aether.db"


@contextmanager
def get_connection():
    """Provide a database connection with automatic cleanup."""

    connection = None

    try:
        connection = sqlite3.connect(
            DATABASE_PATH,
            timeout=10
        )

        connection.row_factory = sqlite3.Row

        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA busy_timeout = 10000")

        # Automatically commit successful operations
        # and roll back operations that raise exceptions.
        with connection:
            yield connection

    finally:
        if connection is not None:
            connection.close()


def get_database_path():
    """Return the database file location."""

    return str(DATABASE_PATH)
