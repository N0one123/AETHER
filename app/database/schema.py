
"""
AETHER — Database Schema

Central database structure for AETHER.
"""

from app.database.connection import get_connection


def initialise_database():
    """Create all AETHER database tables if they do not exist."""

    with get_connection() as connection:

        connection.executescript("""

            CREATE TABLE IF NOT EXISTS astronauts (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                mission TEXT,
                status TEXT NOT NULL DEFAULT 'Registered',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS measurements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                astronaut_id TEXT NOT NULL,
                measurement TEXT NOT NULL,
                value REAL NOT NULL,
                unit TEXT NOT NULL,
                source TEXT NOT NULL,
                simulated INTEGER NOT NULL DEFAULT 0,
                timestamp TEXT NOT NULL,

                FOREIGN KEY (astronaut_id)
                    REFERENCES astronauts(id)
                    ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS health_measurements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                astronaut_id TEXT NOT NULL,
                measurement TEXT NOT NULL,
                value REAL NOT NULL,
                unit TEXT NOT NULL,
                source TEXT NOT NULL,
                simulated INTEGER NOT NULL DEFAULT 0,
                timestamp TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (astronaut_id)
                    REFERENCES astronauts(id)
                    ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS health_monitoring_rules (
                measurement TEXT PRIMARY KEY,
                minimum REAL,
                maximum REAL,
                severity TEXT NOT NULL,
                description TEXT,
                enabled INTEGER NOT NULL DEFAULT 1,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS health_default_rule_state (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                enabled INTEGER NOT NULL DEFAULT 0
            );

            INSERT OR IGNORE INTO health_default_rule_state (id, enabled)
            VALUES (1, 0);

            CREATE TABLE IF NOT EXISTS health_default_rule_backups (
                measurement TEXT PRIMARY KEY,
                had_previous INTEGER NOT NULL,
                minimum REAL,
                maximum REAL,
                severity TEXT,
                description TEXT,
                enabled INTEGER,
                updated_at TEXT
            );

            CREATE TABLE IF NOT EXISTS analyses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                astronaut_id TEXT NOT NULL,
                analysis_type TEXT NOT NULL,
                results TEXT NOT NULL,
                timestamp TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (astronaut_id)
                    REFERENCES astronauts(id)
                    ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS alerts (
                id TEXT PRIMARY KEY,
                astronaut_id TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT,
                severity TEXT NOT NULL,
                source TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'Active',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                resolved_at TEXT,

                FOREIGN KEY (astronaut_id)
                    REFERENCES astronauts(id)
                    ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_name TEXT NOT NULL,
                payload TEXT,
                timestamp TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS system_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                core TEXT NOT NULL,
                level TEXT NOT NULL,
                message TEXT NOT NULL,
                timestamp TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS evaluation_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                astronaut_id TEXT,
                measurement TEXT,
                value REAL,
                unit TEXT,
                source TEXT,
                timestamp TEXT,
                valid INTEGER NOT NULL,
                reason TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE INDEX IF NOT EXISTS idx_measurements_astronaut
                ON measurements(astronaut_id);

            CREATE INDEX IF NOT EXISTS idx_measurements_timestamp
                ON measurements(timestamp);

            CREATE INDEX IF NOT EXISTS idx_health_astronaut
                ON health_measurements(astronaut_id);

            CREATE INDEX IF NOT EXISTS idx_health_timestamp
                ON health_measurements(timestamp);

            CREATE INDEX IF NOT EXISTS idx_health_simulated
                ON health_measurements(simulated);

            CREATE INDEX IF NOT EXISTS idx_alerts_status
                ON alerts(status);

            CREATE INDEX IF NOT EXISTS idx_events_name
                ON events(event_name);

        """)

    return True
