"""
Keeps each contract's in-memory search index available.
The FAISS index lives in memory, so after a restart it is rebuilt on first use
from the text stored on the contract (or, for older rows, from the uploaded file).
"""

from typing import Any, Dict
import json
import os

from sqlalchemy.ext.asyncio import AsyncSession

from src.models.contract import Contract, FileType
from src.services.ocr_service import OCRService
from src.services.rag import rag_service


async def extract_document(file_path: str, file_type: FileType) -> Dict[str, Any]:
    if file_type == FileType.pdf:
        return await OCRService.extract_text_from_pdf(file_path)
    return await OCRService.extract_text_from_docx(file_path)


def store_extracted(contract: Contract, parsed: Dict[str, Any]) -> None:
    """Keep the extracted text on the contract so the index can be rebuilt. Caller commits."""
    contract.extracted_text = parsed.get("text", "") or ""
    contract.page_offsets = json.dumps(parsed.get("page_offsets") or [])
    contract.language = parsed.get("language", "en")
    contract.pages = int(parsed.get("pages", 0) or 0) or None


async def index_contract(contract: Contract) -> bool:
    try:
        offsets = json.loads(contract.page_offsets) if contract.page_offsets else []
    except (TypeError, ValueError):
        offsets = []
    return await rag_service.index_contract(
        contract_id=str(contract.id),
        text=contract.extracted_text or "",
        language=contract.language or "en",
        page_offsets=offsets,
        user_id=str(contract.uploaded_by),
    )


async def ensure_contract_index(db: AsyncSession, contract: Contract) -> bool:
    """Return True when the contract is searchable, rebuilding its index if needed."""
    if rag_service.has_index(contract.id):
        return True

    if not (contract.extracted_text or "").strip():
        if not contract.file_path or not os.path.exists(contract.file_path):
            return False
        try:
            parsed = await extract_document(contract.file_path, contract.file_type)
        except Exception:
            return False
        if not (parsed.get("text") or "").strip():
            return False
        store_extracted(contract, parsed)
        await db.commit()

    return await index_contract(contract)
