import hashlib


def approve_synthetic_panel_dataset(
    database, institution_id, dataset_id, submitter_id, records, username_prefix
):
    coordinator_id = database.ensure_admin(
        f"{username_prefix}-coordinator", f"{username_prefix} coordinator password long"
    )
    experts = [
        database.ensure_admin(
            f"{username_prefix}-expert-{index}",
            f"{username_prefix} expert {index} password long",
        )
        for index in range(5)
    ]
    with database.connection() as connection:
        for user_id in [coordinator_id, *experts]:
            connection.execute(
                """INSERT INTO institution_memberships (user_id, institution_id, role, status)
                   VALUES (?, ?, 'administrator', 'active')""",
                (user_id, institution_id),
            )
    assessment_id = database.create_assessment(
        coordinator_id, institution_id, "document_extracted"
    )
    with database.connection() as connection:
        for record in records:
            document_id = record.get("source_document_id")
            if not document_id:
                document_id = f"{username_prefix}-source-{record['example_id']}"
                connection.execute(
                    """UPDATE research_examples SET source_document_id = ?
                       WHERE dataset_id = ? AND example_id = ?""",
                    (document_id, dataset_id, record["example_id"]),
                )
            checksum = hashlib.sha256(
                f"{username_prefix}:{record['example_id']}".encode()
            ).hexdigest()
            connection.execute(
                """INSERT INTO documents
                   (id, institution_id, assessment_id, filename, file_type, file_size,
                    checksum, storage_key, extraction_status, authorization_status,
                    research_permission_status, review_status, malware_scan_status)
                   VALUES (?, ?, ?, ?, 'text/plain', 1, ?, ?, 'completed',
                           'verified', 'verified', 'verified', 'clean')""",
                (
                    document_id, institution_id, assessment_id,
                    f"{record['example_id']}.txt", checksum,
                    f"test-only/{username_prefix}/{record['example_id']}.txt",
                ),
            )

    for expert_id in experts:
        database.verify_expert_qualification(
            coordinator_id,
            institution_id,
            expert_id,
            f"fixture qualification reference for {expert_id}",
            "Synthetic test fixture qualification verification only.",
        )
    database.register_consensus_procedure(
        coordinator_id,
        institution_id,
        f"{username_prefix}-consensus",
        "fixture-v1",
        f"fixture approval reference for {username_prefix}",
        "Synthetic test fixture authority",
        "Synthetic software test procedure; not a research-method decision.",
    )
    for expert_id in experts:
        database.submit_expert_panel_reviews(
            expert_id,
            institution_id,
            dataset_id,
            [
                {
                    "example_id": record["example_id"],
                    "label": record["label"],
                    "rubric_version": "synthetic-fixture-rubric-v1",
                    "continuous_ratings": {"quality": 0.5},
                    "note": "Synthetic software test fixture judgment only.",
                }
                for record in records
            ],
        )
    for record in records:
        database.record_expert_panel_consensus(
            coordinator_id,
            institution_id,
            dataset_id,
            record["example_id"],
            record["label"],
            "consensus",
            f"{username_prefix}-consensus",
            "fixture-v1",
            "Synthetic software test consensus only.",
        )
    database.review_research_dataset(
        coordinator_id,
        institution_id,
        dataset_id,
        "approved",
        "Synthetic software test dataset approval only.",
        source_use_clearance_reference=f"test-only source clearance {username_prefix}",
        institutional_approval_reference=f"test-only institutional approval {username_prefix}",
    )
    return coordinator_id, experts
