from pathlib import Path
from typing import List, Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ..assistant.avatars import get_avatar, list_avatars
from ..assistant.catalog import ProductCatalog
from ..assistant.llm import LLMGenerationError, ProductLLM
from ..assistant.rag import ProductRAG


DATA_PATH = Path(__file__).resolve().parents[2] / "data" / "vital_products_fixed.csv"

CATALOG = ProductCatalog(DATA_PATH)
RAG = ProductRAG(CATALOG.products)
LLM = ProductLLM()

router = APIRouter(prefix="/bo2", tags=["bo2"])


class AvatarOut(BaseModel):
	avatar_id: str
	name: str
	tone: str
	audience_focus: str


class HealthOut(BaseModel):
	status: str
	product_count: int
	rag_chunk_count: int
	llm_model: str
	llm_base_url: str


class RagRetrieveRequest(BaseModel):
	question: str = Field(..., min_length=3)
	top_k: int = Field(default=5, ge=1, le=10)


class RagAskRequest(BaseModel):
	question: str = Field(..., min_length=3)
	avatar_id: Literal["ava_med", "leo_pharma"] = "ava_med"
	audience: str = Field(default="physicians")
	top_k: int = Field(default=5, ge=1, le=10)


@router.get("/health", response_model=HealthOut)
def health() -> HealthOut:
	stats = RAG.stats()
	return HealthOut(
		status="ok",
		product_count=stats.product_count,
		rag_chunk_count=stats.chunk_count,
		llm_model=LLM.model,
		llm_base_url=LLM.base_url,
	)


@router.get("/avatars", response_model=List[AvatarOut])
def avatars() -> List[AvatarOut]:
	return [
		AvatarOut(
			avatar_id=a.avatar_id,
			name=a.name,
			tone=a.tone,
			audience_focus=a.audience_focus,
		)
		for a in list_avatars()
	]


@router.post("/rag/reindex")
def rag_reindex() -> dict:
	stats = RAG.reindex()
	return {
		"status": "ok",
		"product_count": stats.product_count,
		"chunk_count": stats.chunk_count,
	}


@router.post("/rag/retrieve")
def rag_retrieve(payload: RagRetrieveRequest) -> dict:
	try:
		chunks = RAG.retrieve(question=payload.question, top_k=payload.top_k)
	except ValueError as exc:
		raise HTTPException(status_code=400, detail=str(exc)) from exc

	return {
		"question": payload.question,
		"contexts": [
			{
				"chunk_id": c.chunk_id,
				"product_name": c.product_name,
				"score": round(c.score, 4),
				"text": c.text,
				"metadata": c.metadata,
			}
			for c in chunks
		],
	}


@router.post("/rag/ask")
def rag_ask(payload: RagAskRequest) -> dict:
	try:
		avatar = get_avatar(payload.avatar_id)
		chunks = RAG.retrieve(question=payload.question, top_k=payload.top_k)
	except ValueError as exc:
		raise HTTPException(status_code=400, detail=str(exc)) from exc

	try:
		answer = LLM.generate_answer(
			question=payload.question,
			contexts=chunks,
			avatar=avatar,
			audience=payload.audience,
		)
		generation_mode = "llm"
		llm_error = ""
	except LLMGenerationError as exc:
		# Keep demo usable even when Ollama is not running.
		best = chunks[0].product_name if chunks else "No product found"
		answer = (
			"LLM unavailable or timed out. "
			f"Top retrieved product: {best}."
		)
		generation_mode = "fallback"
		llm_error = str(exc)

	return {
		"question": payload.question,
		"avatar": {
			"avatar_id": avatar.avatar_id,
			"name": avatar.name,
			"tone": avatar.tone,
		},
		"audience": payload.audience,
		"generation_mode": generation_mode,
		"llm_error": llm_error,
		"answer": answer,
		"contexts": [
			{
				"chunk_id": c.chunk_id,
				"product_name": c.product_name,
				"score": round(c.score, 4),
				"metadata": c.metadata,
			}
			for c in chunks
		],
	}
