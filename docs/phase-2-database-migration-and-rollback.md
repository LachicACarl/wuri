# Phase 2 — Database Migration and Rollback Plan

Status: proposed design only. Do not connect to Supabase, read or change the local database, or run migrations until the security hold is explicitly cleared.

## Source baseline

`backend/app/database.py` opens the SQLite database, enables foreign keys, commits each successful `connection()` context, rolls back on exceptions, and applies sorted SQLite scripts during `Database` initialization. Eight SQL migration files are tracked in `backend/migrations/`; migration 004 performs a table rebuild, while migration 005 includes a data update that invalidates prior approvals. The application currently has no PostgreSQL driver or separate PostgreSQL migration runner.

The default SQLite path is `backend/data/wuri.sqlite3`, overridden by `WURI_DATABASE_PATH`. This plan did not open or inspect that file. No database migration or data copy is authorized now.

## Proposed deployment/data strategy

Use a new, isolated PostgreSQL development project and retain the existing SQLite deployment/data as a separate source and rollback artifact. The initial data path should be a controlled one-time export/import, not dual-write. Do not point the SQLite application at PostgreSQL or replay its migration scripts.

1. **Clearance and ownership:** Obtain written security clearance for any runtime or migration activity. Confirm the project owner, data custodian, researcher approvals, and the authorized migration operator. Supabase key rotation remains **UNCONFIRMED**.
2. **Freeze and protect the source:** After authorization, identify the exact SQLite file from the process configuration without printing secrets. Schedule a write freeze, create a protected backup using an approved method, record a checksum and file size, and verify a restorable copy. Do not overwrite or move the source database.
3. **Create PostgreSQL schema separately:** Author PostgreSQL-specific migrations in version control. Use an ordered migration ledger with a version, checksum, applied timestamp, and success/failure record. Make each migration transactional where PostgreSQL supports it. Do not reuse `schema_migrations` rows as proof that the SQLite DDL ran on PostgreSQL.
4. **Deploy schema to a disposable development project:** Apply the PostgreSQL migrations only after clearance. Use synthetic records first. Verify PK/FK/check/unique constraints, indexes, defaults, and query behavior before any source-data export.
5. **Implement a controlled exporter/importer:** Use a fixed, documented table order with parameterized inserts and explicit conversion functions. Preserve text/prefixed IDs, foreign keys, provenance, approval states, audit records, and nullable values. Never use production credentials in a developer workstation or log export rows.
6. **Move objects separately:** Database rows contain `storage_key` values while file bytes are stored on local disk. Copy files to private object storage in a separate controlled process, verify SHA-256/size, and update keys through a recorded mapping. Do not make this a database-only migration.
7. **Reconcile:** Compare per-table counts, FK relationships, unique-key counts, null counts, constrained status counts, and JSON parse/round-trip results. Compare per-object checksums and sizes. Review audit/provenance preservation and any intentionally changed values. Acceptance criteria and tolerances must be approved before data transfer.
8. **Cut over:** Keep the original SQLite source and a verified backup unchanged. At an approved cutover, freeze writes, perform a final export delta or full final copy, reconcile, then direct the approved backend to PostgreSQL and object storage. Keep a documented decision owner and rollback window.

## Reversibility and rollback boundary

The safest rollback is to return to the unchanged SQLite deployment **before PostgreSQL receives authoritative writes**. Keep the old service configuration and a protected SQLite snapshot available; change traffic/configuration only through an approved deployment procedure.

Once PostgreSQL accepts new authoritative writes, switching back to the old SQLite file would lose those writes. There is no bidirectional replication or reverse-migration process in the repository. Do not claim automatic rollback after cutover. A later rollback would require a separately designed PostgreSQL-to-SQLite export, reconciliation, and controlled write freeze, or a restore/forward-fix decision. Schema/type transformations, timestamp normalization, JSONB conversion, and object-key replacement may not be exactly reversible.

Prefer forward recovery for failures after cutover unless a tested reverse-data path exists. Keep timestamped database backups and object-storage recovery/versioning expectations separate; a PostgreSQL backup does not restore external files. Confirm restore access and recovery-point/recovery-time objectives with the project owner before production use.

## Table and data ordering considerations

Create parent tables before children: users/institutions, memberships, assessments, documents, evidence passages/matches, research datasets/examples/ratings/experiments, then dependent review/consensus tables. The exact foreign-key graph must be derived from every migration and the exporter; do not rely on this abbreviated order alone. Preserve compound keys in research review/consensus tables and the parent institution self-reference.

Specific migration semantics to preserve:

- Migration 004 rebuilds examples and uses `INSERT OR IGNORE`; a PostgreSQL port must define which conflicts are ignored and prove that all other source rows are preserved.
- Migration 005 changes approved research datasets back to submitted and inserts audit events. That is an intentional provenance gate, not disposable seed data.
- Migrations 006–008 add institution, evidence authorization, review, and malware scan state defaults. Preserve defaults and status checks for existing rows.
- The SQLite migration runner records migration names after script execution and runs a foreign-key check. The PostgreSQL runner needs independent failure, retry, checksum, and concurrent-start behavior.

## Conversion policy to decide before export

| SQLite representation | Conservative initial PostgreSQL choice | Required decision/check |
|---|---|---|
| IDs stored as text, often prefixed UUID strings | `TEXT` with the same values | Preserve all references and API contracts. Do not cast to `UUID` without proving every ID is canonical and removing prefixes safely. |
| JSON stored as `TEXT` and serialized by `json.dumps`/`json.loads` | Keep as `TEXT` for the first compatible cutover, or deliberately use `JSONB` with coordinated code changes | Validate every field, nullable value, ordering assumption, and JSON query. Avoid accidental double encoding. |
| Timestamps stored as text with `CURRENT_TIMESTAMP` defaults | Choose a single policy: preserve text formatting first or migrate to `TIMESTAMPTZ` with conversion at API boundaries | Confirm UTC/timezone, precision, string comparisons, expiry, and output formatting. Do not allow implicit conversion to change audit chronology. |
| SQLite `INTEGER` / `REAL` | PostgreSQL `INTEGER`/`BIGINT` and `DOUBLE PRECISION` or a justified `NUMERIC` | Check observed ranges and numeric meaning; don't alter score precision without researcher review. |
| `CHECK`, `UNIQUE`, FK and compound PK constraints | Recreate as PostgreSQL constraints | Preflight synthetic/source-copy data for violations before adding constraints. Preserve delete/cascade behavior. |

## Verification gates (future, after written clearance)

- Fresh PostgreSQL schema creation and migration restart policy.
- Per-migration transaction failure and retry behavior.
- Create/read/update/delete flows for each domain table, with foreign-key and unique violations.
- Transaction rollback and connection loss/recovery.
- Record-level reconciliation and object checksum reconciliation.
- Authentication, session, and institution isolation checks with at least two synthetic institutions.
- Restoring both database and object-store backups in a separate environment.
- Approved sign-off from the security reviewer, data owner, and research owner as applicable.

No code, database, migration, or data copy was changed or run to prepare this plan. Runtime and migration work remain blocked by the security NO-GO gate.
