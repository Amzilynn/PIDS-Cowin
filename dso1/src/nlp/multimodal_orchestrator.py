import threading
import queue
import time
import pandas as pd
from groq import Groq
from dotenv import load_dotenv
from dso1.src.nlp import stt, voice, prompts

# Load variables from .env
load_dotenv()

class MultimodalOrchestrator:
    """
    Orchestrates CV signals and NLP conversational flow.
    Ensures CV analysis continues during STT/LLM/TTS phases.
    """
    def __init__(self):
        self.client = Groq()
        self.state = "IDLE"  # IDLE, LISTENING, THINKING, SPEAKING
        self.transcript_queue = queue.Queue()
        self.audio_queue = queue.Queue()
        
        # Load Semantic RAG Data
        from dso1.src.rag.rag_build import load_or_build_rag
        from dso1.src.rag.retriever import Retriever
        print("[INFO] Initializing RAG Database (this may take a moment)...")
        store = load_or_build_rag()
        self.retriever = Retriever(store)
        print("[INFO] RAG Database ready.")

    def get_context(self, query):
        """Retrieve context dynamically using semantic search via RAG."""
        context = "Relevant Product Information:\n"
        try:
            # Retriever returns a list of matched text strings
            results = self.retriever.retrieve(query, k=3)
            if results:
                for res in results:
                    context += f"{res}\n---\n"
            else:
                context += "No relevant product data found."
        except Exception as e:
            print(f"[ERROR] RAG retrieval failed: {e}")
            context += "No product data available."
        return context

    def request_response(self, user_input):
        """Get response from Groq using Samar's logic but with RAG context."""
        context = self.get_context(user_input)
        full_prompt = f"{prompts.SYSTEM_PROMPT}\n\nCONTEXT:\n{context}\n\nUSER: {user_input}"
        
        self.state = "THINKING"
        completion = self.client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": full_prompt}],
            temperature=0.7,
            max_tokens=1024,
        )
        response_text = completion.choices[0].message.content
        self.state = "SPEAKING"
        return response_text

    def start_listening(self):
        """Start a background thread to record and transcribe audio."""
        def _listen():
            self.state = "LISTENING"
            try:
                # Use Samar's function
                text, lang = stt.record_and_transcribe(duration=5)
                if text.strip():
                    self.transcript_queue.put((text, lang))
            except Exception as e:
                print(f"[ERROR] STT failed: {e}")
            finally:
                self.state = "IDLE"

        threading.Thread(target=_listen, daemon=True).start()

    def speak_response(self, text, lang="fr"):
        """Speak response in a background thread."""
        def _speak():
            self.state = "SPEAKING"
            try:
                # Use Samar's function
                voice.speak(text, lang)
            except Exception as e:
                print(f"[ERROR] TTS failed: {e}")
            finally:
                self.state = "IDLE"

        threading.Thread(target=_speak, daemon=True).start()
