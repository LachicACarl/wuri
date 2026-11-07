from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
import re
from typing import Iterable

import docx
import fitz


MAX_PASSAGE_CHARS = 1200
PASSAGE_OVERLAP_CHARS = 120


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


def validate_content(filename: str, content: bytes) -> None:
    extension = Path(filename).suffix.lower()
    if extension == ".pdf" and not content.startswith(b"%PDF"):
        raise ValueError("The file does not contain a valid PDF signature.")
    if extension == ".docx" and not content.startswith(b"PK"):
        raise ValueError("The file does not contain a valid DOCX package.")
    if extension == ".txt":
        content.decode("utf-8")


def _extract_pdf(content: bytes) -> list[ExtractedBlock]:
    blocks = []
    with fitz.open(stream=content, filetype="pdf") as document:
        for page_index, page in enumerate(document):
            text = _clean_text(page.get_text())
            if text:
                blocks.append(ExtractedBlock(text, page_index + 1, None, None, None, "pdf_text_extraction"))
    return blocks


def _iter_docx_blocks(document):
    from docx.document import Document as DocumentObject
    from docx.table import Table, _Cell
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
    document = docx.Document(BytesIO(content))
    blocks = []
    current_section = None
    for block in _iter_docx_blocks(document):
        if hasattr(block, "text"):
            text = _clean_text(block.text)
            style_name = getattr(getattr(block, "style", None), "name", "") or ""
            if text:
                if "heading" in style_name.lower():
                    current_section = text
                blocks.append(ExtractedBlock(text, None, current_section, None, None, "docx_paragraph_extraction"))
        else:
            rows = [" | ".join(_clean_text(cell.text) for cell in row.cells) for row in block.rows]
            text = _clean_text("\n".join(row for row in rows if row))
            if text:
                blocks.append(ExtractedBlock(text, None, current_section, None, None, "docx_table_extraction"))
    return blocks


def _extract_txt(content: bytes) -> list[ExtractedBlock]:
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
