
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
                rule_id TEXT PRIMARY KEY,
                measurement TEXT NOT NULL,
                minimum REAL,
                maximum REAL,
                severity TEXT NOT NULL,
                description TEXT,
                enabled INTEGER NOT NULL DEFAULT 1,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS health_default_rule_state (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                enabled INTEGER NOT NULL DEFAULT 0,
                rules_version INTEGER NOT NULL DEFAULT 3
            );

            INSERT OR IGNORE INTO health_default_rule_state (id, enabled)
            VALUES (1, 0);

            CREATE TABLE IF NOT EXISTS health_default_rule_backups (
                rule_id TEXT PRIMARY KEY,
                measurement TEXT NOT NULL,
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

        _migrate_health_monitoring_rules(connection)
        _migrate_health_default_rule_backups(connection)

        state_columns = {
            row["name"]
            for row in connection.execute(
                "PRAGMA table_info(health_default_rule_state)"
            ).fetchall()
        }

        if "rules_version" not in state_columns:
            connection.execute(
                """
                ALTER TABLE health_default_rule_state
                ADD COLUMN rules_version INTEGER NOT NULL DEFAULT 1
                """
            )

    return True


def _migrate_health_monitoring_rules(connection):
    """Give monitoring rules independent IDs while preserving existing rows."""

    columns = {
        row["name"]
        for row in connection.execute(
            "PRAGMA table_info(health_monitoring_rules)"
        ).fetchall()
    }

    if "rule_id" in columns:
        if "measurement" not in columns:
            connection.execute(
                """
                ALTER TABLE health_default_rule_backups
                ADD COLUMN measurement TEXT
                """
            )
            connection.execute(
                """
                UPDATE health_default_rule_backups
                SET measurement = COALESCE(
                    (
                        SELECT measurement
                        FROM health_monitoring_rules
                        WHERE health_monitoring_rules.rule_id =
                              health_default_rule_backups.rule_id
                    ),
                    rule_id
                )
                WHERE measurement IS NULL
                """
            )
        return

    connection.execute(
        "ALTER TABLE health_monitoring_rules "
        "RENAME TO health_monitoring_rules_legacy"
    )
    connection.execute(
        """
        CREATE TABLE health_monitoring_rules (
            rule_id TEXT PRIMARY KEY,
            measurement TEXT NOT NULL,
            minimum REAL,
            maximum REAL,
            severity TEXT NOT NULL,
            description TEXT,
            enabled INTEGER NOT NULL DEFAULT 1,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    connection.execute(
        """
        INSERT INTO health_monitoring_rules (
            rule_id, measurement, minimum, maximum, severity,
            description, enabled, updated_at
        )
        SELECT measurement, measurement, minimum, maximum, severity,
               description, enabled, updated_at
        FROM health_monitoring_rules_legacy
        """
    )
    connection.execute("DROP TABLE health_monitoring_rules_legacy")


def _migrate_health_default_rule_backups(connection):
    """Key saved custom rules by rule ID after the rules-table migration."""

    columns = {
        row["name"]
        for row in connection.execute(
            "PRAGMA table_info(health_default_rule_backups)"
        ).fetchall()
    }

    if "rule_id" in columns:
        return

    connection.execute(
        "ALTER TABLE health_default_rule_backups "
        "RENAME TO health_default_rule_backups_legacy"
    )
    connection.execute(
        """
        CREATE TABLE health_default_rule_backups (
            rule_id TEXT PRIMARY KEY,
            measurement TEXT NOT NULL,
            had_previous INTEGER NOT NULL,
            minimum REAL,
            maximum REAL,
            severity TEXT,
            description TEXT,
            enabled INTEGER,
            updated_at TEXT
        )
        """
    )
    connection.execute(
        """
        INSERT INTO health_default_rule_backups (
            rule_id, measurement, had_previous, minimum, maximum, severity,
            description, enabled, updated_at
        )
        SELECT measurement, measurement, had_previous, minimum, maximum, severity,
               description, enabled, updated_at
        FROM health_default_rule_backups_legacy
        """
    )
    connection.execute("DROP TABLE health_default_rule_backups_legacy")
