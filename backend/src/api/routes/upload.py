from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
import os, uuid

from src.config.database import get_db
from src.config.settings import get_settings
from src.models.contract import Contract, FileType, ContractStatus

from src.api.routes.auth import get_current_user
from src.models.user import User

from src.services.indexing import extract_document, store_extracted, index_contract
from src.services.analysis_store import analyze_and_save
from src.services.llm import LLMError

router = APIRouter()
settings = get_settings()

_ALLOWED_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/octet-stream",
}

@router.post("/upload")
async def upload_contract(
    file: UploadFile = File(...),
    output_language: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Upload a contract (PDF/DOCX), index it and run the AI analysis in ONE LLM call.
    The analysis (summary, parties, dates, financial terms, cited risks) is saved on the contract.
    output_language: "en" or "ar" for the analysis prose; defaults to the contract's language.
    Required auth: Bearer Token → assigns actual user ID to uploaded_by.
    """
    if file.content_type not in _ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail="Invalid file type. Only PDF and DOCX are allowed.")

    name = file.filename or "contract"
    is_pdf = file.content_type == "application/pdf" or name.lower().endswith(".pdf")
    if not is_pdf and not name.lower().endswith(".docx"):
        raise HTTPException(status_code=400, detail="Invalid file type. Only PDF and DOCX are allowed.")

    content = await file.read()
    if len(content) > settings.max_file_size:
        raise HTTPException(status_code=413, detail="File is too large.")

    file_type = FileType.pdf if is_pdf else FileType.docx
    ext = ".pdf" if is_pdf else ".docx"
    unique_name = f"{uuid.uuid4()}{ext}"
    file_path = os.path.join(settings.upload_dir, unique_name)

    os.makedirs(settings.upload_dir, exist_ok=True)
    with open(file_path, "wb") as f:
        f.write(content)

    contract = Contract(
        title=os.path.splitext(name)[0],
        file_name=name,
        file_path=file_path,
        file_type=file_type,
        uploaded_by=str(current_user.id),
        status=ContractStatus.processing,
    )
    db.add(contract)
    await db.commit()
    await db.refresh(contract)

    try:
        parsed = await extract_document(file_path, file_type)
        if not (parsed.get("text") or "").strip():
            raise HTTPException(status_code=422, detail="Unable to extract text from file")

        store_extracted(contract, parsed)
        await db.commit()
        await index_contract(contract)

        language = contract.language or "en"
        lang = output_language if output_language in ("en", "ar") else language
        analysis = await analyze_and_save(db, contract, output_language=lang)

        contract.status = ContractStatus.completed
        await db.commit()
        await db.refresh(contract)

        return {
            "contract_id": contract.id,
            "file_name": contract.file_name,
            "status": contract.status.value,
            "pages": contract.pages,
            "language": language,
            "message": "Contract analyzed successfully.",
            "analysis": analysis,
        }

    except HTTPException:
        contract.status = ContractStatus.failed
        await db.commit()
        raise

    except LLMError as e:
        contract.status = ContractStatus.failed
        await db.commit()
        raise HTTPException(status_code=502, detail=f"AI analysis failed: {str(e)}")

    except Exception as e:
        contract.status = ContractStatus.failed
        await db.commit()
        raise HTTPException(status_code=500, detail=f"Analysis failed: {type(e).__name__}: {str(e)}")
