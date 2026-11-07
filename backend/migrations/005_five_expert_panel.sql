ALTER TABLE research_datasets
    ADD COLUMN review_design TEXT NOT NULL DEFAULT 'legacy_two_reviewer';

ALTER TABLE research_datasets
    ADD COLUMN consensus_procedure_id TEXT;

ALTER TABLE research_datasets
    ADD COLUMN source_use_clearance_reference TEXT;

ALTER TABLE research_datasets
    ADD COLUMN institutional_approval_reference TEXT;

INSERT INTO audit_events
    (id, institution_id, assessment_id, user_id, event_type, metadata_json)
SELECT lower(hex(randomblob(16))), institution_id, NULL, NULL,
       'research.dataset.legacy_approval_invalidated',
       json_object('dataset_id', id, 'review_design', 'legacy_two_reviewer')
FROM research_datasets
WHERE verification_status = 'approved';

UPDATE research_datasets
SET verification_status = 'submitted',
    verification_note = 'Legacy approval invalidated: five-expert panel and clearance references are required.',
    reviewed_by = NULL,
    reviewed_at = NULL
WHERE verification_status = 'approved';

CREATE TABLE IF NOT EXISTS research_expert_qualifications (
    institution_id TEXT NOT NULL REFERENCES institutions(id),
    expert_id TEXT NOT NULL REFERENCES users(id),
    qualification_status TEXT NOT NULL
        CHECK (qualification_status IN ('verified', 'rejected')),
    qualification_reference TEXT NOT NULL,
    verification_note TEXT NOT NULL,
    verified_by TEXT NOT NULL REFERENCES users(id),
    verified_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (institution_id, expert_id)
);

CREATE TABLE IF NOT EXISTS research_expert_panel_reviews (
    dataset_id TEXT NOT NULL,
    example_id TEXT NOT NULL,
    reviewer_id TEXT NOT NULL REFERENCES users(id),
    rubric_version TEXT NOT NULL,
    categorical_label TEXT NOT NULL,
    continuous_ratings_json TEXT NOT NULL DEFAULT '{}',
    note TEXT NOT NULL,
    submitted_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (dataset_id, example_id, reviewer_id),
    FOREIGN KEY (dataset_id, example_id)
        REFERENCES research_examples(dataset_id, example_id)
);

CREATE INDEX IF NOT EXISTS ix_research_expert_panel_reviews_case
    ON research_expert_panel_reviews(dataset_id, example_id);

CREATE TABLE IF NOT EXISTS research_consensus_procedures (
    institution_id TEXT NOT NULL REFERENCES institutions(id),
    procedure_id TEXT NOT NULL,
    procedure_version TEXT NOT NULL,
    approval_reference TEXT NOT NULL,
    approving_authority TEXT NOT NULL,
    rationale TEXT NOT NULL,
    approved_by TEXT NOT NULL REFERENCES users(id),
    approved_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (institution_id, procedure_id, procedure_version)
);

CREATE TABLE IF NOT EXISTS research_expert_panel_consensus (
    dataset_id TEXT NOT NULL,
    example_id TEXT NOT NULL,
    institution_id TEXT NOT NULL REFERENCES institutions(id),
    final_label TEXT NOT NULL,
    resolution TEXT NOT NULL CHECK (resolution IN ('consensus', 'adjudicated')),
    procedure_id TEXT NOT NULL,
    procedure_version TEXT NOT NULL,
    resolved_by TEXT NOT NULL REFERENCES users(id),
    note TEXT NOT NULL,
    resolved_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (dataset_id, example_id),
    FOREIGN KEY (dataset_id, example_id)
        REFERENCES research_examples(dataset_id, example_id),
    FOREIGN KEY (institution_id, procedure_id, procedure_version)
        REFERENCES research_consensus_procedures(institution_id, procedure_id, procedure_version)
);
