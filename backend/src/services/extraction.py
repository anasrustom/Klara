"""
Extraction Service
- Hybrid extraction: heuristics + Gemini JSON-mode
- Returns structured, evidence-backed data for dashboard & downstream risk analysis
"""

from typing import Dict, List, Optional, Any
import json
import re
import math

import google.generativeai as genai

from src.config.settings import get_settings

settings = get_settings()


_CURRENCY_RE = r"(?:USD|QAR|SAR|AED|EUR|GBP|\$|€|£|ر\.ق)"
_MONEY_RE = rf"{_CURRENCY_RE}\s?\d{{1,3}}(?:,\d{{3}})*(?:\.\d+)?"
_LAW_HINT = re.compile(r"(?is)Governing\s+Law[:\-]?\s*(.+?)(?:\.|\n)")
_PARTIES_BLOCK = re.compile(
    r"(?is)(?:This\s+Agreement\s+is\s+made\s+by\s+and\s+between|This\s+Agreement\s+is\s+between)(.+?)(?:\.\s|NOW,?\s+THEREFORE|WHEREAS)"
)

def _find_money(full_text: str) -> List[str]:
    return re.findall(_MONEY_RE, full_text or "")[:25]

def _find_governing_law(full_text: str) -> Optional[str]:
    m = _LAW_HINT.search(full_text or "")
    return m.group(1).strip() if m else None


def _chunk_text(text: str, approx_tokens: int = 600, stride: int = 90) -> List[Dict[str, Any]]:
    """
    Approximate token chunking by words. Keeps context via overlap.
    """
    words = (text or "").split()
    if not words:
        return []
    chunks = []
    step = max(1, approx_tokens - stride)
    i = 0
    cidx = 0
    while i < len(words):
        seg = " ".join(words[i : i + approx_tokens])
        if seg.strip():
            chunks.append({
                "chunk_id": f"c_{cidx:05d}",
                "page": 0,
                "section": None,
                "text": seg
            })
            cidx += 1
        i += step
    return chunks


EXTRACTION_SCHEMA = {
    "type": "object",
    "properties": {
        "doc_id": {"type": "string"},
        "language": {"type": "string", "enum": ["en", "ar"]},
        "parties": {"type": "array", "items": {"type": "object"}},
        "dates": {"type": "object"},
        "governing_law": {"type": "object"},
        "financial_terms": {"type": "object"},
        "obligations": {"type": "array"},
        "deliverables": {"type": "array"},
        "definitions_consistency": {"type": "object"},
        "confidence_overall": {"type": "number"}
    },
    "required": ["doc_id", "language", "parties", "dates"]
}

SYSTEM_EXTRACT_INSTRUCTIONS = (
    "You are an AI contract analyst. Extract key fields from the provided contract CHUNKS. "
    "Return ONLY valid JSON matching the provided schema. "
    "For each field include evidence chunk_ids where possible. "
    "Normalize dates to ISO-8601 when possible and also return raw string if present. "
    "If uncertain, set the value to null and confidence < 0.5."
)


class ExtractionService:
    """
    Service for extracting structured data from contract text using Gemini.
    """

    def __init__(self):
        if not settings.gemini_api_key:
            self.model = None
            return

        genai.configure(api_key=settings.gemini_api_key)

        self.model = genai.GenerativeModel(
            model_name=settings.gemini_model,
            generation_config={"response_mime_type": "application/json"}
        )

    async def extract_all(self, doc_id: str, text: str, language: str = "en") -> Dict:
        """
        Main entry: extracts all key info.
        Args:
          doc_id: unique id (we pass contract.id as string)
          text: full contract text
          language: 'en' or 'ar'
        Returns:
          dict with fields:
           - parties, dates, governing_law, financial_terms, obligations, deliverables,
             definitions_consistency, confidence_overall
        """
        if not self.model:
            return {
                "doc_id": doc_id,
                "language": language if language in ("en", "ar") else "en",
                "parties": [],
                "dates": {},
                "governing_law": None,
                "financial_terms": {},
                "obligations": [],
                "deliverables": [],
                "definitions_consistency": {},
                "confidence_overall": 0.0
            }

        chunks = _chunk_text(text, approx_tokens=600, stride=90)
        llm_chunks = chunks[:40]

        payload = {
            "schema": EXTRACTION_SCHEMA,
            "language": language if language in ("en", "ar") else "en",
            "doc_id": doc_id,
            "chunks": llm_chunks
        }

        try:
            prompt_parts = [
                {"text": SYSTEM_EXTRACT_INSTRUCTIONS},
                {"text": json.dumps(payload, ensure_ascii=False)}
            ]
            resp = self.model.generate_content(contents=[{"role": "user", "parts": prompt_parts}])
            data = json.loads(resp.text)
        except Exception as e:
            data = {
                "doc_id": doc_id,
                "language": language if language in ("en", "ar") else "en",
                "parties": [],
                "dates": {},
                "governing_law": None,
                "financial_terms": {},
                "obligations": [],
                "deliverables": [],
                "definitions_consistency": {},
                "confidence_overall": 0.0,
                "error": f"gemini_error: {type(e).__name__}: {str(e)}"
            }

        full_text = text or ""

        try:
            money_mentions = _find_money(full_text)
            if money_mentions:
                ft = data.setdefault("financial_terms", {})
                ft.setdefault("amounts", [])
                seen = set()
                for m in money_mentions:
                    if m in seen:
                        continue
                    seen.add(m)
                    ft["amounts"].append({"label": "Detected", "value": None, "raw": m})
        except Exception:
            pass

        try:
            if not data.get("governing_law"):
                gl = _find_governing_law(full_text)
                if gl:
                    data["governing_law"] = {"jurisdiction": gl, "confidence": 0.5}
        except Exception:
            pass

        try:
            if not data.get("parties"):
                m = _PARTIES_BLOCK.search(full_text)
                if m:
                    block = " ".join(m.group(1).split())[:500]
                    data["parties"] = [{"name": block, "role": None, "address": None, "confidence": 0.4, "evidence_chunks": []}]
        except Exception:
            pass

        data.setdefault("doc_id", doc_id)
        data.setdefault("language", language if language in ("en", "ar") else "en")
        data.setdefault("parties", [])
        data.setdefault("dates", {})
        data.setdefault("financial_terms", {})
        data.setdefault("obligations", [])
        data.setdefault("deliverables", [])
        data.setdefault("definitions_consistency", {})
        data.setdefault("confidence_overall", 0.5 if data.get("parties") or data.get("dates") else 0.3)

        return data

    async def extract_parties(self, contract_text: str) -> List[Dict]:
        parties = []
        try:
            m = _PARTIES_BLOCK.search(contract_text or "")
            if m:
                block = " ".join(m.group(1).split())
                parties.append({"name": block[:500], "role": None, "address": None, "confidence": 0.4})
        except Exception:
            pass
        return parties

    async def extract_dates(self, contract_text: str) -> List[Dict]:
        return []

    async def extract_financial_terms(self, contract_text: str) -> List[Dict]:
        return [{"raw": m} for m in _find_money(contract_text or "")]
    
    async def extract_governing_law(self, contract_text: str) -> Optional[str]:
        return _find_governing_law(contract_text or "")
    
    async def extract_jurisdiction(self, contract_text: str) -> Optional[str]:
        return None


extraction_service = ExtractionService()