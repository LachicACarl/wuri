import os
import json
import math
import sqlite3
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote
from typing import Any, Literal
from uuid import uuid4

from fastapi import Cookie, FastAPI, File, Form, HTTPException, Query, Request, Response, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator

from .document_processing import (
    ParserWorkerUnavailableError, extract_blocks_isolated, segment_blocks,
)
from .malware_scanning import configured_malware_scanner
from .database import Database
from .experiment_runner import ResearchExperimentRunner, has_local_sentence_transformer_artifact
from .frameworks import FRAMEWORK_DEFINITIONS, FRAMEWORK_EDITIONS, framework_catalog, verified_frameworks
from .indicators import FRAMEWORK_INDICATORS
from .orchestration import determine_status
from .retrieval import retrieve_matches
from .research_validation import ablation_statuses, split_evidence_dataset
from .research_import import (
    MAX_IMPORT_BYTES, parse_research_upload, validate_research_records,
)
from .security import (
    SESSION_COOKIE, SESSION_TTL_SECONDS, create_session_token, hash_password,
    read_session_claims, validate_session_secret, verify_password,
)
from .storage import PrivateStorage
from .request_limits import RequestBodyLimitMiddleware
from .cors_config import configured_cors_origins

MAX_UPLOAD_BYTES = 25 * 1024 * 1024
SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".txt"}

app = FastAPI(title="WURI Ranking Readiness API")
# The last middleware registered is outermost in Starlette. Keep CORS outside
# the request guard so approved origins retain CORS headers on 413 responses.
app.add_middleware(
    RequestBodyLimitMiddleware,
    max_body_bytes=MAX_UPLOAD_BYTES + 1024 * 1024,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=configured_cors_origins(),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["Content-Type"],
    expose_headers=["Content-Type"],
)

database = Database()
storage = PrivateStorage()
malware_scanner = configured_malware_scanner()


class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=254)
    password: str = Field(min_length=1, max_length=1024)


class InstitutionRequest(BaseModel):
    name: str = Field(min_length=1, max_length=300)
    display_name: str | None = Field(default=None, max_length=300)
    country: str = Field(default="Philippines", min_length=1, max_length=100)
    region: str | None = Field(default=None, max_length=200)
    institution_type: str | None = Field(default=None, max_length=100)
    campus_name: str | None = Field(default=None, max_length=300)
    parent_institution_id: str | None = Field(default=None, max_length=100)
    status: Literal["active", "inactive"] = "active"
    provenance: str | None = Field(default=None, max_length=2_000)


class EvidenceReadinessRequest(BaseModel):
    framework_id: str = Field(min_length=1, max_length=100)
    framework_edition: str = Field(min_length=1, max_length=20)
    criterion_id: str = Field(min_length=1, max_length=200)
    eligibility_status: Literal["verified", "not_eligible", "unknown"] = "unknown"
    authorization_status: Literal["verified", "not_authorized", "unknown"] = "unknown"
    provenance_status: Literal["verified", "incomplete", "unknown"] = "unknown"
    evidence_status: Literal["available", "missing", "incomplete", "unknown"] = "unknown"
    privacy_status: Literal["reviewed", "issues_found", "unknown"] = "unknown"
    expert_review_status: Literal["not_required", "pending", "complete", "unknown"] = "not_required"
    evidence_title: str | None = Field(default=None, max_length=300)
    evidence_type: str | None = Field(default=None, max_length=100)
    source_reference: str | None = Field(default=None, max_length=1_000)
    source_date: str | None = Field(default=None, max_length=30)
    collection_date: str | None = Field(default=None, max_length=30)
    description: str | None = Field(default=None, max_length=2_000)
    limitations: str | None = Field(default=None, max_length=2_000)
    reviewer_id: str | None = Field(default=None, max_length=100)


class DocumentMetadataRequest(BaseModel):
    title: str | None = Field(default=None, max_length=300)
    source_reference: str | None = Field(default=None, max_length=1_000)
    collection_date: str | None = Field(default=None, max_length=30)
    reporting_period: str | None = Field(default=None, max_length=100)
    provenance: str | None = Field(default=None, max_length=2_000)
    authorization_status: Literal["verified", "pending", "unavailable", "unknown"] | None = None
    research_permission_status: Literal["verified", "pending", "unavailable", "unknown"] | None = None
    review_status: Literal["uploaded", "processing_failed", "pending_review", "verified", "rejected"] | None = None
    limitations: str | None = Field(default=None, max_length=2_000)


class ResearchExampleRequest(BaseModel):
    example_id: str = Field(min_length=1, max_length=200)
    text: str | None = Field(default=None, max_length=10_000)
    framework: str = Field(min_length=1, max_length=100)
    indicator: str = Field(min_length=1, max_length=200)
    major_indicator_group: str | None = Field(default=None, max_length=200)
    label: str | bool
    source_document_id: str | None = None
    source_passage_id: str | None = None
    annotation_version: str | None = Field(default=None, max_length=100)
    annotation_provenance: str = Field(min_length=1, max_length=2_000)
    annotation_status: str
    institution_group_id: str | None = Field(default=None, max_length=200)
    leakage_group_id: str | None = Field(default=None, max_length=200)
    model_prediction: Any = None


class ResearchDatasetRequest(BaseModel):
    dataset_version: str = Field(min_length=1, max_length=100)
    annotation_version: str = Field(min_length=1, max_length=100)
    provenance: str = Field(min_length=1, max_length=2_000)
    random_seed: int
    records: list[ResearchExampleRequest] = Field(min_length=3, max_length=2_000)


class ExpertRatingRequest(BaseModel):
    case_id: str = Field(min_length=1, max_length=200)
    expert_reference: str = Field(min_length=1, max_length=100)
    dimension: str = Field(min_length=1, max_length=200)
    score: float
    rating_scale: dict[str, float]
    provenance: str = Field(min_length=1, max_length=2_000)
    annotation_version: str = Field(min_length=1, max_length=100)
    status: Literal["independent", "adjudicated"]


class ExpertRatingsRequest(BaseModel):
    ratings: list[ExpertRatingRequest] = Field(min_length=1, max_length=50_000)


class DatasetReviewRequest(BaseModel):
    decision: Literal["approved", "rejected"]
    note: str = Field(min_length=10, max_length=2_000)
    source_use_clearance_reference: str | None = Field(default=None, max_length=500)
    institutional_approval_reference: str | None = Field(default=None, max_length=500)


class ResearchExperimentRequest(BaseModel):
    dataset_id: str = Field(min_length=1, max_length=100)
    configuration_id: Literal["A0", "A1", "A2", "A3", "A4"]
    random_seed: int
    evaluation_scope: Literal["retrieval", "readiness"] = "retrieval"


class AnnotationReviewItem(BaseModel):
    example_id: str = Field(min_length=1, max_length=200)
    label: str | bool
    decision: Literal["confirm", "correct", "adjudicate"]
    note: str = Field(min_length=10, max_length=2_000)


class AnnotationReviewsRequest(BaseModel):
    reviews: list[AnnotationReviewItem] = Field(min_length=1, max_length=50)


class ExpertQualificationRequest(BaseModel):
    expert_id: str = Field(min_length=1, max_length=100)
    qualification_reference: str = Field(min_length=1, max_length=500)
    note: str = Field(min_length=10, max_length=2_000)
    status: Literal["verified", "rejected"] = "verified"


class ConsensusProcedureRequest(BaseModel):
    procedure_id: str = Field(min_length=1, max_length=100)
    procedure_version: str = Field(min_length=1, max_length=100)
    approval_reference: str = Field(min_length=1, max_length=500)
    approving_authority: str = Field(min_length=1, max_length=300)
    rationale: str = Field(min_length=10, max_length=2_000)


class ExpertPanelReviewItem(BaseModel):
    example_id: str = Field(min_length=1, max_length=200)
    label: str | bool
    rubric_version: str = Field(min_length=1, max_length=100)
    continuous_ratings: dict[str, float] = Field(default_factory=dict)
    note: str = Field(min_length=10, max_length=2_000)

    @field_validator("continuous_ratings", mode="before")
    @classmethod
    def validate_continuous_ratings(cls, value):
        if not isinstance(value, dict):
            raise ValueError("Continuous ratings must be a mapping of rubric dimension to score.")
        for dimension, score in value.items():
            if (
                not isinstance(dimension, str) or not dimension.strip()
                or isinstance(score, bool) or not isinstance(score, (int, float))
                or not math.isfinite(score) or not 0 <= score <= 1
            ):
                raise ValueError("Continuous ratings must be named, finite numeric scores within [0, 1].")
        return value


class ExpertPanelReviewsRequest(BaseModel):
    reviews: list[ExpertPanelReviewItem] = Field(min_length=1, max_length=50)


class ExpertPanelConsensusRequest(BaseModel):
    example_id: str = Field(min_length=1, max_length=200)
    final_label: str | bool
    resolution: Literal["consensus", "adjudicated"]
    procedure_id: str = Field(min_length=1, max_length=100)
    procedure_version: str = Field(min_length=1, max_length=100)
    note: str = Field(min_length=10, max_length=2_000)


@app.get("/")
def read_root():
    return {"status": "Backend active"}


@app.get("/api/frameworks")
def list_framework_catalog():
    return {
        "frameworks": framework_catalog(),
        "editions": FRAMEWORK_EDITIONS,
        "scoring_enabled": False,
    }


@app.get("/api/institutions")
def list_institutions(session: str | None = Cookie(default=None, alias=SESSION_COOKIE)):
    user = current_user(session)
    return {"institutions": [dict(row) for row in database.institutions_for_user(user["id"])]}


@app.post("/api/institutions", status_code=201)
def create_institution(
    request: InstitutionRequest,
    session: str | None = Cookie(default=None, alias=SESSION_COOKIE),
):
    user = current_user(session)
    try:
        institution_id = database.create_institution(user["id"], request.model_dump())
    except PermissionError as error:
        raise HTTPException(status_code=403, detail=str(error)) from error
    except sqlite3.IntegrityError as error:
        raise HTTPException(status_code=409, detail="Institution could not be created.") from error
    return {"institution_id": institution_id}


@app.patch("/api/institutions/{institution_id}")
def update_institution(
    institution_id: str,
    request: InstitutionRequest,
    session: str | None = Cookie(default=None, alias=SESSION_COOKIE),
):
    user = current_user(session)
    try:
        database.update_institution(user["id"], institution_id, request.model_dump())
    except PermissionError as error:
        raise HTTPException(status_code=403, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    return {"updated": True, "institution_id": institution_id}


@app.get("/api/institutions/{institution_id}/readiness")
def list_evidence_readiness(
    institution_id: str,
    framework_id: str = Query(min_length=1, max_length=100),
    framework_edition: str = Query(min_length=1, max_length=20),
    session: str | None = Cookie(default=None, alias=SESSION_COOKIE),
):
    user = current_user(session)
    if FRAMEWORK_EDITIONS.get(framework_id) != framework_edition:
        raise HTTPException(status_code=422, detail="Framework edition is not registered.")
    try:
        records = database.evidence_readiness(
            user["id"], institution_id, framework_id, framework_edition
        )
    except PermissionError as error:
        raise HTTPException(status_code=403, detail=str(error)) from error
    return {
        "institution_id": institution_id,
        "framework_id": framework_id,
        "framework_edition": framework_edition,
        "records": [dict(row) for row in records],
        "scoring_enabled": False,
    }


@app.put("/api/institutions/{institution_id}/readiness", status_code=200)
def update_evidence_readiness(
    institution_id: str,
    request: EvidenceReadinessRequest,
    session: str | None = Cookie(default=None, alias=SESSION_COOKIE),
):
    user = current_user(session)
    if FRAMEWORK_EDITIONS.get(request.framework_id) != request.framework_edition:
        raise HTTPException(status_code=422, detail="Framework edition is not registered.")
    if request.criterion_id not in FRAMEWORK_DEFINITIONS[request.framework_id].criteria:
        raise HTTPException(status_code=422, detail="Criterion is not registered for this framework.")
    try:
        record_id = database.upsert_evidence_readiness(
            user["id"], institution_id, request.model_dump()
        )
    except PermissionError as error:
        raise HTTPException(status_code=403, detail=str(error)) from error
    except sqlite3.IntegrityError as error:
        raise HTTPException(status_code=409, detail="Evidence readiness record could not be saved.") from error
    return {"readiness_id": record_id, "updated": True, "scoring_enabled": False}


@app.post("/api/auth/login")
def login(request: LoginRequest, response: Response, http_request: Request):
    configured_username = os.getenv("WURI_ADMIN_USERNAME")
    configured_password = os.getenv("WURI_ADMIN_PASSWORD")
    try:
        secret = validate_session_secret(os.getenv("WURI_SESSION_SECRET"))
    except ValueError as error:
        raise HTTPException(status_code=503, detail="Authentication configuration is invalid.") from error
    if not configured_username or not configured_password:
        raise HTTPException(status_code=503, detail="Authentication is not configured.")

    # Use the direct ASGI peer address. Do not trust X-Forwarded-For unless a
    # separately configured trusted-proxy layer sanitizes it.
    client_host = http_request.client.host if http_request.client else "unknown"
    normalized_login = request.username.strip().lower()
    ip_rate_key = hashlib.sha256(f"ip:{client_host}".encode("utf-8")).hexdigest()
    account_rate_key = hashlib.sha256(
        f"account:{client_host}:{normalized_login}".encode("utf-8")
    ).hexdigest()
    retry_after = max(
        database.login_rate_limit_status(account_rate_key),
        database.login_rate_limit_status(ip_rate_key),
    )
    if retry_after:
        raise HTTPException(
            status_code=429,
            detail="Too many failed login attempts. Try again later.",
            headers={"Retry-After": str(retry_after)},
        )

    normalized_admin = configured_username.strip().lower()
    if not database.user_by_username(normalized_admin):
        try:
            database.ensure_admin(normalized_admin, hash_password(configured_password))
        except ValueError as error:
            raise HTTPException(status_code=503, detail="Authentication configuration is invalid.") from error

    user = database.user_by_username(normalized_login)
    if not user or user["status"] != "active" or not verify_password(request.password, user["password_hash"]):
        account_retry = database.record_login_failure(
            account_rate_key, max_attempts=5, window_seconds=900
        )
        ip_retry = database.record_login_failure(
            ip_rate_key, max_attempts=20, window_seconds=900
        )
        retry_after = max(account_retry, ip_retry)
        if retry_after:
            raise HTTPException(
                status_code=429,
                detail="Too many failed login attempts. Try again later.",
                headers={"Retry-After": str(retry_after)},
            )
        raise HTTPException(status_code=401, detail="Invalid credentials.")

    database.clear_login_failures(account_rate_key)
    database.clear_login_failures(ip_rate_key)
    token = create_session_token(user["id"], secret)
    claims = read_session_claims(token, secret)
    if not claims:
        raise HTTPException(status_code=503, detail="Unable to establish an authenticated session.")
    database.create_session(
        str(claims["session_id"]), user["id"], int(claims["expires_at"])
    )
    response.set_cookie(
        SESSION_COOKIE,
        token,
        httponly=True,
        secure=session_cookie_secure(),
        samesite="lax",
        max_age=SESSION_TTL_SECONDS,
    )
    return {"authenticated": True}


@app.get("/api/auth/session")
def session_status(session: str | None = Cookie(default=None, alias=SESSION_COOKIE)):
    user = current_user(session)
    return {
        "authenticated": True,
        "user": {
            "id": user["id"],
            "username": user["username"],
            "status": user["status"],
        },
    }


@app.post("/api/auth/logout")
def logout(
    response: Response,
    session: str | None = Cookie(default=None, alias=SESSION_COOKIE),
):
    secret = os.getenv("WURI_SESSION_SECRET")
    claims = read_session_claims(session, secret) if secret else None
    if claims:
        database.revoke_session(str(claims["session_id"]))
    response.delete_cookie(
        SESSION_COOKIE,
        httponly=True,
        secure=session_cookie_secure(),
        samesite="lax",
    )
    return {"authenticated": False}


def current_user(session: str | None):
    secret = os.getenv("WURI_SESSION_SECRET")
    claims = read_session_claims(session, secret) if secret else None
    if not claims:
        raise HTTPException(status_code=401, detail="Authentication required.")
    user_id = str(claims["user_id"])
    if not database.session_is_active(str(claims["session_id"]), user_id):
        raise HTTPException(status_code=401, detail="Authentication required.")
    user = database.user(user_id)
    if not user or user["status"] != "active":
        raise HTTPException(status_code=401, detail="Authentication required.")
    return user

def session_cookie_secure() -> bool:
    requested = os.getenv("SESSION_COOKIE_SECURE", "true").strip().lower()
    if requested not in {"true", "false"}:
        raise HTTPException(status_code=503, detail="SESSION_COOKIE_SECURE must be true or false.")
    if requested == "false" and os.getenv("WURI_ENVIRONMENT", "").strip().lower() != "development":
        raise HTTPException(
            status_code=503,
            detail="Insecure session cookies require WURI_ENVIRONMENT=development.",
        )
    return requested == "true"


def selected_institution(user_id: str, institution_id: str | None):
    memberships = database.memberships(user_id)
    allowed = {row["institution_id"] for row in memberships if row["role"] in {"administrator", "evaluator"}}
    if institution_id:
        if institution_id in allowed:
            return institution_id
        raise HTTPException(status_code=403, detail="Institution access denied.")
    if len(allowed) == 1:
        return next(iter(allowed))
    raise HTTPException(status_code=403, detail="An authorized institution is required.")


def authorized_research_institution(user_id: str, institution_id: str | None):
    memberships = database.memberships(user_id)
    allowed = {row["institution_id"] for row in memberships}
    if institution_id:
        if institution_id in allowed:
            return institution_id
        raise HTTPException(status_code=403, detail="Institution access denied.")
    if len(allowed) == 1:
        return next(iter(allowed))
    raise HTTPException(status_code=403, detail="An authorized institution is required.")


def _validate_upload_content(extension: str, content: bytes):
    if extension == ".txt":
        try:
            content.decode("utf-8")
        except UnicodeDecodeError as error:
            raise HTTPException(status_code=415, detail="TXT evidence must be UTF-8 text.") from error
    elif extension == ".pdf" and not content.startswith(b"%PDF-"):
        raise HTTPException(status_code=415, detail="The uploaded file is not a valid PDF.")
    elif extension == ".docx" and not content.startswith(b"PK"):
        raise HTTPException(status_code=415, detail="The uploaded file is not a valid DOCX archive.")


async def _read_upload_limited(file: UploadFile) -> bytes:
    """Read an upload without buffering more than the configured size limit."""
    chunks = []
    total = 0
    try:
        while True:
            chunk = await file.read(min(1024 * 1024, MAX_UPLOAD_BYTES + 1 - total))
            if not chunk:
                break
            total += len(chunk)
            if total > MAX_UPLOAD_BYTES:
                raise HTTPException(status_code=413, detail="The uploaded document exceeds the 25 MB limit.")
            chunks.append(chunk)
    finally:
        await file.close()
    return b"".join(chunks)


def _delete_temporary_upload(storage_key: str | None) -> None:
    """Best-effort cleanup that must never hide the original upload failure."""
    if not storage_key:
        return
    try:
        storage.delete(storage_key)
    except Exception:
        # Cleanup must not replace the original upload failure. Deployments
        # should separately alert on orphaned objects and reconcile private storage.
        pass


@app.post("/api/upload")
async def upload_document(
    file: UploadFile = File(...),
    assessment_id: str | None = Query(default=None),
    institution_id: str | None = Query(default=None),
    framework_id: str | None = Query(default=None),
    framework_edition: str | None = Query(default=None),
    criterion_id: str | None = Query(default=None),
    title: str | None = Query(default=None, max_length=300),
    source_reference: str | None = Query(default=None, max_length=1_000),
    collection_date: str | None = Query(default=None, max_length=30),
    reporting_period: str | None = Query(default=None, max_length=100),
    provenance: str | None = Query(default=None, max_length=2_000),
    limitations: str | None = Query(default=None, max_length=2_000),
    session: str | None = Cookie(default=None, alias=SESSION_COOKIE),
):
    user = current_user(session)
    institution_id = selected_institution(user["id"], institution_id)
    if any(value is not None for value in (framework_id, framework_edition, criterion_id)):
        if not (framework_id and framework_edition and criterion_id):
            raise HTTPException(status_code=422, detail="Framework, edition, and criterion must be supplied together.")
        if FRAMEWORK_EDITIONS.get(framework_id) != framework_edition:
            raise HTTPException(status_code=422, detail="Framework edition is not registered.")
        if criterion_id not in FRAMEWORK_DEFINITIONS[framework_id].criteria:
            raise HTTPException(status_code=422, detail="Criterion is not registered for this framework.")
    filename = file.filename or ""
    extension = Path(filename).suffix.lower()
    if extension not in SUPPORTED_EXTENSIONS:
        raise HTTPException(status_code=415, detail="Only PDF, DOCX, and TXT files are supported.")

    content = await _read_upload_limited(file)
    if not content:
        raise HTTPException(status_code=400, detail="The uploaded document is empty.")
    _validate_upload_content(extension, content)

    storage_key = None
    checksum = None
    try:
        storage_key, checksum = storage.save(content, extension)
    except OSError as error:
        raise HTTPException(
            status_code=503, detail="Private document storage is unavailable."
        ) from error

    try:
        scan = malware_scanner.scan(storage.root / storage_key)
    except Exception as error:
        _delete_temporary_upload(storage_key)
        raise HTTPException(
            status_code=503, detail="Malware scanning is unavailable."
        ) from error

    if scan.status == "infected":
        _delete_temporary_upload(storage_key)
        raise HTTPException(status_code=422, detail="The uploaded document failed malware scanning.")
    if scan.status != "clean":
        _delete_temporary_upload(storage_key)
        raise HTTPException(status_code=503, detail="Malware scanning is unavailable.")

    try:
        blocks = extract_blocks_isolated(filename, content)
    except ParserWorkerUnavailableError as error:
        _delete_temporary_upload(storage_key)
        raise HTTPException(
            status_code=503, detail="The document parsing service is unavailable."
        ) from error
    except Exception as error:
        # Parser libraries can raise format-specific exceptions outside the
        # common ValueError/RuntimeError hierarchy. Fail closed and clean up.
        _delete_temporary_upload(storage_key)
        raise HTTPException(
            status_code=422, detail="The document could not be extracted."
        ) from error

    if not blocks:
        _delete_temporary_upload(storage_key)
        raise HTTPException(status_code=422, detail="The document contains no extractable text.")

    created_assessment = False
    try:
        document_id = str(uuid4())
        if not assessment_id:
            assessment_id = database.create_assessment(user["id"], institution_id, "document_extracted")
            created_assessment = True
        passages = segment_blocks(blocks, document_id, filename)
        warnings = []
        matches = []
        model_path = os.getenv("WURI_SBERT_MODEL_PATH")
        model_artifact_available = has_local_sentence_transformer_artifact(model_path)
        if model_artifact_available:
            try:
                from sentence_transformers import SentenceTransformer
                model = SentenceTransformer(model_path, local_files_only=True)
                matches = retrieve_matches(passages, model=model)
            except Exception:
                model_artifact_available = False
                warnings.append("Semantic retrieval is unavailable; the configured local model artifact could not be loaded.")
        else:
            warnings.append("Semantic retrieval is unavailable; no valid local model artifact is configured.")

        assessment_status = determine_status(
            has_passages=bool(passages),
            has_matches=bool(matches),
            model_artifact_available=model_artifact_available,
        )
        document = {
            "document_id": document_id,
            "filename": filename,
            "file_type": extension.lstrip("."),
            "file_size": len(content),
            "checksum": checksum,
            "storage_key": storage_key,
            "extraction_status": "success",
            "title": title or filename,
            "source_reference": source_reference,
            "collection_date": collection_date,
            "reporting_period": reporting_period,
            "provenance": provenance,
            "limitations": limitations,
            "authorization_status": "unknown",
            "research_permission_status": "unknown",
            "malware_scan_status": scan.status,
            "malware_scanned_at": datetime.now(timezone.utc).isoformat(),
            "malware_scanner": scan.scanner,
            "mapping": (
                {"framework_id": framework_id, "framework_edition": framework_edition,
                 "criterion_id": criterion_id}
                if framework_id else None
            ),
        }
        database.persist_document(
            user["id"], institution_id, assessment_id, document,
            [passage.as_dict() for passage in passages],
            [match.as_dict() for match in matches],
        )
    except Exception as error:
        _delete_temporary_upload(storage_key)
        if created_assessment and assessment_id:
            try:
                database.remove_empty_assessment(user["id"], assessment_id)
            except Exception:
                pass
        raise HTTPException(
            status_code=500, detail="The document could not be persisted."
        ) from error

    return {
        "document": {
            "document_id": document_id,
            "filename": filename,
            "file_type": extension.lstrip("."),
            "extraction_status": "success",
            "extraction_method": sorted({block.extraction_method for block in blocks}),
        },
        "passages": [passage.as_dict() for passage in passages],
        "matches": [match.as_dict() for match in matches],
        "warnings": warnings,
        "processing_status": "evidence_extracted" if not matches else "indicator_matches_retrieved",
        "readiness_assessment_status": "not_implemented",
        "assessment_status": assessment_status.as_dict(),
        "assessment_id": assessment_id,
    }


@app.get("/api/assessments")
def list_assessments(session: str | None = Cookie(default=None, alias=SESSION_COOKIE)):
    user = current_user(session)
    return {"assessments": [dict(row) for row in database.assessments(user["id"])]}


@app.get("/api/assessments/{assessment_id}")
def get_assessment(assessment_id: str, session: str | None = Cookie(default=None, alias=SESSION_COOKIE)):
    user = current_user(session)
    detail = database.assessment_detail(user["id"], assessment_id)
    if not detail:
        raise HTTPException(status_code=404, detail="Assessment not found.")
    return detail


@app.get("/api/documents/{document_id}/download")
def download_document(document_id: str, session: str | None = Cookie(default=None, alias=SESSION_COOKIE)):
    user = current_user(session)
    with database.connection() as connection:
        row = connection.execute(
            """SELECT d.filename, d.file_type, d.storage_key
               FROM documents d JOIN institution_memberships m ON m.institution_id = d.institution_id
               WHERE d.id = ? AND m.user_id = ? AND m.status = 'active'""",
            (document_id, user["id"]),
        ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Document not found.")
    try:
        content = storage.read(row["storage_key"])
    except (OSError, ValueError) as error:
        raise HTTPException(status_code=404, detail="Document content is unavailable.") from error
    with database.connection() as connection:
        connection.execute(
            """INSERT INTO audit_events
               (id, institution_id, user_id, event_type, metadata_json)
               SELECT lower(hex(randomblob(16))), institution_id, ?, 'document.downloaded', ?
               FROM documents WHERE id = ?""",
            (user["id"], json.dumps({"document_id": document_id}), document_id),
        )
    safe_filename = Path(row["filename"]).name
    download_name = quote(safe_filename, safe="")
    return Response(
        content=content,
        media_type="application/octet-stream",
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{download_name}"},
    )


@app.get("/api/institutions/{institution_id}/documents")
def list_institution_documents(
    institution_id: str,
    session: str | None = Cookie(default=None, alias=SESSION_COOKIE),
):
    user = current_user(session)
    with database.connection() as connection:
        rows = connection.execute(
            """SELECT d.id, d.filename, d.title, d.file_type, d.file_size, d.checksum,
                      d.extraction_status, d.authorization_status,
                      d.research_permission_status, d.review_status,
                      d.source_reference, d.collection_date, d.reporting_period,
                      d.provenance, d.limitations, d.created_at,
                      m.framework_id, m.framework_edition, m.criterion_id
               FROM documents d
               JOIN institution_memberships im ON im.institution_id = d.institution_id
               LEFT JOIN document_framework_mappings m ON m.document_id = d.id
               WHERE d.institution_id = ? AND im.user_id = ? AND im.status = 'active'
               ORDER BY d.created_at DESC, d.id, m.criterion_id""",
            (institution_id, user["id"]),
        ).fetchall()
    if not rows and not any(
        row["id"] == institution_id for row in database.institutions_for_user(user["id"])
    ):
        raise HTTPException(status_code=403, detail="Institution access denied.")
    return {"institution_id": institution_id, "documents": [dict(row) for row in rows]}


@app.patch("/api/documents/{document_id}")
def update_document_metadata(
    document_id: str,
    request: DocumentMetadataRequest,
    session: str | None = Cookie(default=None, alias=SESSION_COOKIE),
):
    user = current_user(session)
    try:
        database.update_document_metadata(
            user["id"], document_id,
            {key: value for key, value in request.model_dump().items() if value is not None},
        )
    except PermissionError as error:
        raise HTTPException(status_code=403, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    return {"updated": True, "document_id": document_id}


@app.delete("/api/documents/{document_id}")
def delete_document(
    document_id: str,
    session: str | None = Cookie(default=None, alias=SESSION_COOKIE),
):
    user = current_user(session)
    try:
        storage_key = database.delete_document(user["id"], document_id)
        storage.delete(storage_key)
    except PermissionError as error:
        raise HTTPException(status_code=403, detail=str(error)) from error
    except (OSError, ValueError) as error:
        raise HTTPException(status_code=500, detail="Document storage cleanup failed.") from error
    return {"deleted": True, "document_id": document_id}


@app.get("/api/research/validation/status")
def research_validation_status(
    institution_id: str | None = Query(default=None),
    session: str | None = Cookie(default=None, alias=SESSION_COOKIE),
):
    user = current_user(session)
    institution_id = authorized_research_institution(user["id"], institution_id)
    counts = database.research_counts(user["id"], institution_id)
    datasets = [dict(row) for row in database.research_datasets(user["id"], institution_id)]
    for dataset in datasets:
        dataset["split_summary"] = json.loads(dataset.pop("split_summary_json"))

    source_root = Path(__file__).resolve().parents[2]
    enhanced_path = os.getenv("WURI_ENHANCED_MODEL_PATH")
    available = set()
    if counts["expert_labeled_examples"]:
        available.add("genuine_expert_labeled_dataset")
    if counts["expert_eqam_dimensions"] == 5 and counts["expert_eqam_min_raters_per_dimension"] >= 2:
        available.add("expert_eqam_ratings")
    if counts["expert_reference_dimensions"] >= 5 and counts["expert_reference_min_raters_per_dimension"] >= 2:
        available.add("expert_reference_readiness_scores")
    if counts["locked_thresholds"]:
        available.add("locked_validation_threshold")
    if len(verified_frameworks()) == len(FRAMEWORK_DEFINITIONS):
        available.add("verified_framework_criteria_and_weights")
    if (
        has_local_sentence_transformer_artifact(enhanced_path)
        and os.getenv("WURI_ENHANCED_MODEL_VERSION")
    ):
        available.add("enhanced_model_artifact")
    if (
        has_local_sentence_transformer_artifact(os.getenv("WURI_BASELINE_MODEL_PATH"))
        and os.getenv("WURI_BASELINE_MODEL_VERSION")
    ):
        available.add("baseline_model_version")
    if os.getenv("WURI_XAI_EVALUATION_INSTRUMENT") and counts["xai_dimensions"] >= 6:
        available.add("xai_evaluation_instrument_and_ratings")

    missing_global = []
    if not counts["expert_labeled_examples"]:
        missing_global.append("genuine expert-labeled evidence-indicator dataset")
    if not (source_root / "UniversityRanking_V3.1.docx").is_file():
        missing_global.append("authoritative dissertation Chapter 3 source for protocol verification")
    if "enhanced_model_artifact" not in available:
        missing_global.append("trained enhanced Sentence-BERT model artifact and training provenance")
    if "baseline_model_version" not in available:
        missing_global.append("explicit conventional baseline model version")
    if not counts["expert_eqam_ratings"] or counts["expert_eqam_min_raters_per_dimension"] < 2:
        missing_global.append("at least two independent expert raters covering all five EQAM dimensions")
    if counts["expert_reference_dimensions"] < 5 or counts["expert_reference_min_raters_per_dimension"] < 2:
        missing_global.append("two independent expert references for RRS across all frameworks plus ARRS")
    if "verified_framework_criteria_and_weights" not in available:
        missing_global.append("verified framework criteria and weight provenance")
    if "approved_criterion_aggregation" not in available:
        missing_global.append("approved criterion aggregation policy")
    if "approved_conventional_weights" not in available:
        missing_global.append("verified conventional AHP/TOPSIS baseline configuration")

    ablations = ablation_statuses(available)
    overall_state = (
        "blocked_missing_data"
        if any(item["status"] == "blocked_missing_data" for item in ablations)
        else "not_implemented"
        if any(item["status"] == "not_implemented" for item in ablations)
        else "not_implemented"
    )
    readiness_results = counts["completed_experiments"] > 0
    retrieval_results = counts["completed_retrieval_experiments"] > 0
    return {
        "state": "completed_with_limitations" if readiness_results or retrieval_results else overall_state,
        "empirical_results_available": readiness_results,
        "retrieval_results_available": retrieval_results,
        "empirical_result_note": (
            "Held-out retrieval results are reported separately and do not constitute completed readiness scoring. "
            "Only authorized completed readiness runs count as readiness results; software fixtures are tests only."
        ),
        "dataset_counts": counts,
        "datasets": datasets,
        "ablations": ablations,
        "missing_prerequisites": missing_global,
        "protocol_source": {
            "file": "UniversityRanking_V3.1.docx",
            "available_in_workspace": (source_root / "UniversityRanking_V3.1.docx").is_file(),
            "status": "must_verify_chapter_3_before_research_claims",
        },
        "implemented_metrics": [
            "accuracy", "macro_precision", "macro_recall", "macro_f1",
            "precision@1", "precision@3", "precision@5",
            "recall@1", "recall@3", "recall@5",
            "mae", "rmse", "spearman_rho", "icc_2_1", "exact_agreement", "cohen_kappa",
            "paired_score_test", "eqam_rss_regression_diagnostics", "xai_traceability_audit",
        ],
        "research_runs": [
            _serialize_research_experiment(row)
            for row in database.research_experiments(user["id"], institution_id)
        ],
    }


def _serialize_research_experiment(row):
    result = {key: row[key] for key in row.keys()}
    for key in (
        "configuration_json", "result_json", "warnings_json", "preflight_json",
        "sample_counts_json", "evaluation_config_json",
    ):
        value = result.get(key)
        if value:
            result[key.removesuffix("_json")] = json.loads(value)
        result.pop(key, None)
    if result.get("execution_state") == "failed":
        result["error_summary"] = "Experiment execution failed; no results were stored."
    return result


@app.get("/api/research/experiments/preflight")
def research_experiment_preflight(
    dataset_id: str = Query(min_length=1, max_length=100),
    configuration_id: Literal["A0", "A1", "A2", "A3", "A4"] = Query(),
    evaluation_scope: Literal["retrieval", "readiness"] = Query(default="retrieval"),
    institution_id: str | None = Query(default=None),
    session: str | None = Cookie(default=None, alias=SESSION_COOKIE),
):
    user = current_user(session)
    institution_id = authorized_research_institution(user["id"], institution_id)
    runner = ResearchExperimentRunner(database)
    try:
        report = runner.preflight(
            user["id"], institution_id, dataset_id, configuration_id, evaluation_scope
        )
    except PermissionError as error:
        raise HTTPException(status_code=403, detail="Institution research access denied.") from error
    if report["dataset"] is None:
        raise HTTPException(status_code=404, detail="Research dataset not found.")
    return report


@app.post("/api/research/experiments", status_code=201)
def run_research_experiment(
    request: ResearchExperimentRequest,
    institution_id: str | None = Query(default=None),
    session: str | None = Cookie(default=None, alias=SESSION_COOKIE),
):
    user = current_user(session)
    institution_id = selected_institution(user["id"], institution_id)
    runner = ResearchExperimentRunner(database)
    try:
        report = runner.preflight(
            user["id"], institution_id, request.dataset_id, request.configuration_id,
            request.evaluation_scope,
        )
        if report["dataset"] is None:
            raise HTTPException(status_code=404, detail="Research dataset not found.")
        return runner.run(
            user["id"], institution_id, request.dataset_id,
            request.configuration_id, request.random_seed, request.evaluation_scope,
        )
    except PermissionError as error:
        raise HTTPException(status_code=403, detail="Institution research access denied.") from error
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error


@app.get("/api/research/experiments/{experiment_id}")
def get_research_experiment(
    experiment_id: str,
    institution_id: str | None = Query(default=None),
    session: str | None = Cookie(default=None, alias=SESSION_COOKIE),
):
    user = current_user(session)
    institution_id = authorized_research_institution(user["id"], institution_id)
    try:
        result = database.get_research_experiment(user["id"], institution_id, experiment_id)
    except PermissionError as error:
        raise HTTPException(status_code=403, detail="Institution research access denied.") from error
    if result is None:
        raise HTTPException(status_code=404, detail="Research experiment not found.")
    return _serialize_research_experiment(result)


@app.post("/api/research/datasets", status_code=201)
def create_research_dataset(
    request: ResearchDatasetRequest,
    institution_id: str | None = Query(default=None),
    session: str | None = Cookie(default=None, alias=SESSION_COOKIE),
):
    user = current_user(session)
    institution_id = selected_institution(user["id"], institution_id)
    records = [record.model_dump() for record in request.records]
    for record in records:
        if record["framework"] not in FRAMEWORK_INDICATORS:
            raise HTTPException(status_code=422, detail="Unsupported framework identifier.")
        if record["indicator"] not in FRAMEWORK_INDICATORS[record["framework"]]:
            raise HTTPException(status_code=422, detail="Unsupported indicator identifier.")
        if str(record["label"]).strip().casefold() not in {
            "true", "false", "1", "0", "yes", "no",
            "positive", "negative", "relevant", "not_relevant",
        }:
            raise HTTPException(status_code=422, detail="Research relevance labels must be binary.")
        if not record["annotation_version"]:
            record["annotation_version"] = request.annotation_version
        if record.get("model_prediction") is not None:
            record["original_prediction_json"] = json.dumps(record.pop("model_prediction"), sort_keys=True)
    if sum(len((record.get("text") or "").encode("utf-8")) for record in records) > 10 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Research dataset evidence text exceeds the 10 MB import limit.")
    try:
        records = database.prepare_research_records(user["id"], institution_id, records)
    except PermissionError as error:
        raise HTTPException(status_code=403, detail="The dataset references inaccessible institutional evidence.") from error
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    try:
        split = split_evidence_dataset(
            records,
            request.dataset_version,
            request.random_seed,
        )
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    try:
        dataset_id = database.create_research_dataset(
            user["id"],
            institution_id,
            {
                "dataset_version": request.dataset_version,
                "annotation_version": request.annotation_version,
                "provenance": request.provenance,
            },
            records,
            split.as_dict(),
        )
    except PermissionError as error:
        raise HTTPException(status_code=403, detail="The dataset references inaccessible institutional evidence.") from error
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    except sqlite3.IntegrityError as error:
        raise HTTPException(status_code=409, detail="Dataset version already exists or contains conflicting records.") from error
    return {"dataset_id": dataset_id, "split": split.as_dict(), "empirical_result": False}


@app.post("/api/research/datasets/import", status_code=201)
async def import_research_dataset_file(
    file: UploadFile = File(...),
    dataset_version: str = Form(min_length=1, max_length=100),
    annotation_version: str = Form(min_length=1, max_length=100),
    provenance: str = Form(min_length=1, max_length=2_000),
    random_seed: int = Form(),
    institution_id: str | None = Query(default=None),
    session: str | None = Cookie(default=None, alias=SESSION_COOKIE),
):
    user = current_user(session)
    institution_id = selected_institution(user["id"], institution_id)
    filename = file.filename or ""
    extension = Path(filename).suffix.lower()
    if extension not in {".csv", ".jsonl"}:
        raise HTTPException(status_code=415, detail="Only CSV and JSONL research files are supported.")
    content = await file.read(MAX_IMPORT_BYTES + 1)
    if not content:
        raise HTTPException(status_code=400, detail="The research import file is empty.")
    if len(content) > MAX_IMPORT_BYTES:
        raise HTTPException(status_code=413, detail="Research import exceeds the 25 MB limit.")

    storage_key = None
    import_id = None
    try:
        storage_key, checksum = storage.save(content, extension)
        import_id = database.create_research_import(
            user["id"], institution_id, filename, storage_key, checksum, len(content)
        )
    except (OSError, PermissionError, sqlite3.Error, ValueError):
        if storage_key:
            storage.delete(storage_key)
        raise

    records, errors = parse_research_upload(filename, content)
    normalized, schema_errors = validate_research_records(
        records,
        dataset_version=dataset_version,
        annotation_version=annotation_version,
        provenance=provenance,
    )
    errors.extend(schema_errors)
    report = {
        "format": extension[1:],
        "parsed_record_count": len(records),
        "accepted_record_count": 0,
        "errors": errors,
    }
    if errors:
        database.finish_research_import(import_id, institution_id, "rejected", report)
        raise HTTPException(
            status_code=422,
            detail={"import_id": import_id, "status": "rejected", "report": report},
        )
    try:
        prepared = database.prepare_research_records(user["id"], institution_id, normalized)
    except (PermissionError, ValueError) as error:
        source_errors = []
        for record in normalized:
            try:
                database.prepare_research_records(user["id"], institution_id, [record])
            except (PermissionError, ValueError) as row_error:
                source_errors.append({
                    "line": record.get("source_line"),
                    "example_id": record["example_id"],
                    "message": (
                        "A referenced evidence passage is not accessible."
                        if isinstance(row_error, PermissionError) else str(row_error)
                    ),
                })
        report["errors"].extend(source_errors or [{"line": None, "message": str(error)}])
        database.finish_research_import(import_id, institution_id, "rejected", report)
        raise HTTPException(
            status_code=403 if isinstance(error, PermissionError) else 422,
            detail={"import_id": import_id, "status": "rejected", "report": report},
        ) from error
    try:
        split = split_evidence_dataset(prepared, dataset_version, random_seed)
        dataset_id = database.create_research_dataset(
            user["id"],
            institution_id,
            {
                "dataset_version": dataset_version,
                "annotation_version": annotation_version,
                "provenance": provenance,
            },
            prepared,
            split.as_dict(),
        )
    except (ValueError, sqlite3.IntegrityError) as error:
        report["errors"].append({"line": None, "message": str(error)})
        database.finish_research_import(import_id, institution_id, "rejected", report)
        raise HTTPException(
            status_code=422 if isinstance(error, ValueError) else 409,
            detail={"import_id": import_id, "status": "rejected", "report": report},
        ) from error
    report.update({
        "accepted_record_count": len(prepared),
        "dataset_id": dataset_id,
        "dataset_version": dataset_version,
        "split_counts": split.counts,
        "split_version": split.split_version,
        "sha256": checksum,
    })
    database.finish_research_import(import_id, institution_id, "accepted", report, dataset_id)
    return {
        "import_id": import_id,
        "dataset_id": dataset_id,
        "status": "accepted",
        "report": report,
        "split": split.as_dict(),
        "empirical_result": False,
    }


@app.get("/api/research/imports/{import_id}")
def get_research_import_report(
    import_id: str,
    institution_id: str | None = Query(default=None),
    session: str | None = Cookie(default=None, alias=SESSION_COOKIE),
):
    user = current_user(session)
    institution_id = authorized_research_institution(user["id"], institution_id)
    try:
        report = database.get_research_import(user["id"], institution_id, import_id)
    except PermissionError as error:
        raise HTTPException(status_code=403, detail="Institution research access denied.") from error
    if report is None:
        raise HTTPException(status_code=404, detail="Research import not found.")
    return report


@app.get("/api/research/datasets/{dataset_id}/annotations")
def get_annotation_review_queue(
    dataset_id: str,
    institution_id: str | None = Query(default=None),
    session: str | None = Cookie(default=None, alias=SESSION_COOKIE),
):
    user = current_user(session)
    institution_id = authorized_research_institution(user["id"], institution_id)
    try:
        queue = database.annotation_review_queue(user["id"], institution_id, dataset_id)
    except PermissionError as error:
        raise HTTPException(status_code=403, detail="Institution research access denied.") from error
    except ValueError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    return {"dataset_id": dataset_id, "annotations": queue}


@app.post("/api/research/expert-qualifications", status_code=201)
def record_expert_qualification(
    request: ExpertQualificationRequest,
    institution_id: str | None = Query(default=None),
    session: str | None = Cookie(default=None, alias=SESSION_COOKIE),
):
    user = current_user(session)
    institution_id = selected_institution(user["id"], institution_id)
    try:
        database.verify_expert_qualification(
            user["id"], institution_id, request.expert_id,
            request.qualification_reference, request.note, request.status,
        )
    except PermissionError as error:
        raise HTTPException(status_code=403, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    return {"expert_id": request.expert_id, "qualification_status": request.status}


@app.post("/api/research/consensus-procedures", status_code=201)
def record_consensus_procedure(
    request: ConsensusProcedureRequest,
    institution_id: str | None = Query(default=None),
    session: str | None = Cookie(default=None, alias=SESSION_COOKIE),
):
    user = current_user(session)
    institution_id = selected_institution(user["id"], institution_id)
    try:
        database.register_consensus_procedure(
            user["id"], institution_id, request.procedure_id,
            request.procedure_version, request.approval_reference,
            request.approving_authority, request.rationale,
        )
    except PermissionError as error:
        raise HTTPException(status_code=403, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    except sqlite3.IntegrityError as error:
        raise HTTPException(status_code=409, detail="This consensus procedure version is already recorded.") from error
    return {
        "procedure_id": request.procedure_id,
        "procedure_version": request.procedure_version,
        "status": "approval_reference_recorded",
    }


@app.post("/api/research/datasets/{dataset_id}/expert-panel-reviews", status_code=201)
def submit_expert_panel_reviews(
    dataset_id: str,
    request: ExpertPanelReviewsRequest,
    institution_id: str | None = Query(default=None),
    session: str | None = Cookie(default=None, alias=SESSION_COOKIE),
):
    user = current_user(session)
    institution_id = selected_institution(user["id"], institution_id)
    try:
        count = database.submit_expert_panel_reviews(
            user["id"], institution_id, dataset_id,
            [review.model_dump() for review in request.reviews],
        )
    except PermissionError as error:
        raise HTTPException(status_code=403, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    except sqlite3.IntegrityError as error:
        raise HTTPException(status_code=409, detail="An expert panel judgment conflicts with an existing judgment.") from error
    return {
        "dataset_id": dataset_id,
        "stored_review_count": count,
        "status": "independent_judgment_recorded",
    }


@app.get("/api/research/datasets/{dataset_id}/expert-panel-agreement")
def get_expert_panel_agreement(
    dataset_id: str,
    institution_id: str | None = Query(default=None),
    session: str | None = Cookie(default=None, alias=SESSION_COOKIE),
):
    user = current_user(session)
    institution_id = authorized_research_institution(user["id"], institution_id)
    try:
        return database.expert_panel_agreement(user["id"], institution_id, dataset_id)
    except PermissionError as error:
        raise HTTPException(status_code=403, detail=str(error)) from error


@app.post("/api/research/datasets/{dataset_id}/expert-panel-consensus", status_code=201)
def record_expert_panel_consensus(
    dataset_id: str,
    request: ExpertPanelConsensusRequest,
    institution_id: str | None = Query(default=None),
    session: str | None = Cookie(default=None, alias=SESSION_COOKIE),
):
    user = current_user(session)
    institution_id = selected_institution(user["id"], institution_id)
    try:
        database.record_expert_panel_consensus(
            user["id"], institution_id, dataset_id, request.example_id,
            request.final_label, request.resolution, request.procedure_id,
            request.procedure_version, request.note,
        )
    except PermissionError as error:
        raise HTTPException(status_code=403, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    except sqlite3.IntegrityError as error:
        raise HTTPException(status_code=409, detail="A consensus record already exists for this case.") from error
    return {"dataset_id": dataset_id, "example_id": request.example_id, "status": request.resolution}


@app.post("/api/research/datasets/{dataset_id}/annotation-reviews", status_code=201)
def submit_annotation_reviews(
    dataset_id: str,
    request: AnnotationReviewsRequest,
    institution_id: str | None = Query(default=None),
    session: str | None = Cookie(default=None, alias=SESSION_COOKIE),
):
    user = current_user(session)
    institution_id = selected_institution(user["id"], institution_id)
    try:
        count = database.submit_annotation_reviews(
            user["id"], institution_id, dataset_id,
            [review.model_dump() for review in request.reviews],
        )
    except PermissionError as error:
        raise HTTPException(status_code=403, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    except sqlite3.IntegrityError as error:
        raise HTTPException(status_code=409, detail="An annotation review conflicts with an existing review.") from error
    return {"dataset_id": dataset_id, "stored_review_count": count}


@app.get("/api/research/datasets")
def list_research_datasets(
    institution_id: str | None = Query(default=None),
    session: str | None = Cookie(default=None, alias=SESSION_COOKIE),
):
    user = current_user(session)
    institution_id = authorized_research_institution(user["id"], institution_id)
    return {
        "datasets": [dict(row) for row in database.research_datasets(user["id"], institution_id)]
    }


@app.post("/api/research/datasets/{dataset_id}/review")
def review_research_dataset(
    dataset_id: str,
    request: DatasetReviewRequest,
    institution_id: str | None = Query(default=None),
    session: str | None = Cookie(default=None, alias=SESSION_COOKIE),
):
    user = current_user(session)
    institution_id = authorized_research_institution(user["id"], institution_id)
    try:
        database.review_research_dataset(
            user["id"], institution_id, dataset_id, request.decision, request.note,
            source_use_clearance_reference=request.source_use_clearance_reference,
            institutional_approval_reference=request.institutional_approval_reference,
        )
    except PermissionError as error:
        raise HTTPException(status_code=403, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    return {"dataset_id": dataset_id, "verification_status": request.decision}


@app.post("/api/research/datasets/{dataset_id}/expert-ratings", status_code=201)
def add_expert_ratings(
    dataset_id: str,
    request: ExpertRatingsRequest,
    institution_id: str | None = Query(default=None),
    session: str | None = Cookie(default=None, alias=SESSION_COOKIE),
):
    user = current_user(session)
    institution_id = selected_institution(user["id"], institution_id)
    ratings = [rating.model_dump() for rating in request.ratings]
    try:
        for rating in ratings:
            dimension = rating["dimension"]
            minimum = rating["rating_scale"].get("minimum")
            maximum = rating["rating_scale"].get("maximum")
            if (
                minimum is None or maximum is None or not math.isfinite(minimum)
                or not math.isfinite(maximum) or minimum >= maximum
                or not math.isfinite(rating["score"])
            ):
                raise ValueError("Each expert rating must specify a valid minimum and maximum scale.")
            if not minimum <= rating["score"] <= maximum:
                raise ValueError("Expert rating score falls outside its declared rating scale.")
            valid_dimensions = {
                "semantic_relevance", "model_confidence", "evidence_completeness",
                "source_reliability", "evidence_strength", "arrs",
                "rrs:WURI", "rrs:THE", "rrs:QS", "rrs:UI GreenMetric",
                "xai:clarity", "xai:interpretability", "xai:traceability",
                "xai:usefulness", "xai:numerical_consistency", "xai:user_confidence",
            }
            if dimension not in valid_dimensions:
                raise ValueError("Unsupported expert rating dimension.")
            if dimension in {
                "semantic_relevance", "model_confidence", "evidence_completeness",
                "source_reliability", "evidence_strength",
            } and (minimum < 0 or maximum > 1):
                raise ValueError("EQAM expert ratings must use a scale within [0, 1].")
            if dimension == "arrs" or dimension.startswith("rrs:"):
                if minimum < 0 or maximum > 100:
                    raise ValueError("Expert RRS/ARRS references must use a scale within [0, 100].")
        rating_ids = database.persist_expert_ratings(user["id"], institution_id, dataset_id, ratings)
    except PermissionError as error:
        raise HTTPException(status_code=403, detail="Research dataset access denied.") from error
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    except sqlite3.IntegrityError as error:
        raise HTTPException(status_code=409, detail="An expert rating with this case, expert, and dimension already exists.") from error
    return {
        "stored_rating_count": len(ratings),
        "rating_ids": rating_ids,
        "status": "submitted_for_independent_review",
    }


@app.post("/api/research/expert-ratings/{rating_id}/review")
def review_expert_rating(
    rating_id: str,
    request: DatasetReviewRequest,
    institution_id: str | None = Query(default=None),
    session: str | None = Cookie(default=None, alias=SESSION_COOKIE),
):
    user = current_user(session)
    institution_id = authorized_research_institution(user["id"], institution_id)
    try:
        database.review_expert_rating(
            user["id"], institution_id, rating_id, request.decision, request.note
        )
    except PermissionError as error:
        raise HTTPException(status_code=403, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    return {"rating_id": rating_id, "review_status": request.decision}


@app.post("/api/research/experiments/{experiment_id}/lock-threshold")
def lock_research_threshold(
    experiment_id: str,
    institution_id: str | None = Query(default=None),
    session: str | None = Cookie(default=None, alias=SESSION_COOKIE),
):
    user = current_user(session)
    institution_id = selected_institution(user["id"], institution_id)
    try:
        result = database.lock_threshold_from_validation_predictions(
            user["id"], institution_id, experiment_id
        )
    except PermissionError as error:
        raise HTTPException(status_code=403, detail="Research experiment access denied.") from error
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    except sqlite3.IntegrityError as error:
        raise HTTPException(status_code=409, detail="A validation threshold is already locked for this dataset and metric.") from error
    return result
