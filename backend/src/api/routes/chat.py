from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from typing import Optional, List

from src.config.database import get_db
from src.models.user import User
from src.models.chat_history import ChatHistory
from src.models.contract import Contract, ContractStatus
from src.api.routes.auth import get_current_user
from src.services.chat import chat_service
from src.services.indexing import ensure_contract_index

router = APIRouter()

# Portfolio questions search this many of the user's most recent contracts
_PORTFOLIO_LIMIT = 25

async def _load_previous_messages(
    db: AsyncSession,
    user_id: str,
    contract_id: Optional[str],
    limit: int = 10,
) -> List[dict]:
    """
    Fetch recent chat history to provide conversational context to the model.
    We keep it simple: last `limit` messages for this user (and contract if provided).
    """
    stmt = (
        select(ChatHistory)
        .where(ChatHistory.user_id == user_id)
        .order_by(desc(ChatHistory.timestamp))
        .limit(limit)
    )
    if contract_id:
        stmt = (
            select(ChatHistory)
            .where(ChatHistory.user_id == user_id)
            .where(ChatHistory.contract_id == contract_id)
            .order_by(desc(ChatHistory.timestamp))
            .limit(limit)
        )

    rows = (await db.execute(stmt)).scalars().all()
    history = [
        {
            "message": r.message,
            "response": r.response,
            "contract_id": r.contract_id,
            "created_at": r.timestamp.isoformat() if r.timestamp else None,
        }
        for r in reversed(rows)
    ]
    return history


@router.post("")
async def ask_question(
    message: str,
    contract_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Ask a question about a specific contract (if contract_id is provided)
    or about the overall portfolio (no contract_id).

    Returns:
      {
        "response": str,
        "citations": [{chunk_id, page, snippet, contract_id, contract_title}],
        "sources": List[str],
        "confidence": float
      }
    """
    if not message or not message.strip():
        raise HTTPException(status_code=400, detail="Message must not be empty.")
    if len(message) > 2000:
        raise HTTPException(status_code=400, detail="Message is too long.")

    previous_messages = await _load_previous_messages(
        db=db,
        user_id=current_user.id,
        contract_id=contract_id,
        limit=10,
    )

    if contract_id:
        contract = (await db.execute(
            select(Contract).where(Contract.id == contract_id, Contract.uploaded_by == current_user.id)
        )).scalar_one_or_none()
        if not contract:
            raise HTTPException(status_code=404, detail="Contract not found")
        if not await ensure_contract_index(db, contract):
            raise HTTPException(status_code=409, detail="This contract has no searchable text yet.")
        result = await chat_service.answer_contract_question(
            question=message,
            contract_id=str(contract_id),
            previous_messages=previous_messages,
        )
    else:
        contracts = (await db.execute(
            select(Contract)
            .where(Contract.uploaded_by == current_user.id, Contract.status == ContractStatus.completed)
            .order_by(desc(Contract.upload_date))
            .limit(_PORTFOLIO_LIMIT)
        )).scalars().all()
        titles = {}
        for c in contracts:
            if await ensure_contract_index(db, c):
                titles[str(c.id)] = c.title
        result = await chat_service.answer_general_question(
            question=message,
            user_id=str(current_user.id),
            previous_messages=previous_messages,
            contract_titles=titles,
        )

    ai_response = result.get("answer", "I couldn't generate a response.")
    citations = result.get("citations", [])
    sources = result.get("sources", [])
    confidence = float(result.get("confidence", 0.0))

    record = ChatHistory(
        contract_id=contract_id,
        user_id=current_user.id,
        message=message,
        response=ai_response,
    )
    db.add(record)
    await db.commit()

    return {
        "response": ai_response,
        "citations": citations,
        "sources": sources,
        "confidence": confidence,
    }


@router.get("/history")
async def get_chat_history(
    contract_id: Optional[str] = None,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Return recent chat history. If contract_id is provided, filter by that contract.
    """
    limit = max(1, min(limit, 200))

    stmt = (
        select(ChatHistory)
        .where(ChatHistory.user_id == current_user.id)
        .order_by(desc(ChatHistory.timestamp))
        .limit(limit)
    )
    if contract_id:
        stmt = (
            select(ChatHistory)
            .where(ChatHistory.user_id == current_user.id)
            .where(ChatHistory.contract_id == contract_id)
            .order_by(desc(ChatHistory.timestamp))
            .limit(limit)
        )

    rows = (await db.execute(stmt)).scalars().all()
    history = [
        {
            "id": getattr(r, "id", None),
            "contract_id": r.contract_id,
            "message": r.message,
            "response": r.response,
            "created_at": r.timestamp.isoformat() if r.timestamp else None,
        }
        for r in rows
    ]

    return {"history": list(reversed(history)), "count": len(history)}
