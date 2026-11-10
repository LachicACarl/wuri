from dataclasses import dataclass
from io import BytesIO
import json
import os
from pathlib import Path, PurePosixPath, PureWindowsPath
import subprocess
import sys
import re
import zipfile
import zlib
from typing import Iterable

import docx
import fitz


MAX_PASSAGE_CHARS = 1200
PASSAGE_OVERLAP_CHARS = 120

# Parsing ceilings deliberately sit below the 25 MiB upload bound. They cap
# object counts and extracted output even where an input is highly compressed.
MAX_PDF_PAGES = 500
MAX_PDF_TEXT_CHARS = 5_000_000
MAX_DOCX_ENTRIES = 2_000
MAX_DOCX_UNCOMPRESSED_BYTES = 50 * 1024 * 1024
MAX_DOCX_ENTRY_BYTES = 20 * 1024 * 1024
MAX_DOCX_COMPRESSION_RATIO = 100
MAX_DOCX_TEXT_CHARS = 5_000_000
MAX_TEXT_CHARS = 5_000_000


class ParserWorkerUnavailableError(RuntimeError):
    """The isolated parser process could not be started safely."""


@dataclass(frozen=True)
class ExtractedBlock:
    text: str
    page_number: int | None
    section_title: str | None
    start_offset: int | None
    end_offset: int | None
    extraction_method: str


@dataclass(frozen=True)
class Passage:
    passage_id: str
    document_id: str
    filename: str
    passage_index: int
    text: str
    page_number: int | None
    section_title: str | None
    start_offset: int | None
    end_offset: int | None
    extraction_method: str
    extraction_status: str = "success"

    def as_dict(self) -> dict:
        return {
            "passage_id": self.passage_id,
            "document_id": self.document_id,
            "filename": self.filename,
            "passage_index": self.passage_index,
            "text": self.text,
            "page_number": self.page_number,
            "section_title": self.section_title,
            "start_offset": self.start_offset,
            "end_offset": self.end_offset,
            "extraction_method": self.extraction_method,
            "extraction_status": self.extraction_status,
        }


def _clean_text(text: str) -> str:
    return re.sub(r"[ \t]+", " ", text).strip()


def _validate_docx_archive(content: bytes) -> None:
    """Validate DOCX ZIP metadata before python-docx opens/decompresses it."""
    try:
        with zipfile.ZipFile(BytesIO(content)) as archive:
            entries = archive.infolist()
            if len(entries) > MAX_DOCX_ENTRIES:
                raise ValueError("DOCX package contains too many archive entries.")
            total_uncompressed = 0
            required = {"[Content_Types].xml", "word/document.xml"}
            names = set()
            for entry in entries:
                name = entry.filename
                path = PurePosixPath(name)
                windows_path = PureWindowsPath(name)
                if (
                    not name or name.startswith(("/", "\\\\"))
                    or "\\" in name or path.is_absolute()
                    or windows_path.is_absolute() or windows_path.drive
                    or any(part in {"", ".", ".."} for part in path.parts)
                    or any(part in {"", ".", ".."} for part in windows_path.parts)
                ):
                    raise ValueError("DOCX package contains an unsafe archive path.")
                if name in names:
                    raise ValueError("DOCX package contains duplicate archive paths.")
                names.add(name)
                if entry.flag_bits & 0x1:
                    raise ValueError("Encrypted DOCX archive entries are not supported.")
                if entry.file_size < 0 or entry.compress_size < 0:
                    raise ValueError("DOCX package contains invalid archive metadata.")
                if entry.compress_type not in {zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED}:
                    raise ValueError("DOCX package uses an unsupported compression method.")
                if entry.file_size > MAX_DOCX_ENTRY_BYTES:
                    raise ValueError("DOCX archive entry exceeds the uncompressed size limit.")
                total_uncompressed += entry.file_size
                if total_uncompressed > MAX_DOCX_UNCOMPRESSED_BYTES:
                    raise ValueError("DOCX package exceeds the total uncompressed size limit.")
                if entry.file_size > 0:
                    if entry.compress_size == 0:
                        raise ValueError("DOCX package contains an invalid compression ratio.")
                    ratio = entry.file_size / entry.compress_size
                    if ratio > MAX_DOCX_COMPRESSION_RATIO:
                        raise ValueError("DOCX package exceeds the allowed compression ratio.")
            if not required.issubset(names):
                raise ValueError("DOCX package is missing required document parts.")
            # Test CRCs and actually decompress each entry only after metadata
            # ceilings have been checked. The aggregate expanded bytes are capped.
            for entry in entries:
                with archive.open(entry, "r") as stream:
                    remaining = entry.file_size
                    while remaining:
                        chunk = stream.read(min(1024 * 1024, remaining))
                        if not chunk:
                            raise ValueError("DOCX package contains a truncated archive entry.")
                        remaining -= len(chunk)
                    if stream.read(1):
                        raise ValueError("DOCX package entry exceeds its declared size.")
    except zipfile.BadZipFile as error:
        raise ValueError("The DOCX package is not a valid ZIP archive.") from error
    except (OSError, RuntimeError, EOFError, zlib.error) as error:
        raise ValueError("The DOCX package is malformed or unreadable.") from error


def validate_content(filename: str, content: bytes) -> None:
    extension = Path(filename).suffix.lower()
    if extension == ".pdf":
        if not content.startswith(b"%PDF-"):
            raise ValueError("The file does not contain a valid PDF signature.")
        try:
            with fitz.open(stream=content, filetype="pdf") as document:
                if document.page_count > MAX_PDF_PAGES:
                    raise ValueError("PDF exceeds the maximum page count.")
                if document.is_encrypted:
                    raise ValueError("Password-protected PDF files are not supported.")
        except ValueError:
            raise
        except Exception as error:
            # MuPDF parser exceptions vary across supported PyMuPDF releases.
            raise ValueError("The PDF file is malformed or unreadable.") from error
    elif extension == ".docx":
        if not content.startswith(b"PK"):
            raise ValueError("The file does not contain a valid DOCX package.")
        _validate_docx_archive(content)
    elif extension == ".txt":
        if len(content) > MAX_TEXT_CHARS:
            raise ValueError("TXT document exceeds the extracted text size limit.")
        content.decode("utf-8")


def _extract_pdf(content: bytes) -> list[ExtractedBlock]:
    blocks = []
    total_chars = 0
    with fitz.open(stream=content, filetype="pdf") as document:
        if document.page_count > MAX_PDF_PAGES:
            raise ValueError("PDF exceeds the maximum page count.")
        if document.is_encrypted:
            raise ValueError("Password-protected PDF files are not supported.")
        for page_index, page in enumerate(document):
            text = _clean_text(page.get_text())
            total_chars += len(text)
            if total_chars > MAX_PDF_TEXT_CHARS:
                raise ValueError("PDF extracted text exceeds the configured limit.")
            if text:
                blocks.append(ExtractedBlock(text, page_index + 1, None, None, None, "pdf_text_extraction"))
    return blocks


def _iter_docx_blocks(document):
    from docx.table import Table
    from docx.text.paragraph import Paragraph
    from docx.oxml.text.paragraph import CT_P
    from docx.oxml.table import CT_Tbl

    parent = document.element.body
    for child in parent.iterchildren():
        if isinstance(child, CT_P):
            yield Paragraph(child, document)
        elif isinstance(child, CT_Tbl):
            yield Table(child, document)


def _extract_docx(content: bytes) -> list[ExtractedBlock]:
    _validate_docx_archive(content)
    document = docx.Document(BytesIO(content))
    blocks = []
    total_chars = 0
    current_section = None
    for block in _iter_docx_blocks(document):
        if hasattr(block, "text"):
            text = _clean_text(block.text)
            style_name = getattr(getattr(block, "style", None), "name", "") or ""
            if text:
                total_chars += len(text)
                if "heading" in style_name.lower():
                    current_section = text
                blocks.append(ExtractedBlock(text, None, current_section, None, None, "docx_paragraph_extraction"))
        else:
            rows = []
            for row in block.rows:
                cell_texts = []
                for cell in row.cells:
                    cell_text = _clean_text(cell.text)
                    total_chars += len(cell_text)
                    cell_texts.append(cell_text)
                    if total_chars > MAX_DOCX_TEXT_CHARS:
                        raise ValueError("DOCX extracted text exceeds the configured limit.")
                rows.append(" | ".join(cell_texts))
            text = _clean_text("\\n".join(row for row in rows if row))
            if text:
                blocks.append(ExtractedBlock(text, None, current_section, None, None, "docx_table_extraction"))
        if total_chars > MAX_DOCX_TEXT_CHARS:
            raise ValueError("DOCX extracted text exceeds the configured limit.")
    return blocks


def _extract_txt(content: bytes) -> list[ExtractedBlock]:
    if len(content) > MAX_TEXT_CHARS:
        raise ValueError("TXT document exceeds the extracted text size limit.")
    text = content.decode("utf-8")
    blocks = []
    offset = 0
    for raw_line in text.splitlines(keepends=True):
        cleaned = _clean_text(raw_line)
        if cleaned:
            start = text.find(cleaned, offset)
            end = start + len(cleaned)
            blocks.append(ExtractedBlock(cleaned, None, None, start, end, "txt_extraction"))
        offset += len(raw_line)
    return blocks


def extract_blocks(filename: str, content: bytes) -> list[ExtractedBlock]:
    extension = Path(filename).suffix.lower()
    validate_content(filename, content)
    if extension == ".pdf":
        return _extract_pdf(content)
    if extension == ".docx":
        return _extract_docx(content)
    if extension == ".txt":
        return _extract_txt(content)
    raise ValueError("Unsupported document format.")


def extract_blocks_isolated(
    filename: str,
    content: bytes,
    timeout_seconds: float = 25,
) -> list[ExtractedBlock]:
    """Parse a document in a separate, time-limited worker process.

    POSIX workers apply CPU, address-space, file-descriptor, and core-dump
    limits before importing PDF/DOCX parser libraries. Windows development
    uses the wall-clock timeout; deployment readiness remains blocked unless
    the POSIX resource limits or an equivalent platform sandbox are present.
    """
    if len(content) > 25 * 1024 * 1024:
        raise ValueError("Document exceeds the parser worker input limit.")

    environment = {
        key: value
        for key, value in os.environ.items()
        if key in {
            "PATH", "SYSTEMROOT", "WINDIR", "TEMP", "TMP", "TMPDIR",
            "APPDATA",
            "LD_LIBRARY_PATH", "DYLD_LIBRARY_PATH", "LANG", "LC_ALL",
        }
    }
    environment["PYTHONIOENCODING"] = "utf-8"
    backend_root = Path(__file__).resolve().parents[1]
    command = [
        sys.executable, "-m", "app.document_parser_worker", filename,
    ]
    try:
        completed = subprocess.run(
            command,
            input=content,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            cwd=backend_root,
            env=environment,
            timeout=timeout_seconds,
            check=False,
        )
    except subprocess.TimeoutExpired as error:
        raise TimeoutError("Document parsing exceeded the execution time limit.") from error
    except OSError as error:
        raise ParserWorkerUnavailableError(
            "The isolated document parser could not be started."
        ) from error

    try:
        result = json.loads(completed.stdout.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ParserWorkerUnavailableError(
            "The isolated document parser returned an invalid response."
        ) from error

    if completed.returncode != 0:
        message = result.get("error", "The isolated document parser failed.")
        if result.get("error_type") == "ValueError":
            raise ValueError(message)
        if result.get("error_type") == "WorkerLimitsUnavailable":
            raise ParserWorkerUnavailableError(message)
        raise RuntimeError(message)

    if os.name == "posix" and result.get("resource_limits_applied") is not True:
        raise ParserWorkerUnavailableError("Parser worker resource limits were not applied.")

    try:
        return [ExtractedBlock(**block) for block in result["blocks"]]
    except (KeyError, TypeError, ValueError) as error:
        raise ParserWorkerUnavailableError(
            "The isolated document parser returned invalid blocks."
        ) from error


def _split_long_text(text: str, max_chars: int, overlap_chars: int) -> Iterable[str]:
    start = 0
    while start < len(text):
        end = min(start + max_chars, len(text))
        if end < len(text):
            boundary = text.rfind(" ", start, end)
            if boundary > start + max_chars // 2:
                end = boundary
        piece = text[start:end].strip()
        if piece:
            yield piece
        if end >= len(text):
            break
        start = max(start + 1, end - overlap_chars)


def segment_blocks(
    blocks: Iterable[ExtractedBlock],
    document_id: str,
    filename: str,
    max_chars: int = MAX_PASSAGE_CHARS,
    overlap_chars: int = PASSAGE_OVERLAP_CHARS,
) -> list[Passage]:
    passages = []
    seen = set()
    for block in blocks:
        for text in _split_long_text(block.text, max_chars, overlap_chars):
            key = (block.page_number, block.section_title, text)
            if key in seen:
                continue
            seen.add(key)
            index = len(passages)
            passages.append(Passage(
                passage_id=f"{document_id}-PASSAGE-{index + 1:04d}",
                document_id=document_id,
                filename=filename,
                passage_index=index,
                text=text,
                page_number=block.page_number,
                section_title=block.section_title,
                start_offset=block.start_offset,
                end_offset=block.end_offset,
                extraction_method=block.extraction_method,
            ))
    return passages
