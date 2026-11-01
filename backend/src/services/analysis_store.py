"""
Turns the model's analysis JSON into database rows.
- Maps free-text labels onto the model enums
- Grounds every citation: the snippet shown to users is taken from the indexed
  contract text, never invented by the model
"""

from typing import Any, Dict, List, Optional
from datetime import datetime
import json
import re

from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.contract import (
    Contract, ContractParty, KeyDate, FinancialTerm,
    PartyType, PartyRole, DateType, TermType,
)
from src.models.risk import Risk, RiskSeverity, RiskType
from src.utils.text import grounded_snippet

SNIPPET_MAX = 240

_SEVERITY = {
    "critical": RiskSeverity.critical, "severe": RiskSeverity.critical,
    "high": RiskSeverity.high, "major": RiskSeverity.high,
    "medium": RiskSeverity.medium, "moderate": RiskSeverity.medium,
    "low": RiskSeverity.low, "minor": RiskSeverity.low, "info": RiskSeverity.low,
}

_RISK_TYPE = {
    "missing_clause": RiskType.missing_clause, "missing": RiskType.missing_clause,
    "unusual_clause": RiskType.unusual_clause, "unusual": RiskType.unusual_clause,
    "non_standard": RiskType.non_standard, "nonstandard": RiskType.non_standard,
    "inconsistency": RiskType.inconsistency, "inconsistent": RiskType.inconsistency,
    "compliance": RiskType.compliance, "regulatory": RiskType.compliance,
}

_ROLE = {
    "client": PartyRole.client, "customer": PartyRole.client, "buyer": PartyRole.client,
    "company": PartyRole.client, "licensee": PartyRole.client,
    "vendor": PartyRole.vendor, "provider": PartyRole.vendor, "service provider": PartyRole.vendor,
    "supplier": PartyRole.vendor, "contractor": PartyRole.vendor, "developer": PartyRole.vendor,
    "seller": PartyRole.vendor, "licensor": PartyRole.vendor, "msp": PartyRole.vendor,
    "partner": PartyRole.partner,
}

_DATE_TYPE = {d.value: d for d in DateType}
_TERM_TYPE = {t.value: t for t in TermType}


def _key(value: Any) -> str:
    return re.sub(r"[\s\-]+", "_", str(value or "").strip().lower())


def map_severity(value: Any) -> RiskSeverity:
    return _SEVERITY.get(str(value or "").strip().lower(), RiskSeverity.medium)


def map_risk_type(value: Any) -> RiskType:
    return _RISK_TYPE.get(_key(value), RiskType.non_standard)


def map_role(value: Any) -> PartyRole:
    raw = str(value or "").strip().lower().replace("_", " ")
    return _ROLE.get(raw, PartyRole.other)


def map_party_type(value: Any) -> PartyType:
    return PartyType.individual if _key(value) == "individual" else PartyType.organization


def map_date_type(value: Any) -> DateType:
    return _DATE_TYPE.get(_key(value), DateType.other)


def map_term_type(value: Any) -> TermType:
    return _TERM_TYPE.get(_key(value), TermType.other)


def parse_iso_date(value: Any) -> Optional[datetime]:
    if not value or not isinstance(value, str):
        return None
    try:
        return datetime.fromisoformat(value.strip()[:10])
    except ValueError:
        return None


def parse_amount(value: Any) -> Optional[float]:
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    cleaned = re.sub(r"[^\d.]", "", str(value))
    try:
        return float(cleaned) if cleaned else None
    except ValueError:
        return None


def ground_citation(
    chunk_id: Any, quote: Any, chunks_by_id: Dict[str, Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Resolve a model citation against the real chunks.
    Returns {chunk_id, page, snippet}; all None when the chunk_id is unknown.
    The snippet is always copied from the chunk: the span matching the model's
    quote when it can be found, otherwise the opening of the chunk.
    """
    chunk = chunks_by_id.get(str(chunk_id or "").strip())
    if not chunk:
        return {"chunk_id": None, "page": None, "snippet": None}
    snippet = grounded_snippet(chunk.get("text", ""), quote, SNIPPET_MAX)
    return {"chunk_id": chunk["chunk_id"], "page": chunk.get("page"), "snippet": snippet}


def _text(value: Any, limit: Optional[int] = None) -> Optional[str]:
    if value is None:
        return None
    s = str(value).strip()
    if not s or s.lower() in ("null", "none", "n/a"):
        return None
    return s[:limit] if limit else s


def _list(value: Any) -> List[Dict[str, Any]]:
    return [v for v in value if isinstance(v, dict)] if isinstance(value, list) else []


async def save_analysis(
    db: AsyncSession,
    contract: Contract,
    analysis: Dict[str, Any],
    chunks: List[Dict[str, Any]],
) -> None:
    """
    Replace the contract's AI-derived rows with this analysis and store the full JSON.
    Caller commits.
    """
    chunks_by_id = {c["chunk_id"]: c for c in chunks}

    meta = analysis.get("contract") if isinstance(analysis.get("contract"), dict) else {}
    summary = analysis.get("summary") if isinstance(analysis.get("summary"), dict) else {}

    contract.summary = _text(summary.get("summary"))
    contract.purpose = _text(summary.get("purpose"))
    contract.scope = _text(summary.get("scope"))
    contract.contract_type = _text(meta.get("contract_type"), 200) or contract.contract_type
    contract.industry = _text(meta.get("industry"), 100) or contract.industry
    contract.governing_law = _text(meta.get("governing_law"), 200) or contract.governing_law
    contract.jurisdiction = _text(meta.get("jurisdiction"), 200) or contract.jurisdiction
    contract.analysis_json = json.dumps(analysis, ensure_ascii=False)
    contract.analysis_error = None

    # Re-analysis replaces earlier AI rows
    for model in (Risk, ContractParty, KeyDate, FinancialTerm):
        await db.execute(delete(model).where(model.contract_id == contract.id))

    for r in _list(analysis.get("risks")):
        title = _text(r.get("title"), 300)
        description = _text(r.get("description"))
        if not title or not description:
            continue
        cite = ground_citation(r.get("chunk_id"), r.get("quote"), chunks_by_id)
        db.add(Risk(
            contract_id=contract.id,
            risk_type=map_risk_type(r.get("category") or r.get("risk_type")),
            severity=map_severity(r.get("severity")),
            title=title,
            description=description,
            recommendation=_text(r.get("recommendation")),
            clause_reference=_text(r.get("clause_reference"), 200),
            source_chunk_id=cite["chunk_id"],
            source_page=cite["page"],
            source_snippet=cite["snippet"],
        ))

    seen_parties = set()
    for p in _list(analysis.get("parties")):
        name = _text(p.get("name"), 300)
        if not name or name.lower() in seen_parties:
            continue
        seen_parties.add(name.lower())
        cite = ground_citation(p.get("chunk_id"), p.get("quote"), chunks_by_id)
        db.add(ContractParty(
            contract_id=contract.id,
            name=name,
            type=map_party_type(p.get("type")),
            role=map_role(p.get("role")),
            source_page=cite["page"],
            source_snippet=cite["snippet"],
        ))

    for d in _list(analysis.get("dates")):
        when = parse_iso_date(d.get("date"))
        if not when:
            continue  # "upon signature" style dates stay in analysis_json only
        cite = ground_citation(d.get("chunk_id"), d.get("quote"), chunks_by_id)
        db.add(KeyDate(
            contract_id=contract.id,
            date_type=map_date_type(d.get("type") or d.get("date_type")),
            date=when,
            description=_text(d.get("description")),
            source_page=cite["page"],
            source_snippet=cite["snippet"],
        ))

    for t in _list(analysis.get("financial_terms")):
        description = _text(t.get("description"))
        amount = parse_amount(t.get("amount"))
        if not description and amount is None:
            continue
        cite = ground_citation(t.get("chunk_id"), t.get("quote"), chunks_by_id)
        db.add(FinancialTerm(
            contract_id=contract.id,
            term_type=map_term_type(t.get("type") or t.get("term_type")),
            amount=amount,
            currency=(_text(t.get("currency"), 10) or None),
            schedule=_text(t.get("schedule"), 200),
            description=description,
            source_page=cite["page"],
            source_snippet=cite["snippet"],
        ))


def analysis_extras(contract: Contract) -> Dict[str, Any]:
    """Fields from the stored analysis that have no table of their own."""
    try:
        data = json.loads(contract.analysis_json) if contract.analysis_json else {}
    except (TypeError, ValueError):
        data = {}
    summary = data.get("summary") if isinstance(data.get("summary"), dict) else {}
    highlights = [h for h in summary.get("highlights", []) if isinstance(h, str)] if isinstance(summary.get("highlights"), list) else []
    obligations = [
        {"party": _text(o.get("party")), "obligation": _text(o.get("obligation"))}
        for o in _list(summary.get("key_obligations"))
        if _text(o.get("obligation"))
    ]
    undated = [
        {"type": map_date_type(d.get("type")).value, "description": _text(d.get("description"))}
        for d in _list(data.get("dates"))
        if not parse_iso_date(d.get("date")) and _text(d.get("description"))
    ]
    return {
        "highlights": highlights,
        "key_obligations": obligations,
        "undated_terms": undated,
        "analyzed": bool(contract.analysis_json),
    }


async def analyze_and_save(db: AsyncSession, contract: Contract, output_language: str = "en") -> Dict[str, Any]:
    """
    Make sure the contract is indexed, run the analysis and persist it.
    Returns the raw analysis. Raises LLMError when the model fails (the error is
    recorded on the contract) and ValueError when the contract has no usable text.
    """
    from src.services.analyze import analyze_service
    from src.services.indexing import ensure_contract_index
    from src.services.llm import LLMError

    if not await ensure_contract_index(db, contract):
        raise ValueError("Unable to extract text from file")

    try:
        result = await analyze_service.analyze(contract_id=str(contract.id), output_language=output_language)
    except LLMError as e:
        contract.analysis_error = str(e)[:1000]
        await db.commit()
        raise

    await save_analysis(db, contract, result["analysis"], result["chunks"])
    await db.commit()
    return result["analysis"]
