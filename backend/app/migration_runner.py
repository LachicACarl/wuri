"""Transactional SQLite migration application.

Migration SQL is executed statement-by-statement so DDL and its history row
share one transaction. Migration 004 is the sole legacy table-rebuild migration
that must temporarily disable FK enforcement before BEGIN; its FK graph is
validated before the transaction is committed.
"""

import sqlite3


_FOREIGN_KEYS_OFF_MIGRATIONS = {
    "004_research_import_and_annotations.sql",
}


def _statements(script: str):
    """Yield complete SQL statements without splitting quoted semicolons."""
    pending = ""
    for line in script.splitlines(keepends=True):
        pending += line
        if sqlite3.complete_statement(pending):
            statement = pending.strip()
            if statement:
                yield statement
            pending = ""
    if pending.strip():
        raise ValueError("Migration contains an incomplete SQL statement.")


def apply_migration(
    connection: sqlite3.Connection,
    migration_name: str,
    script: str,
    *,
    disable_foreign_keys: bool = False,
) -> None:
    """Apply one migration and its history record as a single transaction."""
    if disable_foreign_keys != (migration_name in _FOREIGN_KEYS_OFF_MIGRATIONS):
        raise ValueError("Foreign-key mode does not match the migration policy.")
    if connection.in_transaction:
        raise RuntimeError("A migration cannot start inside another transaction.")

    if disable_foreign_keys:
        connection.execute("PRAGMA foreign_keys = OFF")

    try:
        connection.execute("BEGIN IMMEDIATE")
        for statement in _statements(script):
            connection.execute(statement)

        violations = connection.execute("PRAGMA foreign_key_check").fetchall()
        if violations:
            raise sqlite3.IntegrityError(
                f"Migration {migration_name} caused foreign-key violations."
            )

        connection.execute(
            "INSERT INTO schema_migrations (migration_name) VALUES (?)",
            (migration_name,),
        )
        connection.commit()
    except Exception:
        if connection.in_transaction:
            connection.rollback()
        raise
    finally:
        if disable_foreign_keys:
            connection.execute("PRAGMA foreign_keys = ON")
