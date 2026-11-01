"""
Risk Analysis Service
Identifies and analyzes risks in contracts.

- Deterministic pre-checks (fast, explainable)
- Gemini JSON-mode critique (deeper legal review)
- Aggregated severity scoring
"""

from typing import List, Dict, Optional, Any
import re
import json
import math

import google.generativeai as genai
from src.config.settings import get_settings

settings = get_settings()


_HDR = re.IGNORECASE | re.DOTALL

def _has_heading(pattern: str, text: str) -> bool:
    return bool(re.search(pattern, text or "", _HDR))

def _has_liability_cap(text: str) -> bool:
    """
    Very rough detection of a limitation-of-liability section with a numerical/fee-based cap.
    """
    if not _has_heading(r"(limitation of liability|liability)", text):
        return False
    return bool(re.search(r"(cap|maximum|aggregate)\s+(?:liability|amount)|\b%\b|\bpercent\b|\bfee", text, _HDR))

def _has_confidentiality(text: str) -> bool:
    return _has_heading(r"(confidentiality|non-?disclosure|nda)", text)

def _has_indemnity(text: str) -> bool:
    return _has_heading(r"(indemnif(y|ication)|hold harmless)", text)

def _has_termination(text: str) -> bool:
    return _has_heading(r"(termination|term and termination|termination for cause|termination for convenience)", text)

def _has_dispute_resolution(text: str) -> bool:
    return _has_heading(r"(dispute resolution|arbitration|governing law|jurisdiction|venue)", text)

def _has_force_majeure(text: str) -> bool:
    return _has_heading(r"(force majeure|acts of god)", text)

def _has_ip(text: str) -> bool:
    return _has_heading(r"(intellectual property|ip ownership|ownership of work|work product)", text)

def _has_data_protection(text: str) -> bool:
    return _has_heading(r"(data protection|privacy|gdpr|pdpl|personal data|pii)", text)

def _unilateral_termination(text: str) -> bool:
    """
    Naive heuristic: looks for 'terminate for convenience' with only one party mentioned.
    """
    if not re.search(r"terminate\s+for\s+convenience", text, _HDR):
        return False
    window = 400
    for m in re.finditer(r"terminate\s+for\s+convenience", text, _HDR):
        start = max(0, m.start() - window)
        end = m.end() + window
        span = (text or "")[start:end]
        has_buyer = bool(re.search(r"(customer|client|buyer)", span, _HDR))
        has_seller = bool(re.search(r"(supplier|vendor|provider|contractor|licensor)", span, _HDR))
        if has_buyer ^ has_seller:
            return True
    return False


SYSTEM_RISK_INSTRUCTIONS = (
    "Act as a senior contracts counsel. Review the provided contract CHUNKS and the already-extracted fields. "
    "Return ONLY JSON with keys: risks, non_standard, missing_clauses. "
    "Each item should include: id, title, severity (low|medium|high), finding, evidence_chunks (list of chunk_ids), "
    "and recommendation (optional). Use only the provided text; no speculation."
)

CHECKLIST = {
    "liability": [
        "Is there a limitation of liability clause? Is there a monetary cap? Are carve-outs present (IP infringement, death/personal injury, fraud, willful misconduct, data breach)?"
    ],
    "indemnity": [
        "Is indemnity present? Is it mutual? Does it cover third-party claims and IP infringement?"
    ],
    "termination": [
        "Termination for cause with cure periods? Any unilateral termination for convenience? Effect of termination defined?"
    ],
    "confidentiality": [
        "Confidentiality/NDA present? Duration reasonable (>=2 years)? Exceptions (law, court order, independently developed, already known)?"
    ],
    "data_protection": [
        "Data protection/privacy obligations if personal data involved? Breach notice? Security measures? Reference to GDPR/PDPL if applicable?"
    ],
    "payment": [
        "Payment terms defined (due dates, late fees, invoicing, currency)? Excessive penalties?"
    ],
    "ip": [
        "Intellectual property ownership clarified (background vs foreground)? License scope? Restrictions?"
    ],
    "dispute_resolution": [
        "Governing law consistent with venue/arbitration? Seat, rules, language specified if arbitration?"
    ],
    "force_majeure": [
        "Force majeure clause present? Notice and mitigation?"
    ],
    "assignment": [
        "Assignment/subcontracting restrictions? Consent? Change of control?"
    ],
    "warranties": [
        "Reasonable limited warranties and appropriate disclaimers of implied warranties?"
    ],
    "audit": [
        "If relevant (regulated/procurement), audit/inspection rights defined?"
    ],
}


class RiskService:
    """
    Service for identifying and analyzing contract risks using AI.
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

    async def analyze_risks(
        self,
        doc_id: str,
        text: str,
        language: str = "en",
        extracted: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Hybrid risk analysis:
          1) deterministic rules over full text
          2) Gemini JSON-mode critique over top chunks (here: first ~40 chunks by order)
        Returns:
          {
            "risks": [...],
            "non_standard": [...],
            "missing_clauses": [...],
            "overall": {"score": int, "level": "low|medium|high|critical", "summary": str}
          }
        """
        full_text = text or ""
        result: Dict[str, Any] = {"risks": [], "non_standard": [], "missing_clauses": []}

        if not _has_liability_cap(full_text):
            result["risks"].append({
                "id": "risk_liability_cap_missing",
                "title": "No liability cap",
                "severity": "high",
                "finding": "Limitation of Liability is absent or no monetary cap detected.",
                "evidence_chunks": [],
                "recommendation": "Add an aggregate cap (e.g., 12x monthly fees or fees paid in the preceding 12 months) with standard carve-outs."
            })

        if not _has_confidentiality(full_text):
            result["missing_clauses"].append({
                "clause": "Confidentiality",
                "why": "Typical baseline NDA/confidentiality clause is missing; risk of uncontrolled disclosure."
            })

        if not _has_indemnity(full_text):
            result["missing_clauses"].append({
                "clause": "Indemnification",
                "why": "No indemnity for third-party claims (e.g., IP infringement)."
            })

        if not _has_termination(full_text):
            result["missing_clauses"].append({
                "clause": "Termination",
                "why": "Termination for cause with cure periods should be defined."
            })

        if not _has_force_majeure(full_text):
            result["missing_clauses"].append({
                "clause": "Force Majeure",
                "why": "Standard protection for events outside parties' control is missing."
            })

        if not _has_dispute_resolution(full_text):
            result["missing_clauses"].append({
                "clause": "Dispute Resolution / Governing Law",
                "why": "Governing law and forum/arbitration should be explicit and consistent."
            })

        if not _has_ip(full_text):
            result["missing_clauses"].append({
                "clause": "Intellectual Property",
                "why": "Ownership and license scope should be defined."
            })

        if _unilateral_termination(full_text):
            result["non_standard"].append({
                "id": "risk_unilateral_termination",
                "title": "Unilateral termination for convenience",
                "severity": "medium",
                "finding": "Termination for convenience appears to be granted to only one party.",
                "evidence_chunks": [],
                "recommendation": "Make termination for convenience mutual or remove it; define notice period and transition."
            })

        if not _has_data_protection(full_text):
            result["risks"].append({
                "id": "risk_data_protection_missing",
                "title": "Data protection/privacy obligations not found",
                "severity": "medium",
                "finding": "No clear personal data/security obligations or breach notice terms.",
                "evidence_chunks": [],
                "recommendation": "Add data protection clause (e.g., GDPR/PDPL compliance, security measures, breach notice)."
            })
        if self.model:
            llm_chunks = _simple_chunks(full_text, approx_tokens=600, stride=90)[:40]
            payload = {
                "doc_id": doc_id,
                "language": language if language in ("en", "ar") else "en",
                "extracted": extracted or {},
                "checklist": CHECKLIST,
                "chunks": llm_chunks
            }
            try:
                prompt_parts = [
                    {"text": SYSTEM_RISK_INSTRUCTIONS},
                    {"text": json.dumps(payload, ensure_ascii=False)}
                ]
                resp = self.model.generate_content(contents=[{"role": "user", "parts": prompt_parts}])
                llm_json = json.loads(resp.text)

                for k in ("risks", "non_standard", "missing_clauses"):
                    if k in llm_json and isinstance(llm_json[k], list):
                        result[k].extend(llm_json[k])

            except Exception as e:
                result["risks"].append({
                    "id": "risk_llm_error",
                    "title": "LLM analysis incomplete",
                    "severity": "low",
                    "finding": f"Gemini call failed: {type(e).__name__}: {str(e)}",
                    "evidence_chunks": [],
                    "recommendation": "Proceed with deterministic checks; retry LLM later."
                })

        overall = _score_risks(result)
        result["overall"] = overall
        return result

def _simple_chunks(text: str, approx_tokens: int = 600, stride: int = 90):
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

_SEVERITY_WEIGHTS = {"low": 10, "medium": 25, "high": 45, "critical": 70}

def _score_risks(result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Simple weighted scoring across risks + non_standard.
    missing_clauses contribute as medium by default.
    """
    score = 0
    count = 0

    def add_items(items, default_sev="medium"):
        nonlocal score, count
        for it in items or []:
            sev = (it.get("severity") or default_sev).lower()
            w = _SEVERITY_WEIGHTS.get(sev, _SEVERITY_WEIGHTS[default_sev])
            score += w
            count += 1

    add_items(result.get("risks", []), default_sev="medium")
    add_items(result.get("non_standard", []), default_sev="medium")
    miss_weighted = [{"severity": "medium", **(m if isinstance(m, dict) else {})} for m in result.get("missing_clauses", [])]
    add_items(miss_weighted, default_sev="medium")

    if count == 0:
        return {"score": 0, "level": "low", "summary": "No significant risks identified."}

    avg = min(100, int(round(score / max(1, count))))
    if avg < 20:
        level = "low"
    elif avg < 40:
        level = "medium"
    elif avg < 60:
        level = "high"
    else:
        level = "critical"

    return {
        "score": avg,
        "level": level,
        "summary": f"Aggregated risk level: {level} (score {avg}/100) across {count} findings."
    }

risk_service = RiskService()
