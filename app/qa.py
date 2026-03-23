from __future__ import annotations

from typing import Dict, List
import os
import re

from openai import OpenAI

from .config import Settings
from .rag import retrieve


def _format_context(passages: List[Dict[str, str]]) -> str:
    parts: List[str] = []
    for index, passage in enumerate(passages, start=1):
        parts.append(
            f"[Passage {index}]\n"
            f"Source: {passage['source']}\n"
            f"Score: {passage['score']:.3f}\n"
            f"Texte: {passage['text']}"
        )
    return "\n\n".join(parts)


def _infer_question_language(question: str, default_language: str = "fr") -> str:
    text = (question or "").strip().lower()
    if not text:
        return default_language

    english_markers = {
        "what", "when", "where", "which", "how", "why", "can", "could", "should",
        "does", "do", "is", "are", "the", "and", "for", "with", "about", "side", "effects"
    }
    french_markers = {
        "quoi", "quand", "où", "quel", "quelle", "comment", "pourquoi", "est", "sont",
        "les", "des", "avec", "pour", "contre", "effets", "indication", "posologie"
    }
    spanish_markers = {
        "qué", "cuando", "dónde", "cuál", "como", "por", "porque", "los", "las", "con",
        "para", "efectos", "indicaciones", "dosis", "contraindicaciones"
    }

    words = re.findall(r"[a-zA-ZÀ-ÿ]+", text)
    if not words:
        return default_language

    en_score = sum(1 for word in words if word in english_markers)
    fr_score = sum(1 for word in words if word in french_markers)
    es_score = sum(1 for word in words if word in spanish_markers)

    if en_score >= fr_score and en_score >= es_score and en_score > 0:
        return "en"
    if es_score >= fr_score and es_score > 0:
        return "es"
    if fr_score > 0:
        return "fr"
    return default_language


def _fallback_answer(question: str, passages: List[Dict[str, str]], language: str = "fr") -> str:
    fallback_messages = {
        "fr": {
            "no_passages": "Je ne dispose d'aucun passage pertinent dans la base documentaire pour répondre.",
            "low_score": "Je ne trouve pas d'information suffisamment fiable dans les documents fournis pour répondre précisément à cette question.",
            "based_on_docs": "Réponse basée sur les documents:"
        },
        "en": {
            "no_passages": "I do not have any relevant passages in the document database to answer.",
            "low_score": "I cannot find sufficiently reliable information in the provided documents to answer this question precisely.",
            "based_on_docs": "Response based on documents:"
        },
        "es": {
            "no_passages": "No tengo ningún pasaje relevante en la base de datos de documentos para responder.",
            "low_score": "No puedo encontrar información suficientemente confiable en los documentos proporcionados para responder esta pregunta con precisión.",
            "based_on_docs": "Respuesta basada en documentos:"
        }
    }
    
    msgs = fallback_messages.get(language, fallback_messages["fr"])
    
    if not passages:
        return msgs["no_passages"]

    best = passages[0]
    if best["score"] < 0.05:
        return msgs["low_score"]

    return (
        f"{msgs['based_on_docs']}\n\n"
        f"{best['text']}\n\n"
        f"Source: {best['source']}"
    )


def answer_question(question: str, settings: Settings) -> Dict[str, object]:
    answer_language = _infer_question_language(question, settings.language)
    passages = retrieve(settings.index_dir, question, top_k=settings.top_k)
    context = _format_context(passages)

    provider = settings.llm_provider.lower().strip()
    if provider not in {"ollama", "openai"}:
        return {
            "answer": _fallback_answer(question, passages, answer_language),
            "passages": passages,
            "mode": "fallback",
            "answer_language": answer_language,
        }

    if provider == "openai" and not os.getenv("OPENAI_API_KEY"):
        return {
            "answer": _fallback_answer(question, passages, answer_language),
            "passages": passages,
            "mode": "fallback",
            "answer_language": answer_language,
        }

    if provider == "ollama":
        client = OpenAI(
            base_url=settings.ollama_base_url,
            api_key=os.getenv("OLLAMA_API_KEY", "ollama"),
        )
        model = settings.ollama_model
        mode = "ollama"
    else:
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        model = settings.openai_model
        mode = "openai"

    # Language-specific prompts
    _LANGUAGE_PROMPTS = {
        "fr": (
            "Question du médecin:\n"
            f"{question}\n\n"
            "Contexte documentaire:\n"
            f"{context}\n\n"
            "Rédige une réponse claire, professionnelle et concise en français. "
            "N'affirme que les éléments présents dans le contexte."
        ),
        "en": (
            "Medical Question:\n"
            f"{question}\n\n"
            "Document Context:\n"
            f"{context}\n\n"
            "Provide a clear, professional, and concise response in English. "
            "Only state elements present in the context."
        ),
        "es": (
            "Pregunta Médica:\n"
            f"{question}\n\n"
            "Contexto Documental:\n"
            f"{context}\n\n"
            "Proporciona una respuesta clara, profesional y concisa en español. "
            "Sólo afirma elementos presentes en el contexto."
        )
    }
    prompt = _LANGUAGE_PROMPTS.get(settings.language, _LANGUAGE_PROMPTS["fr"])
    prompt = _LANGUAGE_PROMPTS.get(answer_language, _LANGUAGE_PROMPTS["fr"])

    system_prompts = {
        "fr": settings._SYSTEM_PROMPTS.get("fr", settings.system_prompt),
        "en": settings._SYSTEM_PROMPTS.get("en", settings.system_prompt),
        "es": settings._SYSTEM_PROMPTS.get("es", settings.system_prompt),
    }
    selected_system_prompt = system_prompts.get(answer_language, settings.system_prompt)

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": selected_system_prompt},
            {"role": "user", "content": prompt},
        ],
        temperature=0.2,
    )

    answer_text = response.choices[0].message.content or _fallback_answer(question, passages, answer_language)

    return {
        "answer": answer_text,
        "passages": passages,
        "mode": mode,
        "answer_language": answer_language,
    }