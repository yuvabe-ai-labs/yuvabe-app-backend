import uuid
from typing import List, Optional

from pydantic import BaseModel


class UploadKBResponse(BaseModel):
    kb_id: uuid.UUID
    name: str
    chunks_stored: int


class UploadKBRequest(BaseModel):
    name: str
    description: Optional[str] = None


class TokenizeRequest(BaseModel):
    text: str


class TokenizeResponse(BaseModel):
    input_ids: List[int]
    attention_mask: List[int]


class SemanticSearchRequest(BaseModel):
    embedding: List[float]
    top_k: Optional[int] = 3


class SemanticSearchResult(BaseModel):
    chunk_id: str
    kb_id: str
    text: str
    score: float

class ManualTextRequest(BaseModel):
    kb_id: uuid.UUID
    text: str
