from __future__ import annotations

import os
from typing import List

import httpx

from .avatars import AvatarProfile
from .models import RetrievedChunk


class LLMGenerationError(Exception):
    pass


class ProductLLM:
    """Small LLM client wrapper for an Ollama local model."""

    def __init__(self) -> None:
        self.base_url = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
        self.model = os.getenv("OLLAMA_MODEL", "llama3.2:3b")
        self.timeout_seconds = float(os.getenv("OLLAMA_TIMEOUT_SECONDS", "120"))

    def generate_answer(
        self,
        question: str,
        contexts: List[RetrievedChunk],
        avatar: AvatarProfile,
        audience: str,
    ) -> str:
        prompt = _build_prompt(question, contexts, avatar, audience)
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.2,
                "num_predict": 220,
            },
        }

        try:
            with httpx.Client(timeout=self.timeout_seconds) as client:
                response = client.post(f"{self.base_url}/api/generate", json=payload)
                response.raise_for_status()
                data = response.json()
        except Exception as exc:
            raise LLMGenerationError(
                f"LLM call failed: {type(exc).__name__}: {exc}"
            ) from exc

        answer = (data.get("response") or "").strip()
        if not answer:
            raise LLMGenerationError("LLM returned an empty answer.")
        return answer


def _build_prompt(
    question: str,
    contexts: List[RetrievedChunk],
    avatar: AvatarProfile,
    audience: str,
) -> str:
    context_lines = []
    for c in contexts[:3]:
        short_text = c.text[:700]
        context_lines.append(
            f"- Product={c.product_name}; Score={c.score:.3f}; Context={short_text}"
        )
    context_block = "\n".join(context_lines) if context_lines else "- No context found"

    return (
        "You are a medico-commercial assistant representing Vital products.\n"
        f"Avatar style: {avatar.name} ({avatar.tone}), default focus: {avatar.audience_focus}.\n"
        f"Target audience for this answer: {audience}.\n"
        "Rules:\n"
        "1) Use only the provided retrieved context.\n"
        "2) If evidence is missing, say 'information not available in retrieved context'.\n"
        "3) Keep answer clear and professional (max 180 words).\n"
        "4) Mention product name(s) and practical guidance.\n\n"
        f"User question: {question}\n\n"
        "Retrieved context:\n"
        f"{context_block}\n"
    )
