from dataclasses import dataclass
from pathlib import Path
import os


@dataclass
class Settings:
    docs_dir: Path = Path("knowledge")
    index_dir: Path = Path("index")
    chroma_collection: str = "medical_docs"
    embedding_model: str = "multi-qa-mpnet-base-dot-v1"
    whisper_model_size: str = "small"
    whisper_device: str = "cpu"
    whisper_compute_type: str = "int8"
    whisper_auto_detect: bool = True
    whisper_lang_min_conf: float = 0.60
    top_k: int = 8
    retrieval_fetch_k: int = 24
    retrieval_alpha_semantic: float = 0.72
    retrieval_alpha_lexical: float = 0.28
    retrieval_min_score: float = 0.16
    retrieval_max_per_source: int = 3
    llm_provider: str = "ollama"
    use_langchain: bool = True
    ollama_base_url: str = "http://127.0.0.1:11434/v1"
    ollama_model: str = "llama3.1:latest"
    openai_model: str = "gpt-4.1-mini"
    language: str = "fr"
    silence_threshold_rms: int = 400
    silence_min_ms: int = 1200
    min_voice_ms: int = 300
    analysis_window_ms: int = 30
    tts_timeout_sec: int = 20
    tts_max_chars: int = 1200
    memory_turns: int = 4
    
    # System prompts in different languages
    _SYSTEM_PROMPTS = {
        "fr": (
            "Tu es un assistant médical spécialisé pour délégué médical. "
            "RÈGLES STRICTES: "
            "1. Réponds UNIQUEMENT avec des informations présentes dans les documents fournis. "
            "2. Cite TOUJOURS la source exacte (produit, indication, document). "
            "3. Si l'information n'existe pas, dis clairement 'Je n'ai pas trouvé cette information'. "
            "4. JAMAIS d'invention sur: composition, posologie, contre-indications, indications, effets secondaires. "
            "5. Pour questions sensibles (interactions, EI graves): recommande la vérification avec source officielle. "
            "6. Structu​re ta réponse: [Produit] → [Indication/Posologie] → [Source]"
        ),
        "en": (
            "You are a medical assistant specialist for medical delegates. "
            "STRICT RULES: "
            "1. Answer ONLY with information from provided documents. "
            "2. ALWAYS cite exact source (product, indication, document). "
            "3. If information not found, clearly state 'I did not find this information'. "
            "4. NEVER invent: composition, dosage, contraindications, indications, side effects. "
            "5. For sensitive questions (interactions, severe AE): recommend official source verification. "
            "6. Structure response: [Product] → [Indication/Dosage] → [Source]"
        ),
        "es": (
            "Eres un asistente médico especializado para delegados médicos. "
            "REGLAS ESTRICTAS: "
            "1. Responde SOLO con información de los documentos proporcionados. "
            "2. SIEMPRE cita la fuente exacta (producto, indicación, documento). "
            "3. Si la información no existe, indica claramente 'No encontré esta información'. "
            "4. NUNCA inventes: composición, dosis, contraindicaciones, indicaciones, efectos adversos. "
            "5. Para preguntas sensibles (interacciones, EA graves): recomienda verificación con fuente oficial. "
            "6. Estructura: [Producto] → [Indicación/Dosis] → [Fuente]"
        )
    }
    
    @property
    def system_prompt(self) -> str:
        return self._SYSTEM_PROMPTS.get(self.language, self._SYSTEM_PROMPTS["fr"])

    @staticmethod
    def from_env() -> "Settings":
        docs_dir = Path(os.getenv("DOCS_DIR", "knowledge"))
        index_dir = Path(os.getenv("INDEX_DIR", "index"))
        chroma_collection = os.getenv("CHROMA_COLLECTION", "medical_docs")
        embedding_model = os.getenv("EMBEDDING_MODEL", "default")
        whisper_model_size = os.getenv("WHISPER_MODEL_SIZE", "small")
        whisper_device = os.getenv("WHISPER_DEVICE", "cpu")
        whisper_compute_type = os.getenv("WHISPER_COMPUTE_TYPE", "int8")
        whisper_auto_detect = os.getenv("WHISPER_AUTO_DETECT", "true").strip().lower() in {"1", "true", "yes", "on"}
        whisper_lang_min_conf = float(os.getenv("WHISPER_LANG_MIN_CONF", "0.60"))
        top_k = int(os.getenv("TOP_K", "4"))
        retrieval_fetch_k = int(os.getenv("RETRIEVAL_FETCH_K", "24"))
        retrieval_alpha_semantic = float(os.getenv("RETRIEVAL_ALPHA_SEMANTIC", "0.72"))
        retrieval_alpha_lexical = float(os.getenv("RETRIEVAL_ALPHA_LEXICAL", "0.28"))
        retrieval_min_score = float(os.getenv("RETRIEVAL_MIN_SCORE", "0.16"))
        retrieval_max_per_source = int(os.getenv("RETRIEVAL_MAX_PER_SOURCE", "3"))
        llm_provider = os.getenv("LLM_PROVIDER", "ollama")
        use_langchain = os.getenv("USE_LANGCHAIN", "true").strip().lower() in {"1", "true", "yes", "on"}
        ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434/v1")
        ollama_model = os.getenv("OLLAMA_MODEL", "llama3.1:latest")
        openai_model = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
        language = os.getenv("LANGUAGE", "fr")
        silence_threshold_rms = int(os.getenv("SILENCE_THRESHOLD_RMS", "400"))
        silence_min_ms = int(os.getenv("SILENCE_MIN_MS", "1200"))
        min_voice_ms = int(os.getenv("MIN_VOICE_MS", "300"))
        analysis_window_ms = int(os.getenv("ANALYSIS_WINDOW_MS", "30"))
        tts_timeout_sec = int(os.getenv("TTS_TIMEOUT_SEC", "20"))
        tts_max_chars = int(os.getenv("TTS_MAX_CHARS", "1200"))
        memory_turns = int(os.getenv("MEMORY_TURNS", "4"))
        return Settings(
            docs_dir=docs_dir,
            index_dir=index_dir,
            chroma_collection=chroma_collection,
            embedding_model=embedding_model,
            whisper_model_size=whisper_model_size,
            whisper_device=whisper_device,
            whisper_compute_type=whisper_compute_type,
            whisper_auto_detect=whisper_auto_detect,
            whisper_lang_min_conf=whisper_lang_min_conf,
            top_k=top_k,
            retrieval_fetch_k=retrieval_fetch_k,
            retrieval_alpha_semantic=retrieval_alpha_semantic,
            retrieval_alpha_lexical=retrieval_alpha_lexical,
            retrieval_min_score=retrieval_min_score,
            retrieval_max_per_source=retrieval_max_per_source,
            llm_provider=llm_provider,
            use_langchain=use_langchain,
            ollama_base_url=ollama_base_url,
            ollama_model=ollama_model,
            openai_model=openai_model,
            language=language,
            silence_threshold_rms=silence_threshold_rms,
            silence_min_ms=silence_min_ms,
            min_voice_ms=min_voice_ms,
            analysis_window_ms=analysis_window_ms,
            tts_timeout_sec=tts_timeout_sec,
            tts_max_chars=tts_max_chars,
            memory_turns=memory_turns,
        )