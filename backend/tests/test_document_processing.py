import subprocess
import unittest
import zipfile
from io import BytesIO
from unittest.mock import patch

import docx
import fitz

from app.document_processing import (
    MAX_DOCX_COMPRESSION_RATIO, MAX_PDF_PAGES, ExtractedBlock,
    extract_blocks, extract_blocks_isolated, segment_blocks,
)
from app.retrieval import retrieve_matches


class FakeModel:
    def encode(self, values, convert_to_tensor=True):
        return values


def fake_cosine_similarity(passages, indicators):
    return [
        [1.0 if indicator.split(",")[0].strip() in passage.lower() else 0.1 for indicator in indicators]
        for passage in passages
    ]


class DocumentProcessingTests(unittest.TestCase):
    def test_isolated_worker_extracts_text(self):
        blocks = extract_blocks_isolated("worker.txt", "Isolated parser — café".encode("utf-8"))
        self.assertEqual([block.text for block in blocks], ["Isolated parser — café"])

    def test_isolated_worker_enforces_wall_clock_timeout(self):
        with patch(
            "app.document_processing.subprocess.run",
            side_effect=subprocess.TimeoutExpired(["python", "-m", "app.document_parser_worker"], 25),
        ):
            with self.assertRaisesRegex(TimeoutError, "execution time limit"):
                extract_blocks_isolated("timeout.txt", b"synthetic", timeout_seconds=25)

    def test_txt_preserves_offsets_and_unicode(self):
        content = "Research innovation\n\nSustainability — água\n".encode()
        blocks = extract_blocks("report.txt", content)
        self.assertEqual([block.text for block in blocks], ["Research innovation", "Sustainability — água"])
        self.assertEqual(blocks[0].start_offset, 0)
        self.assertEqual(blocks[1].end_offset, len("Research innovation\n\nSustainability — água"))

    def test_docx_extracts_paragraphs_and_tables(self):
        document = docx.Document()
        document.add_heading("Research", level=1)
        document.add_paragraph("Indexed publications support the research environment.")
        table = document.add_table(rows=1, cols=2)
        table.rows[0].cells[0].text = "Metric"
        table.rows[0].cells[1].text = "Value"
        blocks = extract_blocks("report.docx", BytesIO(self._docx_bytes(document)).getvalue())
        self.assertEqual(blocks[0].section_title, "Research")
        self.assertTrue(any("Metric | Value" in block.text for block in blocks))

    def test_pdf_preserves_page_numbers(self):
        document = fitz.open()
        page = document.new_page()
        page.insert_text((72, 72), "Page one evidence")
        blocks = extract_blocks("report.pdf", document.tobytes())
        self.assertEqual(blocks[0].page_number, 1)

    def test_invalid_signature_is_rejected(self):
        with self.assertRaises(ValueError):
            extract_blocks("report.pdf", b"not a pdf")

    def test_pdf_page_limit_is_enforced_before_extraction(self):
        document = fitz.open()
        for _ in range(MAX_PDF_PAGES + 1):
            document.new_page()
        with self.assertRaisesRegex(ValueError, "maximum page count"):
            extract_blocks("too-many-pages.pdf", document.tobytes())

    def test_docx_rejects_invalid_zip_and_missing_required_parts(self):
        with self.assertRaisesRegex(ValueError, "valid ZIP archive"):
            extract_blocks("broken.docx", b"PK\x03\x04not-a-zip")
        output = BytesIO()
        with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("[Content_Types].xml", "<Types/>")
            archive.writestr("word/styles.xml", "<styles/>")
        with self.assertRaisesRegex(ValueError, "missing required"):
            extract_blocks("missing-document-part.docx", output.getvalue())

    def test_docx_rejects_excessive_compression_ratio(self):
        output = BytesIO()
        with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("[Content_Types].xml", "A" * 100_000)
            archive.writestr("word/document.xml", "<document/>")
        with self.assertRaisesRegex(ValueError, "compression ratio"):
            extract_blocks("zip-bomb.docx", output.getvalue())

    def test_docx_rejects_unsafe_archive_paths(self):
        output = BytesIO()
        with zipfile.ZipFile(output, "w") as archive:
            archive.writestr("[Content_Types].xml", "<Types/>")
            archive.writestr("word/document.xml", "<document/>")
            archive.writestr("../outside.xml", "unsafe")
        with self.assertRaisesRegex(ValueError, "unsafe archive path"):
            extract_blocks("unsafe.docx", output.getvalue())

    def test_docx_rejects_windows_absolute_and_relative_paths(self):
        unsafe_names = (
            "C:\\\\temp\\\\outside.xml",
            "word\\\\..\\\\outside.xml",
            "word\\\\document.xml",
        )
        for unsafe_name in unsafe_names:
            with self.subTest(archive_name=unsafe_name):
                output = BytesIO()
                with zipfile.ZipFile(output, "w") as archive:
                    archive.writestr("[Content_Types].xml", "<Types/>")
                    archive.writestr("word/document.xml", "<document/>")
                    archive.writestr(unsafe_name, "unsafe")
                with self.assertRaisesRegex(ValueError, "unsafe archive path"):
                    extract_blocks("windows-path.docx", output.getvalue())

    def test_segmentation_is_ordered_and_overlaps_long_text(self):
        block = ExtractedBlock("word " * 600, 2, "Evidence", None, None, "test")
        passages = segment_blocks([block], "doc-1", "report.txt", max_chars=100, overlap_chars=20)
        self.assertGreater(len(passages), 1)
        self.assertEqual([passage.passage_index for passage in passages], list(range(len(passages))))
        self.assertEqual(passages[0].page_number, 2)

    def test_retrieval_returns_traceable_top_k_matches(self):
        blocks = [ExtractedBlock("research environment grants", 3, "Research", None, None, "test")]
        passages = segment_blocks(blocks, "doc-1", "report.txt")
        catalog = {"THE": {"Research Environment": "research environment, grants"}}
        matches = retrieve_matches(
            passages,
            top_k=1,
            model=FakeModel(),
            indicator_catalog=catalog,
            cosine_similarity=fake_cosine_similarity,
        )
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0].document_id, "doc-1")
        self.assertEqual(matches[0].page_number, 3)
        self.assertGreaterEqual(matches[0].similarity, 0)

    @staticmethod
    def _docx_bytes(document):
        output = BytesIO()
        document.save(output)
        return output.getvalue()


if __name__ == "__main__":
    unittest.main()
