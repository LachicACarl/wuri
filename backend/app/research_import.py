from __future__ import annotations

import csv
import io
import json
from typing import Any

from .indicators import FRAMEWORK_INDICATORS


MAX_IMPORT_BYTES = 25 * 1024 * 1024
MAX_TEXT_BYTES = 10 * 1024 * 1024
MAX_RECORDS = 2_000
VALID_LABELS = {"true", "false", "1", "0", "yes", "no", "positive", "negative", "relevant", "not_relevant"}


def parse_research_upload(filename: str, content: bytes) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Parse the supported tabular formats while retaining source row numbers."""
    if len(content) > MAX_IMPORT_BYTES:
        return [], [{"line": None, "message": "Upload exceeds the 25 MB limit."}]
    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError:
        return [], [{"line": None, "message": "Upload must be UTF-8 encoded."}]

    extension = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    records: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    if extension == "csv":
        reader = csv.DictReader(io.StringIO(text, newline=""), strict=True)
        try:
            headers = reader.fieldnames or []
        except csv.Error:
            return [], [{"line": reader.line_num or 1, "message": "Malformed CSV."}]
        if (
            not headers or any(not header.strip() for header in headers)
            or len(headers) != len(set(headers))
        ):
            return [], [{"line": 1, "message": "CSV must have a unique, non-empty header row."}]
        try:
            for line, row in enumerate(reader, start=2):
                if None in row:
                    errors.append({"line": line, "message": "Row contains more values than the header."})
                    continue
                if not row or not any(value and value.strip() for value in row.values()):
                    errors.append({"line": line, "message": "Blank rows are not allowed."})
                    continue
                records.append({key: value for key, value in row.items()})
                records[-1]["_source_line"] = line
        except csv.Error:
            errors.append({"line": (reader.line_num or 1) + 1, "message": "Malformed CSV."})
            return [], errors
    elif extension == "jsonl":
        for line, raw_line in enumerate(text.splitlines(), start=1):
            if not raw_line.strip():
                errors.append({"line": line, "message": "Blank JSONL lines are not allowed."})
                continue
            try:
                record = json.loads(raw_line)
            except json.JSONDecodeError as error:
                errors.append({"line": line, "message": f"Invalid JSON: {error.msg}."})
                continue
            if not isinstance(record, dict):
                errors.append({"line": line, "message": "Each JSONL line must contain one object."})
                continue
            record["_source_line"] = line
            records.append(record)
    else:
        return [], [{"line": None, "message": "Only CSV and JSONL imports are supported."}]

    if not records and not errors:
        errors.append({"line": None, "message": "Upload contains no records."})
    if len(records) > MAX_RECORDS:
        errors.append({"line": None, "message": f"Upload exceeds the {MAX_RECORDS}-record limit."})
    return records, errors


def validate_research_records(
    records: list[dict[str, Any]],
    *,
    dataset_version: str,
    annotation_version: str,
    provenance: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    prepared: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    seen_pairs: set[tuple[str, str, str]] = set()
    total_text_bytes = 0

    for row_index, source in enumerate(records, start=1):
        line = source.get("_source_line", row_index)

        def invalid(message: str) -> None:
            errors.append({"line": line, "example_id": source.get("example_id"), "message": message})

        example_id = source.get("example_id")
        framework = source.get("framework")
        indicator = source.get("indicator")
        label = source.get("label")
        document_id = source.get("source_document_id")
        passage_id = source.get("source_passage_id")
        institution_group_id = source.get("institution_group_id")
        evidence_text = source.get("text")
        if not isinstance(example_id, str) or not example_id.strip() or len(example_id) > 200:
            invalid("example_id must be a non-empty string of at most 200 characters.")
        elif example_id in seen_ids:
            invalid("example_id is duplicated in this upload.")
        else:
            seen_ids.add(example_id)
        if not isinstance(framework, str) or framework not in FRAMEWORK_INDICATORS:
            invalid("framework is not a supported framework identifier.")
        elif not isinstance(indicator, str) or indicator not in FRAMEWORK_INDICATORS[framework]:
            invalid("indicator is not a supported indicator identifier for this framework.")
        if isinstance(label, bool):
            label_key = str(label).lower()
        elif isinstance(label, (str, int)):
            label_key = str(label).strip().lower()
        else:
            label_key = ""
        if label_key not in VALID_LABELS:
            invalid("label must use a supported binary relevance value.")
        if not isinstance(document_id, str) or not document_id.strip() or len(document_id) > 500:
            invalid("source_document_id is required and must be a non-empty string.")
        if not isinstance(institution_group_id, str) or not institution_group_id.strip() or len(institution_group_id) > 200:
            invalid("institution_group_id is required and must be a non-empty string.")
        leakage_group_id = source.get("leakage_group_id")
        if leakage_group_id is not None and (
            not isinstance(leakage_group_id, str) or not leakage_group_id.strip()
            or len(leakage_group_id) > 200
        ):
            invalid("leakage_group_id must be a non-empty string when supplied.")
        major_group = source.get("major_indicator_group")
        if major_group is not None and (
            not isinstance(major_group, str) or len(major_group) > 200
        ):
            invalid("major_indicator_group must be a string of at most 200 characters.")
        if passage_id is not None and (not isinstance(passage_id, str) or not passage_id.strip()):
            invalid("source_passage_id must be a non-empty string when supplied.")
        if not isinstance(evidence_text, str) or not evidence_text.strip():
            evidence_text = None
        elif len(evidence_text) > 100_000:
            invalid("text must not exceed 100,000 characters.")
        else:
            total_text_bytes += len(evidence_text.encode("utf-8"))
        if not evidence_text and not passage_id:
            invalid("Provide evidence text or source_passage_id.")
        if isinstance(framework, str) and framework in FRAMEWORK_INDICATORS and isinstance(indicator, str):
            pair = (str(document_id), str(framework), indicator)
            if pair in seen_pairs:
                invalid("A source document may contain only one annotation for a framework/indicator pair.")
            seen_pairs.add(pair)

        row_annotation_version = source.get("annotation_version") or annotation_version
        if not isinstance(row_annotation_version, str) or not row_annotation_version.strip():
            invalid("annotation_version is required.")
        row_provenance = source.get("annotation_provenance") or provenance
        if (
            not isinstance(row_provenance, str) or not row_provenance.strip()
            or len(row_provenance) > 2_000
        ):
            invalid("annotation_provenance must be a non-empty string of at most 2,000 characters.")
        if errors and errors[-1].get("line") == line:
            continue
        prediction = source.get("model_prediction")
        try:
            if isinstance(prediction, str):
                prediction_json = json.dumps(json.loads(prediction), sort_keys=True)
            else:
                prediction_json = json.dumps(prediction, sort_keys=True, allow_nan=False) if prediction is not None else None
        except (json.JSONDecodeError, TypeError, ValueError):
            if isinstance(prediction, str):
                prediction_json = json.dumps(prediction)
            else:
                invalid("model_prediction must be valid JSON without non-finite numbers.")
                continue
        prepared.append({
            "example_id": example_id.strip(),
            "text": evidence_text,
            "framework": framework,
            "indicator": indicator,
            "major_indicator_group": source.get("major_indicator_group"),
            "label": label if isinstance(label, bool) else str(label).strip() if isinstance(label, int) else label,
            "source_document_id": document_id.strip(),
            "source_passage_id": passage_id.strip() if isinstance(passage_id, str) else None,
            "annotation_version": row_annotation_version.strip(),
            "annotation_provenance": row_provenance.strip(),
            "annotation_status": "submitted",
            "institution_group_id": institution_group_id.strip(),
            "leakage_group_id": leakage_group_id.strip() if isinstance(leakage_group_id, str) else None,
            "original_prediction_json": prediction_json,
            "source_line": line,
        })

    if total_text_bytes > MAX_TEXT_BYTES:
        errors.append({"line": None, "message": "Evidence text exceeds the 10 MB limit."})
    if not isinstance(dataset_version, str) or not dataset_version.strip():
        errors.append({"line": None, "message": "dataset_version is required."})
    if not isinstance(annotation_version, str) or not annotation_version.strip():
        errors.append({"line": None, "message": "annotation_version is required."})
    if not isinstance(provenance, str) or not provenance.strip():
        errors.append({"line": None, "message": "provenance is required."})
    return prepared if not errors else [], errors
