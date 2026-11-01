from typing import Dict, Any, List, Optional
import json

from src.services.rag import rag_service
from src.services.llm import json_model, generate_json, LLMError

TOPICS = [
  "parties to the agreement company customer provider",
  "effective date term expiration renewal",
  "fees payment terms invoice late fees penalties",
  "limited warranty warranty disclaimer",
  "indemnity indemnification hold harmless third-party claims",
  "limitation of liability cap aggregate carve-outs",
  "confidentiality non-disclosure NDA",
  "data protection privacy GDPR PDPL breach notice security",
  "termination for cause convenience cure period notice",
  "governing law venue arbitration seat rules language",
  "force majeure acts of god mitigation notice",
  "intellectual property ownership license background foreground",
  "assignment subcontracting change of control"
]

# Short contracts go to the model whole; longer ones by topic coverage
_SEND_ALL_MAX_CHUNKS = 40
_TOPIC_EVIDENCE_MAX = 30

_LANG_NAMES = {"en": "English", "ar": "Arabic"}

SYSTEM_ANALYZE = (
  "You are a senior contract lawyer reviewing a contract for your client. "
  "Use ONLY the provided CHUNKS of the contract. Do not speculate or invent facts. "
  "Return ONE JSON object with exactly the keys shown in OUTPUT_SHAPE. "
  "Every party, date, financial term and risk must cite the chunk_id it comes from, "
  "and `quote` must be copied verbatim from that chunk (at most 200 characters). "
  "A missing clause has no quote; cite the chunk that is closest to where it should be, or null. "
  "Use only the enum values listed. Dates must be ISO YYYY-MM-DD, or null if the contract gives no calendar date. "
  "Amounts are money figures as plain numbers without currency symbols, or null if no figure is stated. "
  "A percentage or interest rate is not an amount: set amount and currency to null and state the rate in description. "
  "Rank risks from most to least severe and focus on what a client would need to negotiate."
)

OUTPUT_SHAPE = {
  "contract": {
    "contract_type": "string, e.g. Managed Service Provider Agreement",
    "industry": "string, e.g. Technology",
    "governing_law": "string or null",
    "jurisdiction": "string or null (courts or arbitration seat)",
  },
  "summary": {
    "summary": "string, 3 to 5 sentences in plain language",
    "purpose": "string, one sentence",
    "scope": "string, one or two sentences",
    "highlights": ["string, the most important terms, max 6"],
    "key_obligations": [{"party": "string", "obligation": "string", "chunk_id": "string"}],
  },
  "parties": [{
    "name": "string", "type": "organization | individual",
    "role": "client | vendor | partner | other", "chunk_id": "string", "quote": "string",
  }],
  "dates": [{
    "type": "effective_date | expiration_date | renewal_date | milestone | other",
    "date": "YYYY-MM-DD or null", "description": "string", "chunk_id": "string", "quote": "string",
  }],
  "financial_terms": [{
    "type": "payment | penalty | deposit | other", "amount": "number or null",
    "currency": "ISO code or null", "schedule": "string or null", "description": "string",
    "chunk_id": "string", "quote": "string",
  }],
  "risks": [{
    "title": "string, short",
    "category": "missing_clause | unusual_clause | non_standard | inconsistency | compliance",
    "severity": "critical | high | medium | low",
    "description": "string, why this matters to the client",
    "recommendation": "string, the concrete change to ask for",
    "clause_reference": "string or null, e.g. Section 9.2",
    "chunk_id": "string or null", "quote": "string or null",
  }],
}

BOUNDS = {
  "parties_max": 6,
  "dates_max": 8,
  "financial_terms_max": 8,
  "risks_min": 3,
  "risks_max": 8,
  "key_obligations_max": 8,
}


class AnalyzeService:
    _MAX_OUTPUT_TOKENS = 8192

    def __init__(self):
      self.model = json_model(self._MAX_OUTPUT_TOKENS)

    async def build_evidence(self, contract_id: str) -> List[dict]:
      chunks = rag_service.get_chunks(contract_id)
      if len(chunks) <= _SEND_ALL_MAX_CHUNKS:
        return [{"chunk_id": c["chunk_id"], "page": c.get("page"), "text": c["text"]} for c in chunks]

      # Long contract: the opening chunks (parties, dates) plus RAG topic coverage
      seen, hits = set(), []
      for c in chunks[:3]:
        seen.add(c["chunk_id"])
        hits.append({"chunk_id": c["chunk_id"], "page": c.get("page"), "text": c["text"]})
      for t in TOPICS:
        for h in await rag_service.search_contract(contract_id, t, top_k=2):
          if h["chunk_id"] in seen:
            continue
          seen.add(h["chunk_id"])
          hits.append({"chunk_id": h["chunk_id"], "page": h.get("page"), "text": h["text"]})
          if len(hits) >= _TOPIC_EVIDENCE_MAX:
            break
      # Keep document order so the model reads the contract as written
      order = {c["chunk_id"]: i for i, c in enumerate(chunks)}
      return sorted(hits, key=lambda h: order.get(h["chunk_id"], 0))

    async def analyze(self, *, contract_id: str, output_language: str = "en") -> Dict[str, Any]:
      """
      One model call that returns contract metadata, summary, parties, dates,
      financial terms and risks, each tied to the chunk it came from.
      Returns {"analysis": dict, "chunks": evidence list}. Raises LLMError on failure.
      """
      if not self.model:
        raise LLMError("AI service not configured: set GEMINI_API_KEY in backend/.env")

      chunks = await self.build_evidence(contract_id)
      if not chunks:
        raise LLMError("No indexed text for this contract")

      lang = _LANG_NAMES.get(output_language, "English")
      payload = {
        "output_language": lang,
        "bounds": BOUNDS,
        "OUTPUT_SHAPE": OUTPUT_SHAPE,
        "chunks": chunks,
      }
      prompt_parts = [
        {"text": SYSTEM_ANALYZE},
        {"text": f"Write all prose fields in {lang}. Keep `quote` in the contract's original language."},
        {"text": json.dumps(payload, ensure_ascii=False)},
      ]

      data = await generate_json(self.model, prompt_parts, retries=1)
      if not isinstance(data, dict):
        raise LLMError("Model returned JSON that is not an object")
      return {"analysis": data, "chunks": chunks}

analyze_service = AnalyzeService()
