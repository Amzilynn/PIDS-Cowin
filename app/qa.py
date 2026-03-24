from __future__ import annotations

from typing import Dict, List
import os
import re

from openai import OpenAI

try:
    from langchain_core.output_parsers import StrOutputParser
    from langchain_core.prompts import ChatPromptTemplate
    from langchain_openai import ChatOpenAI
except Exception:
    StrOutputParser = None
    ChatPromptTemplate = None
    ChatOpenAI = None

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
        "does", "do", "is", "are", "the", "and", "for", "with", "about", "side", "effects",
        "indication", "indications", "dosage", "contraindications", "benefits", "use", "uses", "of"
    }
    french_markers = {
        "quoi", "quand", "où", "quel", "quelle", "comment", "pourquoi", "est", "sont",
        "les", "des", "avec", "pour", "contre", "effets", "indication", "posologie",
        "parle", "moi", "produit", "nomme", "nommé", "brievement", "brièvement",
        "donne", "decris", "décris", "resume", "résume", "sur", "medicament", "médicament"
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

    # Strong phrase hints
    if any(phrase in text for phrase in ["what is", "what are", "how to", "side effects", "indications of", "dosage of"]):
        en_score += 3
    if any(phrase in text for phrase in ["qu'est-ce", "quelle est", "quelles sont", "effets secondaires", "posologie de"]):
        fr_score += 3
    if any(phrase in text for phrase in ["qué es", "cuál es", "efectos adversos", "dosis de"]):
        es_score += 3

    if en_score >= fr_score and en_score >= es_score and en_score > 0:
        return "en"
    if es_score >= fr_score and es_score > 0:
        return "es"
    if fr_score > 0:
        return "fr"

    # If undecidable, keep app default language rather than forcing English.
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


def _answer_with_langchain(
    *,
    question: str,
    context: str,
    answer_language: str,
    selected_system_prompt: str,
    model: str,
    provider: str,
    settings: Settings,
) -> str | None:
    if ChatOpenAI is None or ChatPromptTemplate is None or StrOutputParser is None:
        return None

    if provider == "ollama":
        llm = ChatOpenAI(
            model=model,
            base_url=settings.ollama_base_url,
            api_key=os.getenv("OLLAMA_API_KEY", "ollama"),
            temperature=0.2,
        )
    else:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            return None
        llm = ChatOpenAI(
            model=model,
            api_key=api_key,
            temperature=0.2,
        )

    language_labels = {
        "fr": "français",
        "en": "English",
        "es": "español",
    }
    target_language = language_labels.get(answer_language, "français")

    sales_role_prompts = {
        "fr": (
            "Tu joues le rôle d'un délégué médical orienté vente en pharmacie. "
            "Objectif: aider à convaincre le pharmacien avec un argumentaire utile et concret, "
            "sans jamais dépasser les informations disponibles dans le contexte documentaire. "
            "Interdictions: inventer des bénéfices, promettre un résultat clinique, ou comparer sans preuve."
        ),
        "en": (
            "You act as a pharmacy-focused medical sales delegate. "
            "Goal: help convince the pharmacist with practical value-oriented arguments, "
            "while never going beyond information present in the provided context. "
            "Forbidden: inventing benefits, making clinical guarantees, or unsupported comparisons."
        ),
        "es": (
            "Actúas como delegado médico orientado a la venta en farmacia. "
            "Objetivo: ayudar a convencer al farmacéutico con argumentos prácticos y de valor, "
            "sin exceder la información del contexto documental. "
            "Prohibido: inventar beneficios, prometer resultados clínicos o comparar sin evidencia."
        ),
    }

    response_formats = {
        "fr": (
            "Format de sortie obligatoire:\n"
            "1) Besoin officine\n"
            "2) Arguments produit (2-4 points)\n"
            "3) Preuves documentaires (citer la source)\n"
            "4) Réponse à une objection probable\n"
            "5) Prochaine action recommandée pour le délégué"
        ),
        "en": (
            "Mandatory output format:\n"
            "1) Pharmacy need\n"
            "2) Product arguments (2-4 bullets)\n"
            "3) Documentary evidence (cite source)\n"
            "4) Response to one likely objection\n"
            "5) Recommended next action for the delegate"
        ),
        "es": (
            "Formato obligatorio:\n"
            "1) Necesidad de la farmacia\n"
            "2) Argumentos del producto (2-4 puntos)\n"
            "3) Evidencias documentales (citar fuente)\n"
            "4) Respuesta a una objeción probable\n"
            "5) Próxima acción recomendada para el delegado"
        ),
    }

    role_instruction = sales_role_prompts.get(answer_language, sales_role_prompts["fr"])
    output_contract = response_formats.get(answer_language, response_formats["fr"])

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", "{system_prompt}\n\n{role_instruction}"),
            (
                "human",
                "Question:\n{question}\n\n"
                "Document context:\n{context}\n\n"
                "Answer language: {target_language}\n"
                "Answer only from context. If missing, say information was not found in provided sources.\n\n"
                "{output_contract}",
            ),
        ]
    )
    chain = prompt | llm | StrOutputParser()
    return chain.invoke(
        {
            "system_prompt": selected_system_prompt,
            "role_instruction": role_instruction,
            "question": question,
            "context": context,
            "target_language": target_language,
            "output_contract": output_contract,
        }
    )


def answer_question(question: str, settings: Settings, preferred_language: str | None = None) -> Dict[str, object]:
    if preferred_language in {"fr", "en", "es"}:
        answer_language = preferred_language
    else:
        answer_language = _infer_question_language(question, settings.language)
    passages = retrieve(
        settings.index_dir,
        question,
        top_k=settings.top_k,
        collection_name=settings.chroma_collection,
        embedding_model=settings.embedding_model,
        fetch_k=settings.retrieval_fetch_k,
        alpha_semantic=settings.retrieval_alpha_semantic,
        alpha_lexical=settings.retrieval_alpha_lexical,
        min_score=settings.retrieval_min_score,
        max_per_source=settings.retrieval_max_per_source,
    )
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

    answer_text: str | None = None
    if settings.use_langchain:
        answer_text = _answer_with_langchain(
            question=question,
            context=context,
            answer_language=answer_language,
            selected_system_prompt=selected_system_prompt,
            model=model,
            provider=provider,
            settings=settings,
        )

    if not answer_text:
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": selected_system_prompt},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.2,
            )
            answer_text = response.choices[0].message.content
        except Exception:
            answer_text = None

    if not answer_text:
        answer_text = _fallback_answer(question, passages, answer_language)

    return {
        "answer": answer_text,
        "passages": passages,
        "mode": "langchain" if settings.use_langchain else mode,
        "answer_language": answer_language,
    }