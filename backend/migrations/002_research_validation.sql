CREATE TABLE IF NOT EXISTS research_datasets (
    id TEXT PRIMARY KEY,
    institution_id TEXT NOT NULL REFERENCES institutions(id),
    dataset_version TEXT NOT NULL,
    annotation_version TEXT NOT NULL,
    provenance TEXT NOT NULL,
    split_seed INTEGER NOT NULL,
    split_version TEXT NOT NULL,
    split_config_json TEXT NOT NULL,
    split_summary_json TEXT NOT NULL,
    verification_status TEXT NOT NULL DEFAULT 'submitted'
        CHECK (verification_status IN ('submitted', 'approved', 'rejected')),
    verification_note TEXT,
    reviewed_by TEXT REFERENCES users(id),
    reviewed_at TEXT,
    created_by TEXT NOT NULL REFERENCES users(id),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (institution_id, dataset_version)
);

CREATE TABLE IF NOT EXISTS research_examples (
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
    annotation_status TEXT NOT NULL CHECK (annotation_status IN ('expert_reviewed', 'adjudicated')),
    partition_name TEXT NOT NULL CHECK (partition_name IN ('train', 'validation', 'test')),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (dataset_id, example_id)
);

CREATE INDEX IF NOT EXISTS ix_research_examples_partition
    ON research_examples(dataset_id, partition_name, framework);

CREATE TABLE IF NOT EXISTS research_expert_ratings (
    id TEXT PRIMARY KEY,
    institution_id TEXT NOT NULL REFERENCES institutions(id),
    dataset_id TEXT NOT NULL REFERENCES research_datasets(id),
    case_id TEXT NOT NULL,
    expert_reference TEXT NOT NULL,
    dimension TEXT NOT NULL,
    score REAL NOT NULL,
    partition_name TEXT NOT NULL CHECK (partition_name IN ('train', 'validation', 'test')),
    rating_scale_json TEXT NOT NULL,
    rating_provenance TEXT NOT NULL,
    annotation_version TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('independent', 'adjudicated')),
    review_status TEXT NOT NULL DEFAULT 'submitted'
        CHECK (review_status IN ('submitted', 'approved', 'rejected')),
    review_note TEXT,
    reviewed_by TEXT REFERENCES users(id),
    reviewed_at TEXT,
    created_by TEXT NOT NULL REFERENCES users(id),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (dataset_id, case_id, expert_reference, dimension)
);

CREATE TABLE IF NOT EXISTS research_thresholds (
    id TEXT PRIMARY KEY,
    dataset_id TEXT NOT NULL REFERENCES research_datasets(id),
    threshold REAL NOT NULL CHECK (threshold >= 0 AND threshold <= 1),
    selection_metric TEXT NOT NULL,
    validation_metrics_json TEXT NOT NULL,
    locked_by TEXT NOT NULL REFERENCES users(id),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (dataset_id, selection_metric)
);

CREATE TABLE IF NOT EXISTS research_experiments (
    id TEXT PRIMARY KEY,
    institution_id TEXT NOT NULL REFERENCES institutions(id),
    dataset_id TEXT REFERENCES research_datasets(id),
    experiment_type TEXT NOT NULL,
    configuration_id TEXT NOT NULL,
    configuration_json TEXT NOT NULL,
    model_version TEXT,
    method_version TEXT NOT NULL,
    random_seed INTEGER NOT NULL,
    status TEXT NOT NULL CHECK (status IN (
        'not_implemented', 'blocked_missing_data', 'ready_to_run',
        'running', 'completed', 'failed', 'completed_with_limitations'
    )),
    result_json TEXT,
    warnings_json TEXT NOT NULL DEFAULT '[]',
    error_summary TEXT,
    created_by TEXT NOT NULL REFERENCES users(id),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    completed_at TEXT
);

CREATE TABLE IF NOT EXISTS research_predictions (
    id TEXT PRIMARY KEY,
    experiment_id TEXT NOT NULL REFERENCES research_experiments(id),
    example_id TEXT NOT NULL,
    partition_name TEXT NOT NULL CHECK (partition_name IN ('train', 'validation', 'test')),
    prediction_json TEXT NOT NULL,
    ground_truth_json TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (experiment_id, example_id)
);

CREATE INDEX IF NOT EXISTS ix_research_experiments_institution
    ON research_experiments(institution_id, created_at DESC);
