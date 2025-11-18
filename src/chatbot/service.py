import os

from sqlmodel.ext.asyncio.session import AsyncSession

from .embedding import embedding_model
from .models import KnowledgeBase, KnowledgeChunk
from .utils import (
    chunk_sentences_with_overlap,
    extract_text_from_pdf_fileobj,
    split_into_sentences,
)

DEFAULT_MAX_WORDS = int(os.getenv("CHUNK_MAX_WORDS", "200"))
DEFAULT_OVERLAP = int(os.getenv("CHUNK_OVERLAP_WORDS", "40"))


async def process_pdf_and_store(
    fileobj, kb_name: str, kb_description: str | None, session: AsyncSession
):
    raw_text = extract_text_from_pdf_fileobj(fileobj)

    sentences = split_into_sentences(raw_text)

    chunks = chunk_sentences_with_overlap(
        sentences, max_words=DEFAULT_MAX_WORDS, overlap_words=DEFAULT_OVERLAP
    )

    kb = KnowledgeBase(name=kb_name, description=kb_description)
    session.add(kb)
    await session.commit()
    await session.refresh(kb)

    chunk_objs = []
    for idx, chunk_text in enumerate(chunks):
        emb = await embedding_model.embed_text(chunk_text)

        chunk = KnowledgeChunk(
            kb_id=kb.id, chunk_index=idx, chunk_text=chunk_text, embedding=emb
        )
        session.add(chunk)
        chunk_objs.append(chunk)

    await session.commit()

    return {"kb_id": kb.id, "name": kb_name, "chunks_stored": len(chunk_objs)}
