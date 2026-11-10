import sqlite3
import unittest

from app.migration_runner import apply_migration


class MigrationRunnerTests(unittest.TestCase):
    def setUp(self):
        self.connection = sqlite3.connect(":memory:")
        self.connection.execute("PRAGMA foreign_keys = ON")
        self.connection.execute(
            "CREATE TABLE schema_migrations (migration_name TEXT PRIMARY KEY)"
        )

    def tearDown(self):
        self.connection.close()


    def test_all_repository_migrations_apply_in_order(self):
        from pathlib import Path

        migration_root = Path(__file__).resolve().parents[1] / "migrations"
        migrations = sorted(migration_root.glob("[0-9][0-9][0-9]_*.sql"))
        self.assertEqual(len(migrations), 12)

        connection = sqlite3.connect(":memory:")
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute(
            """CREATE TABLE schema_migrations (
                migration_name TEXT PRIMARY KEY,
                applied_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )"""
        )
        try:
            for migration in migrations:
                apply_migration(
                    connection,
                    migration.name,
                    migration.read_text(encoding="utf-8"),
                    disable_foreign_keys=(
                        migration.name == "004_research_import_and_annotations.sql"
                    ),
                )

            applied = [
                row["migration_name"]
                for row in connection.execute(
                    "SELECT migration_name FROM schema_migrations ORDER BY migration_name"
                )
            ]
            self.assertEqual(applied, [migration.name for migration in migrations])
            self.assertEqual(connection.execute("PRAGMA foreign_keys").fetchone()[0], 1)
            self.assertEqual(connection.execute("PRAGMA foreign_key_check").fetchall(), [])
        finally:
            connection.close()



    def test_database_initializer_records_migration_010_on_disposable_database(self):
        import tempfile
        from pathlib import Path
        from app.database import Database

        with tempfile.TemporaryDirectory() as directory:
            database_path = Path(directory) / "migration-integration.sqlite3"
            database = Database(database_path)
            with database.connection() as connection:
                self.assertIsNotNone(
                    connection.execute(
                        "SELECT 1 FROM sqlite_master WHERE type='table' "
                        "AND name='storage_cleanup_queue'"
                    ).fetchone()
                )
                self.assertIsNotNone(
                    connection.execute(
                        "SELECT 1 FROM schema_migrations "
                        "WHERE migration_name = ?",
                        ("010_storage_cleanup_queue.sql",),
                    ).fetchone()
                )
                self.assertEqual(
                    connection.execute("PRAGMA foreign_key_check").fetchall(), []
                )
                self.assertEqual(
                    connection.execute("PRAGMA foreign_keys").fetchone()[0], 1
                )

    def test_migration_011_adds_cleanup_retry_columns_and_failed_status(self):
        import tempfile
        from pathlib import Path
        from app.database import Database

        with tempfile.TemporaryDirectory() as directory:
            database = Database(Path(directory) / "migration-011.sqlite3")
            with database.connection() as connection:
                columns = {
                    row["name"] for row in connection.execute(
                        "PRAGMA table_info(storage_cleanup_queue)"
                    )
                }
                self.assertTrue({
                    "next_attempt_at", "last_error_at", "failed_at"
                }.issubset(columns))
                migration = connection.execute(
                    "SELECT 1 FROM schema_migrations WHERE migration_name = ?",
                    ("011_storage_cleanup_backoff.sql",),
                ).fetchone()
                self.assertIsNotNone(migration)
                self.assertEqual(connection.execute("PRAGMA foreign_key_check").fetchall(), [])

    def test_failed_migration_restores_foreign_keys_and_can_restart(self):
        self.connection.execute("CREATE TABLE parent (id TEXT PRIMARY KEY)")
        self.connection.execute(
            "CREATE TABLE child (parent_id TEXT REFERENCES parent(id))"
        )
        self.connection.commit()

        with self.assertRaises(sqlite3.OperationalError):
            apply_migration(
                self.connection,
                "004_research_import_and_annotations.sql",
                "CREATE TABLE temporary_rebuild (id TEXT);\n"
                "INSERT INTO missing_table VALUES (1);\n",
                disable_foreign_keys=True,
            )

        self.assertEqual(
            self.connection.execute("PRAGMA foreign_keys").fetchone()[0], 1
        )
        self.assertIsNone(
            self.connection.execute(
                "SELECT 1 FROM schema_migrations WHERE migration_name = ?",
                ("004_research_import_and_annotations.sql",),
            ).fetchone()
        )
        self.assertIsNone(
            self.connection.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name='temporary_rebuild'"
            ).fetchone()
        )

        apply_migration(
            self.connection,
            "004_research_import_and_annotations.sql",
            "CREATE TABLE temporary_rebuild (id TEXT);\n",
            disable_foreign_keys=True,
        )
        self.assertEqual(
            self.connection.execute("PRAGMA foreign_keys").fetchone()[0], 1
        )
        self.assertIsNotNone(
            self.connection.execute(
                "SELECT 1 FROM schema_migrations WHERE migration_name = ?",
                ("004_research_import_and_annotations.sql",),
            ).fetchone()
        )

    def test_failed_migration_rolls_back_ddl_and_history_for_safe_retry(self):
        self.connection.execute("CREATE TABLE sample (id INTEGER PRIMARY KEY)")
        with self.assertRaises(sqlite3.OperationalError):
            apply_migration(
                self.connection,
                "005_five_expert_panel.sql",
                "ALTER TABLE sample ADD COLUMN review_status TEXT;\n"
                "INSERT INTO missing_table VALUES (1);\n",
            )

        columns = {
            row[1]
            for row in self.connection.execute("PRAGMA table_info(sample)")
        }
        self.assertNotIn("review_status", columns)
        self.assertIsNone(
            self.connection.execute(
                "SELECT 1 FROM schema_migrations WHERE migration_name = ?",
                ("005_five_expert_panel.sql",),
            ).fetchone()
        )

        apply_migration(
            self.connection,
            "005_five_expert_panel.sql",
            "ALTER TABLE sample ADD COLUMN review_status TEXT;\n",
        )
        self.assertIn(
            "review_status",
            {
                row[1]
                for row in self.connection.execute("PRAGMA table_info(sample)")
            },
        )
        self.assertIsNotNone(
            self.connection.execute(
                "SELECT 1 FROM schema_migrations WHERE migration_name = ?",
                ("005_five_expert_panel.sql",),
            ).fetchone()
        )

    def test_migration_004_rebuild_preserves_composite_foreign_key(self):
        self.connection.executescript(
            """
            CREATE TABLE research_datasets (id TEXT PRIMARY KEY);
            CREATE TABLE research_examples (
                id TEXT PRIMARY KEY,
                dataset_id TEXT NOT NULL REFERENCES research_datasets(id),
                example_id TEXT NOT NULL,
                label TEXT NOT NULL,
                UNIQUE (dataset_id, example_id)
            );
            CREATE TABLE research_example_metadata (
                dataset_id TEXT NOT NULL,
                example_id TEXT NOT NULL,
                note TEXT NOT NULL,
                FOREIGN KEY (dataset_id, example_id)
                    REFERENCES research_examples(dataset_id, example_id)
            );
            INSERT INTO research_datasets VALUES ('ds-1');
            INSERT INTO research_examples VALUES ('ex-1', 'ds-1', 'case-1', 'A');
            INSERT INTO research_example_metadata VALUES ('ds-1', 'case-1', 'retained');
            """
        )
        self.connection.commit()

        rebuild = """
        CREATE TABLE research_examples_v2 (
            id TEXT PRIMARY KEY,
            dataset_id TEXT NOT NULL REFERENCES research_datasets(id),
            example_id TEXT NOT NULL,
            label TEXT NOT NULL,
            annotation_status TEXT NOT NULL DEFAULT 'submitted',
            UNIQUE (dataset_id, example_id)
        );
        INSERT INTO research_examples_v2 (id, dataset_id, example_id, label)
        SELECT id, dataset_id, example_id, label FROM research_examples;
        DROP TABLE research_examples;
        ALTER TABLE research_examples_v2 RENAME TO research_examples;
        """

        apply_migration(
            self.connection,
            "004_research_import_and_annotations.sql",
            rebuild,
            disable_foreign_keys=True,
        )

        self.assertEqual(
            self.connection.execute(
                "SELECT note FROM research_example_metadata"
            ).fetchone()[0],
            "retained",
        )
        self.assertEqual(
            self.connection.execute("PRAGMA foreign_key_check").fetchall(),
            [],
        )
        self.assertEqual(
            self.connection.execute("PRAGMA foreign_keys").fetchone()[0],
            1,
        )
        self.assertIsNotNone(
            self.connection.execute(
                "SELECT 1 FROM schema_migrations WHERE migration_name = ?",
                ("004_research_import_and_annotations.sql",),
            ).fetchone()
        )

    def test_migration_004_foreign_key_violation_rolls_back_rebuild(self):
        self.connection.execute(
            "CREATE TABLE parent (id TEXT PRIMARY KEY)"
        )
        self.connection.execute(
            "CREATE TABLE child (parent_id TEXT REFERENCES parent(id))"
        )
        self.connection.commit()

        invalid_rebuild = """
        CREATE TABLE parent_v2 (id TEXT PRIMARY KEY);
        INSERT INTO parent_v2 VALUES ('ok');
        DROP TABLE parent;
        ALTER TABLE parent_v2 RENAME TO parent;
        INSERT INTO child VALUES ('missing');
        """
        with self.assertRaises(sqlite3.IntegrityError):
            apply_migration(
                self.connection,
                "004_research_import_and_annotations.sql",
                invalid_rebuild,
                disable_foreign_keys=True,
            )

        self.assertEqual(
            self.connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='parent'"
            ).fetchone()[0],
            "parent",
        )
        self.assertEqual(
            self.connection.execute("SELECT id FROM parent").fetchall(),
            [],
        )
        self.assertEqual(
            self.connection.execute("SELECT * FROM child").fetchall(),
            [],
        )
        self.assertEqual(
            self.connection.execute("PRAGMA foreign_keys").fetchone()[0],
            1,
        )




if __name__ == "__main__":
    unittest.main()
