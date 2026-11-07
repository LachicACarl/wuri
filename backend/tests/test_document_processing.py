import unittest
from io import BytesIO

import docx
import fitz

from app.document_processing import ExtractedBlock, extract_blocks, segment_blocks
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
