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
