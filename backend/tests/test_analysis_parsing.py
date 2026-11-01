"""
Unit tests for the parts of the pipeline that do not need the model or a database.
Run from backend/: python -m unittest discover -s tests
"""

import unittest

from src.services.llm import parse_json_text
from src.services.analysis_store import (
    ground_citation, map_severity, map_risk_type, map_role, map_date_type,
    parse_amount, parse_iso_date,
)
from src.services.rag import _word_chunks
from src.utils.text import locate_quote
from src.models.risk import RiskSeverity, RiskType
from src.models.contract import PartyRole, DateType


class ParseJsonTextTests(unittest.TestCase):
    def test_plain_json(self):
        self.assertEqual(parse_json_text('{"a": 1}'), {"a": 1})

    def test_fenced_json(self):
        self.assertEqual(parse_json_text('```json\n{"a": [1, 2]}\n```'), {"a": [1, 2]})

    def test_json_with_prose(self):
        self.assertEqual(parse_json_text('Here you go: {"ok": true} hope that helps'), {"ok": True})

    def test_invalid_raises(self):
        with self.assertRaises(ValueError):
            parse_json_text('{"a": ')


class MappingTests(unittest.TestCase):
    def test_severity(self):
        self.assertEqual(map_severity("High"), RiskSeverity.high)
        self.assertEqual(map_severity("severe"), RiskSeverity.critical)
        self.assertEqual(map_severity("whatever"), RiskSeverity.medium)

    def test_risk_type(self):
        self.assertEqual(map_risk_type("missing clause"), RiskType.missing_clause)
        self.assertEqual(map_risk_type(None), RiskType.non_standard)

    def test_role_and_dates(self):
        self.assertEqual(map_role("Service Provider"), PartyRole.vendor)
        self.assertEqual(map_role("customer"), PartyRole.client)
        self.assertEqual(map_date_type("effective date"), DateType.effective_date)

    def test_amount_and_date(self):
        self.assertEqual(parse_amount("USD 12,500.50"), 12500.5)
        self.assertIsNone(parse_amount(None))
        self.assertEqual(parse_iso_date("2025-10-01").year, 2025)
        self.assertIsNone(parse_iso_date("upon signature"))


class CitationTests(unittest.TestCase):
    chunks = {"c_00001": {"chunk_id": "c_00001", "page": 3, "text": "Either party may terminate this Agreement   for convenience on 30 days notice."}}

    def test_verbatim_quote_is_kept(self):
        c = ground_citation("c_00001", "terminate this Agreement for convenience", self.chunks)
        self.assertEqual(c["page"], 3)
        self.assertEqual(c["snippet"], "terminate this Agreement for convenience")

    def test_invented_quote_falls_back_to_chunk_text(self):
        c = ground_citation("c_00001", "may terminate at any time without notice", self.chunks)
        self.assertTrue(c["snippet"].startswith("Either party may terminate"))

    def test_curly_quotes_and_case_still_match(self):
        chunks = {"c_1": {"chunk_id": "c_1", "page": 2, "text": "as of the last date executed below (“Effective Date”) by and between"}}
        c = ground_citation("c_1", 'Last date executed below ("Effective Date")', chunks)
        self.assertEqual(c["snippet"], "last date executed below (“Effective Date”)")

    def test_paraphrased_quote_snaps_to_source_span(self):
        snippet = locate_quote(
            "Either party may terminate this Agreement for convenience upon ninety (90) days prior written notice to the other party.",
            "may terminate this Agreement for convenience upon 90 days written notice",
        )
        self.assertIsNotNone(snippet)
        self.assertTrue(snippet.startswith("may terminate this Agreement for convenience"))

    def test_unknown_chunk(self):
        self.assertIsNone(ground_citation("c_99999", "x", self.chunks)["chunk_id"])


class ChunkingTests(unittest.TestCase):
    def test_pages_are_one_based(self):
        text = " ".join(["alpha"] * 300) + " " + " ".join(["beta"] * 300)
        offsets = [0, len(" ".join(["alpha"] * 300)) + 1]
        chunks = _word_chunks(text, approx_tokens=220, overlap=30, page_offsets=offsets)
        self.assertEqual(chunks[0]["page"], 1)
        self.assertEqual(chunks[-1]["page"], 2)

    def test_no_offsets_means_unknown_page(self):
        self.assertIsNone(_word_chunks("one two three")[0]["page"])


if __name__ == "__main__":
    unittest.main()
