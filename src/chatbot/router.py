import os
import shutil
import tempfile
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy import text
from sqlmodel.ext.asyncio.session import AsyncSession

from src.core.database import get_async_session

from .embedding import embedding_model
from .schemas import (
    SemanticSearchRequest,
    SemanticSearchResult,
    TokenizeRequest,
    TokenizeResponse,
    UploadKBResponse,
)
from .service import process_pdf_and_store

router = APIRouter(prefix="/chatbot", tags=["chatbot"])


# before hitting this endpoint make sure the model.data & model.onnx_data is available on the asset/onnx folder
@router.post("/upload-pdf", response_model=UploadKBResponse)
async def upload_pdf(
    file: UploadFile = File(...),
    name: str = Form(...),
    description: Optional[str] = Form(None),
    session: AsyncSession = Depends(get_async_session),
):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(
            status_code=400, detail="Only PDF files are supported for now."
        )

    tmp_dir = tempfile.mkdtemp()
    tmp_path = os.path.join(tmp_dir, file.filename)
    try:
        with open(tmp_path, "wb") as out_f:
            shutil.copyfileobj(file.file, out_f)

        with open(tmp_path, "rb") as fobj:
            result = await process_pdf_and_store(fobj, name, description, session)

        return UploadKBResponse(
            kb_id=result["kb_id"],
            name=result["name"],
            chunks_stored=result["chunks_stored"],
        )
    finally:
        try:
            os.remove(tmp_path)
            os.rmdir(tmp_dir)
        except Exception:
            pass


@router.post("/tokenize", response_model=TokenizeResponse)
async def tokenize_text(payload: TokenizeRequest):
    try:
        encoded = embedding_model.tokenizer(
            payload.text,
            return_tensors="np",
            truncation=True,
            padding="longest",
            max_length=512,
        )

        return TokenizeResponse(
            input_ids=encoded["input_ids"][0].tolist(),
            attention_mask=encoded["attention_mask"][0].tolist(),
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/semantic-search", response_model=list[SemanticSearchResult])
async def semantic_search(
    payload: SemanticSearchRequest, session: AsyncSession = Depends(get_async_session)
):

    if len(payload.embedding) == 0:
        raise HTTPException(status_code=400, detail="Embedding cannot be empty.")

    q_vector = payload.embedding
    top_k = payload.top_k or 3

    # Convert Python list → pgvector string format
    q_vector_str = "[" + ",".join(str(x) for x in q_vector) + "]"

    sql = text(
        """
        SELECT id, kb_id, chunk_text, embedding <=> :query_vec AS score
        FROM knowledge_chunk
        ORDER BY embedding <=> :query_vec
        LIMIT :top_k
        """
    )

    result = await session.execute(
        sql, {"query_vec": q_vector_str, "top_k": top_k}
    )
    rows = result.fetchall()

    return [
        SemanticSearchResult(
            chunk_id=str(r.id),
            kb_id=str(r.kb_id),
            text=r.chunk_text,
            score=float(r.score),
        )
        for r in rows
    ]

