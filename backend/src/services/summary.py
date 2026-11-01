"""
Summary Service
Generates comprehensive summaries of contracts.

This implementation:
- Uses Gemini 1.5 Pro (JSON mode) to produce a compact, business-friendly summary
- Accepts extracted_data & risks to ground the summary
- Returns a structured dict ready for the dashboard

Return shape:
{
  "summary": str,            # <= ~2200 chars executive summary
  "purpose": str,
  "scope": str,
  "key_obligations": { "<party>": [str, ...], ... },
  "highlights": [str, ...]
}
"""

from typing import Dict, Optional, Any, List
import json

import google.generativeai as genai
from src.config.settings import get_settings

settings = get_settings()

def _to_str_list(seq, maxn=None):
    out = []
    for x in (seq or []):
        if isinstance(x, str):
            s = x.strip()
        elif isinstance(x, dict):
            # try common keys first; fall back to JSON-ish preview
            cand = x.get("name") or x.get("title") or x.get("text") or x.get("value")
            s = str(cand) if cand is not None else json.dumps(x, ensure_ascii=False)[:120]
        else:
            s = str(x)
        if s:
            out.append(s)
        if maxn and len(out) >= maxn:
            break
    return out

def _chunk_text(text: str, approx_tokens: int = 650, stride: int = 100):
    words = (text or "").split()
    if not words:
        return []
    chunks, step, i, cidx = [], max(1, approx_tokens - stride), 0, 0
    while i < len(words):
        seg = " ".join(words[i : i + approx_tokens])
        if seg.strip():
            chunks.append({"chunk_id": f"c_{cidx:05d}", "page": 0, "section": None, "text": seg})
            cidx += 1
        i += step
    return chunks


SYSTEM_SUMMARY_INSTRUCTIONS = (
    "You are an AI contract analyst. Produce a concise, business-friendly executive summary of the contract. "
    "Use ONLY the provided text and extracted data. Do not speculate. "
    "Keep the executive summary <= 2200 characters. "
    "Structure the output as JSON with keys: summary, purpose, scope, key_obligations, highlights. "
    "key_obligations is a mapping from party name to a list of short obligations. "
    "highlights is a list (5–10 items) of the most important points (dates, fees, SLAs, risks). "
    "If a field is truly unknown, use a short placeholder like 'Unknown'."
)


class SummaryService:
    """
    Service for generating contract summaries using AI.
    """

    def __init__(self):
        if settings.gemini_api_key:
            genai.configure(api_key=settings.gemini_api_key)
            self.model = genai.GenerativeModel(
                model_name=settings.gemini_model,
                generation_config={"response_mime_type": "application/json"}
            )
        else:
            self.model = None

    async def generate_summary(
        self,
        contract_text: str,
        extracted_data: Optional[Dict] = None,
        risks: Optional[Dict] = None
    ) -> Dict:
        """
        Generate a compact, one-page-style summary.
        Args:
          contract_text: full contract text (string)
          extracted_data: dict from extraction_service.extract_all(...)
          risks: dict from risk_service.analyze_risks(...)
        Returns:
          dict: {summary, purpose, scope, key_obligations, highlights}
        """
        if not self.model:
            return self._fallback_summary(extracted_data, risks)

        chunks = _chunk_text(contract_text, approx_tokens=650, stride=100)[:40]

        payload = {
            "extracted": extracted_data or {},
            "risks": risks or {},
            "chunks": chunks
        }

        try:
            prompt_parts = [
                {"text": SYSTEM_SUMMARY_INSTRUCTIONS},
                {"text": json.dumps(payload, ensure_ascii=False)}
            ]
            resp = self.model.generate_content(
                contents=[{"role": "user", "parts": prompt_parts}]
            )
            out = json.loads(resp.text)

            return {
                "summary": _ensure_str(out.get("summary"), default="Summary unavailable."),
                "purpose": _ensure_str(out.get("purpose"), default=_infer_purpose(extracted_data)),
                "scope": _ensure_str(out.get("scope"), default=_infer_scope(extracted_data)),
                "key_obligations": _ensure_obligations(out.get("key_obligations"), extracted_data),
                "highlights": _ensure_highlights(out.get("highlights"), extracted_data, risks),
            }

        except Exception as e:
            fail = self._fallback_summary(extracted_data, risks)
            fail["summary"] = f"{fail['summary']} [Note: LLM error {type(e).__name__}]"
            return fail

    async def generate_executive_summary(self, contract_text: str) -> str:
        if not self.model:
            return "Executive summary unavailable - AI service not configured."
        res = await self.generate_summary(contract_text=contract_text)
        return res.get("summary", "Executive summary unavailable.")

    async def extract_purpose(self, contract_text: str) -> str:
        if not self.model:
            return "Purpose unknown - AI service not configured."
        res = await self.generate_summary(contract_text=contract_text)
        return res.get("purpose", "Unknown")

    async def extract_scope(self, contract_text: str) -> str:
        if not self.model:
            return "Scope unknown - AI service not configured."
        res = await self.generate_summary(contract_text=contract_text)
        return res.get("scope", "Unknown")

    async def identify_key_obligations(self, contract_text: str, parties: list = None) -> Dict:
        if not self.model:
            return {}
        res = await self.generate_summary(contract_text=contract_text)
        return res.get("key_obligations", {})

    async def generate_highlights(
        self,
        contract_text: str,
        extracted_data: Optional[Dict] = None
    ) -> list:
        if not self.model:
            return ["AI service not configured"]
        res = await self.generate_summary(contract_text=contract_text, extracted_data=extracted_data)
        return res.get("highlights", [])

    async def generate_one_page_summary(
        self,
        contract_text: str,
        extracted_data: Optional[Dict] = None,
        risks: Optional[Dict] = None
    ) -> Dict:
        return await self.generate_summary(
            contract_text=contract_text,
            extracted_data=extracted_data,
            risks=risks
        )

    def _fallback_summary(self, extracted: Optional[Dict], risks: Optional[Dict]) -> Dict:
        parties = _summarize_parties(extracted)
        key_dates = _summarize_dates(extracted)
        money = _summarize_money(extracted)
        law = _summarize_law(extracted)
        top_risks = _summarize_risks(risks)

        summary = (
            f"{parties} {key_dates} {money} {law} "
            f"{' Top risks: ' + top_risks if top_risks else ''}".strip()
        )
        return {
            "summary": summary or "Summary unavailable.",
            "purpose": _infer_purpose(extracted),
            "scope": _infer_scope(extracted),
            "key_obligations": _infer_obligations(extracted),
            "highlights": _default_highlights(extracted, risks),
        }

def _ensure_str(val, default="Unknown"):
    return val if isinstance(val, str) and val.strip() else default

def _ensure_obligations(obj, extracted):
    if isinstance(obj, dict) and obj:
        return obj
    return _infer_obligations(extracted)

def _ensure_highlights(arr, extracted, risks):
    if isinstance(arr, list) and arr:
        return [str(x) for x in arr if isinstance(x, (str, int, float))][:10]
    return _default_highlights(extracted, risks)


def _summarize_parties(extracted: Optional[Dict]) -> str:
    if not extracted:
        return ""
    parties = extracted.get("parties") or []
    if not parties:
        return ""
    names = []
    for p in parties[:3]:
        name = p.get("name") or ""
        role = p.get("role") or ""
        if name and role:
            names.append(f"{name} ({role})")
        elif name:
            names.append(name)
    if not names:
        return ""
    return "Parties: " + ", ".join(names) + "."

def _summarize_dates(extracted: Optional[Dict]) -> str:
    if not extracted:
        return ""
    dates = extracted.get("dates") or {}
    eff = dates.get("effective_date", {}) if isinstance(dates, dict) else {}
    exp = dates.get("expiration_date", {}) if isinstance(dates, dict) else {}
    parts = []
    if isinstance(eff, dict) and (eff.get("value") or eff.get("raw")):
        parts.append(f"Effective: {eff.get('value') or eff.get('raw')}.")
    if isinstance(exp, dict) and (exp.get("value") or exp.get("raw")):
        parts.append(f"Expires: {exp.get('value') or exp.get('raw')}.")
    return " ".join(parts)

def _summarize_money(extracted: Optional[Dict]) -> str:
    if not extracted:
        return ""
    ft = extracted.get("financial_terms") or {}
    currency = ft.get("currency") or ""
    amts = ft.get("amounts") or []
    if amts:
        raws = []
        for a in amts[:2]:
            raw = a.get("raw")
            val = a.get("value")
            label = a.get("label")
            if raw:
                raws.append(raw)
            elif val is not None:
                raws.append(f"{currency} {val}" if currency else f"{val}")
            elif label:
                raws.append(label)
        if raws:
            return "Financial: " + ", ".join(raws) + "."
    return ""

def _summarize_law(extracted: Optional[Dict]) -> str:
    if not extracted:
        return ""
    gl = extracted.get("governing_law") or {}
    if isinstance(gl, dict):
        j = gl.get("jurisdiction")
        v = gl.get("venue")
        if j and v:
            return f"Governing law: {j}; venue: {v}."
        if j:
            return f"Governing law: {j}."
    return ""

def _summarize_risks(risks: Optional[Dict]) -> str:
    if not risks:
        return ""
    tops = []
    for bucket in ("risks", "non_standard", "missing_clauses"):
        items = risks.get(bucket) or []
        if not isinstance(items, list):
            continue
        for r in items[:2]: 
            title = r.get("title") or r.get("clause") or "Risk"
            sev = r.get("severity", "")
            tops.append(f"{title}" + (f" ({sev})" if sev else ""))
    return "; ".join(tops[:4])

def _infer_purpose(extracted: Optional[Dict]) -> str:
    if not extracted:
        return "Unknown"
    deliverables = _to_str_list(extracted.get("deliverables"), maxn=3)
    if deliverables:
        return "Provision of: " + ", ".join(deliverables)
    obligations = extracted.get("obligations") or []
    if obligations:
        return "Define obligations and services between parties."
    return "Unknown"

def _infer_scope(extracted: Optional[Dict]) -> str:
    if not extracted:
        return "Unknown"
    defs = extracted.get("definitions_consistency") or {}
    if defs.get("undefined_terms"):
        return "Scope defined with some undefined terms."
    return "Scope of services and obligations as per agreement."

def _infer_obligations(extracted: Optional[Dict]) -> Dict[str, List[str]]:
    by_party = {}
    if not extracted:
        return by_party
    for ob in extracted.get("obligations") or []:
        if isinstance(ob, dict):
            party = ob.get("party") or "Unspecified Party"
            text  = ob.get("text") or ob.get("title") or ob.get("name") or ""
        else:
            party, text = "Unspecified Party", str(ob)
        if not text:
            continue
        by_party.setdefault(party, [])
        if len(by_party[party]) < 5:
            by_party[party].append(text[:300])
    return by_party

def _default_highlights(extracted: Optional[Dict], risks: Optional[Dict]) -> List[str]:
    hl = []
    if extracted:
        d = extracted.get("dates") or {}
        for k in ("effective_date", "expiration_date"):
            v = d.get(k) or {}
            if isinstance(v, dict) and (v.get("value") or v.get("raw")):
                hl.append(f"{k.replace('_',' ').title()}: {v.get('value') or v.get('raw')}")
        ft = extracted.get("financial_terms") or {}
        if ft.get("amounts"):
            hl.append("Key financial amounts detected.")
        gl = extracted.get("governing_law") or {}
        if gl.get("jurisdiction"):
            hl.append(f"Governing law: {gl.get('jurisdiction')}")
    if risks and (risks.get("overall") or risks.get("risks") or risks.get("non_standard") or risks.get("missing_clauses")):
        ov = risks.get("overall") or {}
        lvl = ov.get("level")
        if lvl:
            hl.append(f"Overall risk level: {lvl}")
        tops = (risks.get("risks") or []) + (risks.get("non_standard") or [])
        if tops:
            hl.append(f"Top risk: {tops[0].get('title', 'Risk')}")
    return hl[:10]

summary_service = SummaryService()