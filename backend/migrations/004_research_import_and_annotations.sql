PRAGMA foreign_keys = OFF;
BEGIN IMMEDIATE;

DROP TABLE IF EXISTS research_examples_v2;

CREATE TABLE IF NOT EXISTS research_examples_v2 (
    id TEXT PRIMARY KEY,
    dataset_id TEXT NOT NULL REFERENCES research_datasets(id),
    example_id TEXT NOT NULL,
    framework TEXT NOT NULL,
    indicator TEXT NOT NULL,
    major_indicator_group TEXT,
    label TEXT NOT NULL,
    text TEXT,
    source_document_id TEXT,
    source_passage_id TEXT,
    annotation_version TEXT NOT NULL,
    annotation_provenance TEXT NOT NULL,
    annotation_status TEXT NOT NULL
        CHECK (annotation_status IN ('submitted', 'expert_reviewed', 'adjudicated')),
    partition_name TEXT NOT NULL CHECK (partition_name IN ('train', 'validation', 'test')),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (dataset_id, example_id)
);

INSERT OR IGNORE INTO research_examples_v2
    (id, dataset_id, example_id, framework, indicator, major_indicator_group, label,
     text, source_document_id, source_passage_id, annotation_version,
     annotation_provenance, annotation_status, partition_name, created_at)
SELECT id, dataset_id, example_id, framework, indicator, major_indicator_group, label,
       text, source_document_id, source_passage_id, annotation_version,
       annotation_provenance, annotation_status, partition_name, created_at
FROM research_examples;

DROP TABLE research_examples;
ALTER TABLE research_examples_v2 RENAME TO research_examples;

CREATE INDEX IF NOT EXISTS ix_research_examples_partition
    ON research_examples(dataset_id, partition_name, framework);

COMMIT;
PRAGMA foreign_key_check;
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS research_dataset_imports (
    id TEXT PRIMARY KEY,
    institution_id TEXT NOT NULL REFERENCES institutions(id),
    dataset_id TEXT REFERENCES research_datasets(id),
    created_by TEXT NOT NULL REFERENCES users(id),
    original_filename TEXT NOT NULL,
    storage_key TEXT NOT NULL,
    sha256 TEXT NOT NULL,
    byte_count INTEGER NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('processing', 'accepted', 'rejected')),
    report_json TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS research_example_metadata (
    dataset_id TEXT NOT NULL REFERENCES research_datasets(id),
    example_id TEXT NOT NULL,
    institution_group_id TEXT NOT NULL,
    leakage_group_id TEXT,
    original_prediction_json TEXT,
    source_line INTEGER,
    PRIMARY KEY (dataset_id, example_id),
    FOREIGN KEY (dataset_id, example_id)
        REFERENCES research_examples(dataset_id, example_id)
);

CREATE TABLE IF NOT EXISTS research_annotation_reviews (
    id TEXT PRIMARY KEY,
    dataset_id TEXT NOT NULL,
    example_id TEXT NOT NULL,
    reviewer_id TEXT NOT NULL REFERENCES users(id),
    review_stage TEXT NOT NULL CHECK (review_stage IN ('independent', 'adjudication')),
    label TEXT NOT NULL,
    note TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (dataset_id, example_id, reviewer_id, review_stage),
    FOREIGN KEY (dataset_id, example_id)
        REFERENCES research_examples(dataset_id, example_id)
);

CREATE INDEX IF NOT EXISTS ix_research_annotation_reviews_example
    ON research_annotation_reviews(dataset_id, example_id, review_stage);

CREATE TABLE IF NOT EXISTS research_annotation_consensus (
    dataset_id TEXT NOT NULL,
    example_id TEXT NOT NULL,
    final_label TEXT NOT NULL,
    resolution TEXT NOT NULL CHECK (resolution IN ('agreement', 'adjudicated')),
    resolved_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (dataset_id, example_id),
    FOREIGN KEY (dataset_id, example_id)
        REFERENCES research_examples(dataset_id, example_id)
);
