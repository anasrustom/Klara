from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_, and_, exists, delete
from sqlalchemy.orm import selectinload
from typing import Optional, List
from datetime import datetime, timedelta
from pydantic import BaseModel
import json

from src.config.database import get_db
from src.models.contract import Contract, KeyDate, DateType, ContractStatus, ContractParty, PartyType, PartyRole, FinancialTerm, TermType
from src.models.risk import Risk, RiskSeverity, RiskType
from src.models.clause import Clause
from src.models.user import User
from src.api.routes.auth import get_current_user
from src.services.analysis_store import analysis_extras, analyze_and_save
from src.services.llm import LLMError

router = APIRouter()

_SEVERITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3}

def _risk_out(r: Risk) -> dict:
    return {
        "id": r.id,
        "contract_id": r.contract_id,
        "risk_type": r.risk_type.value,
        "severity": r.severity.value,
        "title": r.title,
        "description": r.description,
        "recommendation": r.recommendation,
        "clause_reference": r.clause_reference,
        "source_chunk_id": r.source_chunk_id,
        "source_page": r.source_page,
        "source_snippet": r.source_snippet,
    }

def _sorted_risks(risks) -> list:
    return sorted(risks, key=lambda r: _SEVERITY_ORDER.get(r.severity.value, 9))

# Request/Response models
class RiskCreate(BaseModel):
    risk_type: str
    severity: str
    title: str
    description: str
    recommendation: Optional[str] = None
    clause_reference: Optional[str] = None

class ContractUpdate(BaseModel):
    title: Optional[str] = None
    status: Optional[str] = None
    governing_law: Optional[str] = None
    jurisdiction: Optional[str] = None
    industry: Optional[str] = None
    contract_type: Optional[str] = None
    tags: Optional[List[str]] = None
    summary: Optional[str] = None
    purpose: Optional[str] = None
    scope: Optional[str] = None

@router.get("")
async def list_contracts(
    search: Optional[str] = Query(None),
    industry: Optional[str] = Query(None),
    governing_law: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List all contracts with optional filters.
    TODO: Backend team needs to implement:
    1. Advanced filtering
    2. Sorting options
    3. Performance optimization for large datasets
    """
    query = select(Contract).options(
        selectinload(Contract.parties),
        selectinload(Contract.key_dates),
        selectinload(Contract.financial_terms),
        selectinload(Contract.risks)
    )
    
    # Filter by current user - only show their contracts
    query = query.where(Contract.uploaded_by == current_user.id)
    
    # Apply filters
    if search:
        query = query.where(
            or_(
                Contract.title.ilike(f"%{search}%"),
                Contract.summary.ilike(f"%{search}%")
            )
        )
    
    if industry:
        query = query.where(Contract.industry == industry)
    
    if governing_law:
        query = query.where(Contract.governing_law == governing_law)
    
    if status:
        query = query.where(Contract.status == status)
    
    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    result = await db.execute(count_query)
    total = result.scalar()
    
    # Apply pagination
    query = query.order_by(Contract.upload_date.desc()).offset((page - 1) * page_size).limit(page_size)
    
    result = await db.execute(query)
    contracts = result.scalars().all()
    
    # Convert to response format
    items = []
    for contract in contracts:
        items.append({
            "id": contract.id,
            "title": contract.title,
            "file_name": contract.file_name,
            "file_type": contract.file_type.value,
            "upload_date": contract.upload_date.isoformat(),
            "uploaded_by": contract.uploaded_by,
            "status": contract.status.value,
            "parties": [
                {
                    "id": p.id,
                    "name": p.name,
                    "type": p.type.value,
                    "role": p.role.value
                } for p in contract.parties
            ],
            "key_dates": [
                {
                    "id": d.id,
                    "date_type": d.date_type.value,
                    "date": d.date.isoformat(),
                    "description": d.description
                } for d in contract.key_dates
            ],
            "financial_terms": [
                {
                    "id": t.id,
                    "term_type": t.term_type.value,
                    "amount": t.amount,
                    "currency": t.currency,
                    "schedule": t.schedule,
                    "description": t.description
                } for t in contract.financial_terms
            ],
            "governing_law": contract.governing_law,
            "jurisdiction": contract.jurisdiction,
            "industry": contract.industry,
            "contract_type": contract.contract_type,
            "tags": json.loads(contract.tags) if contract.tags else [],
            "summary": contract.summary,
            "purpose": contract.purpose,
            "scope": contract.scope,
            "risks": [_risk_out(r) for r in _sorted_risks(contract.risks)],
            "updated_at": contract.updated_at.isoformat()
        })
    
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size
    }

@router.get("/{contract_id}")
async def get_contract(
    contract_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get detailed information about a specific contract.
    TODO: Backend team needs to implement access control.
    """
    query = select(Contract).where(
        Contract.id == contract_id,
        Contract.uploaded_by == current_user.id  # Only allow user to access their own contracts
    ).options(
        selectinload(Contract.parties),
        selectinload(Contract.key_dates),
        selectinload(Contract.financial_terms),
        selectinload(Contract.risks),
        selectinload(Contract.clauses)
    )
    
    result = await db.execute(query)
    contract = result.scalar_one_or_none()
    
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")
    
    return {
        "id": contract.id,
        "title": contract.title,
        "file_name": contract.file_name,
        "file_type": contract.file_type.value,
        "upload_date": contract.upload_date.isoformat(),
        "uploaded_by": contract.uploaded_by,
        "status": contract.status.value,
        "language": contract.language,
        "pages": contract.pages,
        "parties": [
            {
                "id": p.id,
                "contract_id": p.contract_id,
                "name": p.name,
                "type": p.type.value,
                "role": p.role.value,
                "source_page": p.source_page,
                "source_snippet": p.source_snippet,
            } for p in contract.parties
        ],
        "key_dates": [
            {
                "id": d.id,
                "contract_id": d.contract_id,
                "date_type": d.date_type.value,
                "date": d.date.isoformat(),
                "description": d.description,
                "source_page": d.source_page,
                "source_snippet": d.source_snippet,
            } for d in sorted(contract.key_dates, key=lambda d: d.date)
        ],
        "financial_terms": [
            {
                "id": t.id,
                "contract_id": t.contract_id,
                "term_type": t.term_type.value,
                "amount": t.amount,
                "currency": t.currency,
                "schedule": t.schedule,
                "description": t.description,
                "source_page": t.source_page,
                "source_snippet": t.source_snippet,
            } for t in contract.financial_terms
        ],
        "governing_law": contract.governing_law,
        "jurisdiction": contract.jurisdiction,
        "industry": contract.industry,
        "contract_type": contract.contract_type,
        "tags": json.loads(contract.tags) if contract.tags else [],
        "summary": contract.summary,
        "purpose": contract.purpose,
        "scope": contract.scope,
        "risks": [_risk_out(r) for r in _sorted_risks(contract.risks)],
        "analysis_error": contract.analysis_error,
        **analysis_extras(contract),
        "updated_at": contract.updated_at.isoformat()
    }

@router.post("/{contract_id}/analyze")
async def reanalyze_contract(
    contract_id: str,
    output_language: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Run the AI analysis again for a stored contract and replace its AI-derived data.
    Useful for contracts uploaded before analysis was persisted.
    """
    result = await db.execute(select(Contract).where(
        Contract.id == contract_id,
        Contract.uploaded_by == current_user.id
    ))
    contract = result.scalar_one_or_none()
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")

    lang = output_language if output_language in ("en", "ar") else (contract.language or "en")
    try:
        await analyze_and_save(db, contract, output_language=lang)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except LLMError as e:
        raise HTTPException(status_code=502, detail=f"AI analysis failed: {str(e)}")

    contract.status = ContractStatus.completed
    await db.commit()
    return {"id": contract.id, "status": contract.status.value, "message": "Contract analyzed successfully."}

@router.get("/dashboard/stats")
async def get_dashboard_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get dashboard statistics for the current user.
    """
    # Total contracts for current user
    total_result = await db.execute(
        select(func.count(Contract.id)).where(Contract.uploaded_by == current_user.id)
    )
    total_contracts = total_result.scalar()
    
    # Pending reviews (pending status = awaiting review) for current user
    pending_result = await db.execute(
        select(func.count(Contract.id)).where(
            Contract.uploaded_by == current_user.id,
            Contract.status == "pending"
        )
    )
    pending_reviews = pending_result.scalar()
    
    # High risk contracts - count contracts with at least one high or critical severity risk
    high_risk_subquery = (
        select(Risk.contract_id)
        .where(
            or_(
                Risk.severity == RiskSeverity.high,
                Risk.severity == RiskSeverity.critical
            )
        )
        .distinct()
    )
    high_risk_result = await db.execute(
        select(func.count(Contract.id)).where(
            Contract.uploaded_by == current_user.id,
            Contract.id.in_(high_risk_subquery)
        )
    )
    high_risk_contracts = high_risk_result.scalar()
    
    # Expiring soon - contracts expiring in next 30 days
    now = datetime.utcnow()
    thirty_days_from_now = now + timedelta(days=30)
    
    expiring_subquery = (
        select(KeyDate.contract_id)
        .where(
            KeyDate.date_type == DateType.expiration_date,
            KeyDate.date >= now,
            KeyDate.date <= thirty_days_from_now
        )
        .distinct()
    )
    expiring_result = await db.execute(
        select(func.count(Contract.id)).where(
            Contract.uploaded_by == current_user.id,
            Contract.id.in_(expiring_subquery)
        )
    )
    expiring_soon = expiring_result.scalar()
    
    # Recent uploads for current user
    recent_query = select(Contract).where(
        Contract.uploaded_by == current_user.id
    ).order_by(Contract.upload_date.desc()).limit(5)
    recent_result = await db.execute(recent_query)
    recent_contracts = recent_result.scalars().all()
    
    return {
        "total_contracts": total_contracts,
        "pending_reviews": pending_reviews,
        "high_risk_contracts": high_risk_contracts,
        "expiring_soon": expiring_soon,
        "recent_uploads": [
            {
                "id": c.id,
                "title": c.title,
                "file_name": c.file_name,
                "status": c.status.value,
                "upload_date": c.upload_date.isoformat()
            } for c in recent_contracts
        ]
    }

@router.patch("/{contract_id}")
async def update_contract(
    contract_id: str,
    update_data: ContractUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update contract details.
    """
    # Get contract
    query = select(Contract).where(
        Contract.id == contract_id,
        Contract.uploaded_by == current_user.id
    )
    result = await db.execute(query)
    contract = result.scalar_one_or_none()
    
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")
    
    # Update fields
    update_dict = update_data.model_dump(exclude_unset=True)
    
    for field, value in update_dict.items():
        if field == "status":
            contract.status = ContractStatus[value]
        elif field == "tags":
            contract.tags = json.dumps(value)
        else:
            setattr(contract, field, value)
    
    await db.commit()
    await db.refresh(contract)
    
    return {
        "id": contract.id,
        "title": contract.title,
        "status": contract.status.value,
        "message": "Contract updated successfully"
    }

@router.post("/{contract_id}/risks")
async def add_risk(
    contract_id: str,
    risk_data: RiskCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Add a risk to a contract.
    """
    # Verify contract exists and belongs to user
    query = select(Contract).where(
        Contract.id == contract_id,
        Contract.uploaded_by == current_user.id
    )
    result = await db.execute(query)
    contract = result.scalar_one_or_none()
    
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")
    
    # Create new risk
    new_risk = Risk(
        contract_id=contract_id,
        risk_type=RiskType[risk_data.risk_type],
        severity=RiskSeverity[risk_data.severity],
        title=risk_data.title,
        description=risk_data.description,
        recommendation=risk_data.recommendation,
        clause_reference=risk_data.clause_reference
    )
    
    db.add(new_risk)
    await db.commit()
    await db.refresh(new_risk)
    
    return {
        "id": new_risk.id,
        "contract_id": new_risk.contract_id,
        "risk_type": new_risk.risk_type.value,
        "severity": new_risk.severity.value,
        "title": new_risk.title,
        "description": new_risk.description,
        "recommendation": new_risk.recommendation,
        "clause_reference": new_risk.clause_reference,
        "message": "Risk added successfully"
    }

@router.delete("/{contract_id}/risks/{risk_id}")
async def delete_risk(
    contract_id: str,
    risk_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete a risk from a contract.
    """
    # Verify contract exists and belongs to user
    query = select(Contract).where(
        Contract.id == contract_id,
        Contract.uploaded_by == current_user.id
    )
    result = await db.execute(query)
    contract = result.scalar_one_or_none()
    
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")
    
    # Delete risk
    delete_query = delete(Risk).where(
        Risk.id == risk_id,
        Risk.contract_id == contract_id
    )
    result = await db.execute(delete_query)
    await db.commit()
    
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Risk not found")
    
    return {"message": "Risk deleted successfully"}
