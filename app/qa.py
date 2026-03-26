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


def _format_conversation_history(
    history: List[Dict[str, str]] | None,
    max_turns: int,
) -> str:
    if not history:
        return ""

    max_messages = max(0, max_turns * 2)
    trimmed_history = history[-max_messages:] if max_messages > 0 else []
    lines: List[str] = []
    for item in trimmed_history:
        role = str(item.get("role", "")).strip().lower()
        content = str(item.get("content", "")).strip()
        if role not in {"user", "assistant"} or not content:
            continue
        label = "Médecin" if role == "user" else "Assistant"
        lines.append(f"{label}: {content}")

    return "\n".join(lines)


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


def _needs_clarification(question: str) -> bool:
    text = (question or "").strip().lower()
    if not text:
        return True

    medical_keywords = {
        "indication", "indications", "dosage", "dose", "posologie", "contre", "contra", "side effect",
        "effets secondaires", "interaction", "interactions", "composition", "dci", "classe", "forme",
        "indication", "indicaciones", "dosis", "contraindication", "contraindications",
    }
    if any(keyword in text for keyword in medical_keywords):
        return False

    generic_request_patterns = [
        r"\bwhat products do you have\b",
        r"\bwhich products do you have\b",
        r"\bi want to ask you about a product\b",
        r"\bi wanna ask you about a product\b",
        r"\bask you about a product\b",
        r"\bparler d[eu]'?n produit\b",
        r"\bparler de produit\b",
        r"\bproduit que vous avez\b",
        r"\bproducto que tienes\b",
        r"\bproducto que tienen\b",
    ]
    if any(re.search(pattern, text) for pattern in generic_request_patterns):
        return True

    words = re.findall(r"[a-zA-ZÀ-ÿ0-9]+", text)
    is_short_greeting = len(words) <= 12 and any(
        greeting in text for greeting in ["hi", "hello", "hey", "salut", "bonjour", "hola"]
    )
    asks_about_product = any(token in text for token in ["product", "produit", "producto"])
    return is_short_greeting and asks_about_product


def _clarification_message(language: str) -> str:
    messages = {
        "fr": (
            "Bien sûr. Pouvez-vous préciser le nom du produit et ce que vous voulez savoir exactement "
            "(indication, posologie, contre-indications, effets secondaires, ou composition) ?"
        ),
        "en": (
            "Sure. Please provide the product name and what you want to know exactly "
            "(indication, dosage, contraindications, side effects, or composition)."
        ),
        "es": (
            "Claro. Indique el nombre del producto y qué desea saber exactamente "
            "(indicación, dosis, contraindicaciones, efectos adversos o composición)."
        ),
    }
    return messages.get(language, messages["en"])


def _smalltalk_reply(question: str, language: str) -> str | None:
    text = (question or "").strip().lower()
    if not text:
        return None

    greetings = {
        "bonjour", "salut", "bonsoir", "hello", "hi", "hey", "hola", "coucou"
    }
    thanks = {
        "merci", "thanks", "thank you", "gracias"
    }

    words = re.findall(r"[a-zA-ZÀ-ÿ']+", text)
    if not words:
        return None

    has_greeting = any(token in text for token in greetings)
    has_thanks = any(token in text for token in thanks)
    is_short = len(words) <= 6

    if not is_short:
        return None

    if has_greeting:
        replies = {
            "fr": "Bonjour 👋 Je suis prêt. Donnez-moi le nom du produit et ce que vous voulez savoir.",
            "en": "Hello 👋 I’m ready. Share the product name and what you want to know.",
            "es": "Hola 👋 Estoy listo. Indique el nombre del producto y lo que desea saber.",
        }
        return replies.get(language, replies["en"])

    if has_thanks:
        replies = {
            "fr": "Avec plaisir ✅ Si vous voulez, je peux répondre sur un produit précis.",
            "en": "You’re welcome ✅ I can help with a specific product if you want.",
            "es": "Con gusto ✅ Puedo ayudarle con un producto específico si quiere.",
        }
        return replies.get(language, replies["en"])

    return None


def _question_requests_objection(question: str) -> bool:
    text = (question or "").strip().lower()
    objection_markers = {
        "objection",
        "objections",
        "counter argument",
        "counter-argument",
        "réponse à une objection",
        "objection probable",
        "handle objection",
        "answer objection",
        "rebuttal",
    }
    return any(marker in text for marker in objection_markers)


def _answer_has_source_citation(answer_text: str, passages: List[Dict[str, str]]) -> bool:
    text = (answer_text or "").lower()
    if not text.strip():
        return False

    if any(token in text for token in ["source:", "sources:", "source :", "sources :", "passage "]):
        return True

    for passage in passages:
        source = str(passage.get("source", "")).strip().lower()
        if source and source in text:
            return True
        source_name = source.replace("\\", "/").split("/")[-1]
        if source_name and source_name in text:
            return True

    return False


def _grounding_overlap_score(answer_text: str, passages: List[Dict[str, str]]) -> float:
    answer_tokens = set(re.findall(r"[a-zA-ZÀ-ÿ0-9]{4,}", (answer_text or "").lower()))
    if not answer_tokens:
        return 0.0

    context_text = " ".join(str(item.get("text", "")) for item in passages)
    context_tokens = set(re.findall(r"[a-zA-ZÀ-ÿ0-9]{4,}", context_text.lower()))
    if not context_tokens:
        return 0.0

    meaningful = {
        token
        for token in answer_tokens
        if token not in {"this", "that", "with", "from", "pour", "avec", "dans", "this", "have", "were", "will"}
    }
    if not meaningful:
        return 0.0

    overlap = len([token for token in meaningful if token in context_tokens])
    return max(0.0, min(1.0, overlap / max(1, len(meaningful))))


def _has_numeric_claim_mismatch(answer_text: str, passages: List[Dict[str, str]]) -> bool:
    answer_numbers = set(re.findall(r"\b\d+(?:[\.,]\d+)?\b", answer_text or ""))
    if not answer_numbers:
        return False

    context_text = " ".join(str(item.get("text", "")) for item in passages)
    context_numbers = set(re.findall(r"\b\d+(?:[\.,]\d+)?\b", context_text))
    if not context_numbers:
        return True

    missing = [number for number in answer_numbers if number not in context_numbers]
    return len(missing) >= 2


def _build_validation_result(
    *,
    answer_text: str,
    passages: List[Dict[str, str]],
    mode: str,
) -> Dict[str, object]:
    has_citation = _answer_has_source_citation(answer_text, passages)
    overlap = _grounding_overlap_score(answer_text, passages)
    numeric_mismatch = _has_numeric_claim_mismatch(answer_text, passages)

    contradiction_risk = bool(overlap < 0.18 or numeric_mismatch)

    retrieval_strength = 0.0
    if passages:
        top_scores = [float(item.get("score", 0.0)) for item in passages[:3]]
        retrieval_strength = sum(top_scores) / max(1, len(top_scores))

    score = 0.45 * retrieval_strength + 0.35 * overlap + 0.20 * (1.0 if has_citation else 0.0)
    if contradiction_risk:
        score -= 0.25
    if mode == "fallback":
        score -= 0.20
    score = max(0.0, min(1.0, score))

    if score >= 0.70 and not contradiction_risk:
        level = "high"
    elif score >= 0.45:
        level = "medium"
    else:
        level = "low"

    issues: List[str] = []
    if not has_citation:
        issues.append("missing_source_citation")
    if overlap < 0.18:
        issues.append("low_grounding_overlap")
    if numeric_mismatch:
        issues.append("possible_numeric_mismatch")
    if mode == "fallback":
        issues.append("fallback_mode")

    return {
        "confidence": level,
        "confidence_score": round(score, 3),
        "has_citation": has_citation,
        "contradiction_risk": contradiction_risk,
        "issues": issues,
    }


def _validation_warning(validation: Dict[str, object], language: str) -> str:
    if validation.get("confidence") == "high" and not validation.get("contradiction_risk"):
        return ""

    messages = {
        "fr": "⚠️ Validation: fiabilité limitée. Vérifiez les sources avant décision clinique.",
        "en": "⚠️ Validation: limited reliability. Please verify sources before clinical decisions.",
        "es": "⚠️ Validación: fiabilidad limitada. Verifique las fuentes antes de decisiones clínicas.",
    }
    return messages.get(language, messages["en"])


def _should_block_answer(validation: Dict[str, object]) -> bool:
    confidence = str(validation.get("confidence", "")).lower()
    contradiction_risk = bool(validation.get("contradiction_risk", False))
    return contradiction_risk or confidence == "low"


def _validation_block_message(language: str) -> str:
    messages = {
        "fr": (
            "Je préfère ne pas répondre car la réponse générée n'est pas suffisamment fiable par rapport aux sources. "
            "Pouvez-vous préciser le nom exact du produit et la rubrique souhaitée (indication, posologie, contre-indications, effets secondaires) ?"
        ),
        "en": (
            "I prefer not to answer because the generated response is not sufficiently reliable against the sources. "
            "Please provide the exact product name and the requested topic (indication, dosage, contraindications, side effects)."
        ),
        "es": (
            "Prefiero no responder porque la respuesta generada no es lo suficientemente fiable según las fuentes. "
            "Indique el nombre exacto del producto y el tema solicitado (indicación, dosis, contraindicaciones, efectos adversos)."
        ),
    }
    return messages.get(language, messages["en"])


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
    if best["score"] < 0.15:
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
    conversation_history: str,
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
    include_objection = _question_requests_objection(question)

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

    if include_objection:
        response_formats = {
            "fr": (
                "Format de sortie obligatoire:\n"
                "1) Réponse directe (2-5 phrases)\n"
                "2) Preuves documentaires (citer la source)\n"
                "3) Réponse à l'objection demandée"
            ),
            "en": (
                "Mandatory output format:\n"
                "1) Direct answer (2-5 sentences)\n"
                "2) Documentary evidence (cite source)\n"
                "3) Response to the requested objection"
            ),
            "es": (
                "Formato obligatorio:\n"
                "1) Respuesta directa (2-5 frases)\n"
                "2) Evidencias documentales (citar fuente)\n"
                "3) Respuesta a la objeción solicitada"
            ),
        }
    else:
        response_formats = {
            "fr": (
                "Format de sortie obligatoire:\n"
                "1) Réponse directe (2-5 phrases)\n"
                "2) Points clés (2-4 puces maximum, seulement si utile)\n"
                "3) Sources (1 ligne)\n"
                "Ne pas ajouter de section objection ni de prochaine action si ce n'est pas demandé."
            ),
            "en": (
                "Mandatory output format:\n"
                "1) Direct answer (2-5 sentences)\n"
                "2) Key points (max 2-4 bullets, only if useful)\n"
                "3) Sources (1 line)\n"
                "Do not add objection or next-action sections unless explicitly requested."
            ),
            "es": (
                "Formato obligatorio:\n"
                "1) Respuesta directa (2-5 frases)\n"
                "2) Puntos clave (máx. 2-4 viñetas, solo si es útil)\n"
                "3) Fuentes (1 línea)\n"
                "No agregues secciones de objeciones ni próximos pasos salvo solicitud explícita."
            ),
        }

    role_instruction = sales_role_prompts.get(answer_language, sales_role_prompts["fr"])
    output_contract = response_formats.get(answer_language, response_formats["fr"])

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", "{system_prompt}\n\n{role_instruction}"),
            (
                "human",
                "Recent conversation history:\n{conversation_history}\n\n"
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
            "conversation_history": conversation_history,
            "question": question,
            "context": context,
            "target_language": target_language,
            "output_contract": output_contract,
        }
    )


def answer_question(
    question: str,
    settings: Settings,
    preferred_language: str | None = None,
    conversation_history: List[Dict[str, str]] | None = None,
) -> Dict[str, object]:
    if preferred_language in {"fr", "en", "es"}:
        answer_language = preferred_language
    else:
        answer_language = _infer_question_language(question, settings.language)

    smalltalk = _smalltalk_reply(question, answer_language)
    if smalltalk:
        return {
            "answer": smalltalk,
            "passages": [],
            "mode": "smalltalk",
            "answer_language": answer_language,
            "validation": {
                "confidence": "high",
                "confidence_score": 1.0,
                "has_citation": True,
                "contradiction_risk": False,
                "issues": [],
            },
        }

    if _needs_clarification(question):
        return {
            "answer": _clarification_message(answer_language),
            "passages": [],
            "mode": "clarification",
            "answer_language": answer_language,
        }

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
    history_block = _format_conversation_history(conversation_history, settings.memory_turns)

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

    answer_text: str | None = _answer_with_langchain(
        question=question,
        context=context,
        answer_language=answer_language,
        selected_system_prompt=selected_system_prompt,
        conversation_history=history_block,
        model=model,
        provider=provider,
        settings=settings,
    )
    answer_mode = "langchain" if answer_text else mode

    if not answer_text:
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": selected_system_prompt},
                    {
                        "role": "user",
                        "content": (
                            "Recent conversation history (for continuity):\n"
                            f"{history_block if history_block else 'No prior history.'}"
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.2,
            )
            answer_text = response.choices[0].message.content
            if answer_text:
                answer_mode = mode
        except Exception:
            answer_text = None

    if not answer_text:
        answer_text = _fallback_answer(question, passages, answer_language)
        answer_mode = "fallback"

    validation = _build_validation_result(
        answer_text=answer_text,
        passages=passages,
        mode=answer_mode,
    )

    if _should_block_answer(validation):
        return {
            "answer": _validation_block_message(answer_language),
            "passages": passages,
            "mode": "validation_blocked",
            "answer_language": answer_language,
            "validation": validation,
        }

    warning = _validation_warning(validation, answer_language)
    final_answer = f"{answer_text}\n\n{warning}" if warning else answer_text

    return {
        "answer": final_answer,
        "passages": passages,
        "mode": answer_mode,
        "answer_language": answer_language,
        "validation": validation,
    }