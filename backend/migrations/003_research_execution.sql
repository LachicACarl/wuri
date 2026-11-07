CREATE TABLE IF NOT EXISTS research_experiment_details (
    experiment_id TEXT PRIMARY KEY REFERENCES research_experiments(id),
    execution_state TEXT NOT NULL CHECK (execution_state IN (
        'ready_to_run', 'blocked_missing_data', 'blocked_missing_model',
        'blocked_methodology_review', 'not_implemented', 'running',
        'completed', 'completed_with_limitations', 'failed'
    )),
    preflight_json TEXT NOT NULL,
    sample_counts_json TEXT NOT NULL DEFAULT '{}',
    evaluation_config_json TEXT NOT NULL DEFAULT '{}',
    started_at TEXT,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_research_experiment_details_state
    ON research_experiment_details(execution_state, updated_at DESC);
