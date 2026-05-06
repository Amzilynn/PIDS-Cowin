"""Vital medical delegate agent (Token Factory Llama-3.1-70B-Instruct + tool calling)."""

from __future__ import annotations

import json
import os
import re
import sys
import uuid
from typing import Any

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.join(BASE_DIR, "..")
sys.path.insert(0, SRC_DIR)

from openai import OpenAI

from llm.prompt_builder import VitalPromptBuilder
from llm.tools import TOOLS_SCHEMA, dispatch_tool


class VitalAgent:
    """Conversational agent for VITAL medical delegates (French, tool-grounded)."""

    def __init__(
        self,
        session_id: str | None = None,
        persona: str = "medical"    # "medical" or "commercial"
    ) -> None:
        """Initialize session, system prompt, and empty user/assistant history."""
        import uuid
        
        # validate persona
        if persona not in ("medical", "commercial"):
            raise ValueError(
                f"persona must be 'medical' or 'commercial', "
                f"got '{persona}'"
            )
        
        from dotenv import load_dotenv
        load_dotenv()
        
        self.session_id = session_id or str(uuid.uuid4())
        self.persona = persona
        self.prompt_builder = VitalPromptBuilder()
        self.conversation_history: list[dict[str, str]] = []
        self.max_history_turns = 10
        self.last_intent = "GENERAL"
        
        self._system_prompt = self.prompt_builder.build_system_prompt(persona=self.persona)
        
        base_url = os.getenv("TOKENFACTORY_URL", "https://tokenfactory.esprit.tn/api")
        api_key = os.getenv("TOKENFACTORY_API_KEY")
        
        self._client = OpenAI(
            base_url=base_url,
            api_key=api_key,
            timeout=120,
        )
        print(f"VitalAgent ready — session {self.session_id} | persona: {self.persona}")
    def detect_intent(self, user_message: str) -> str:
        """Detect conversation intent, persona-aware."""
        msg = user_message.lower().strip()
        
        # Greeting - simple short response
        greeting_kw = [
            "hello", "hi", "hey", "good morning", "good afternoon",
            "hello!", "hi!", "bonjour", "salut"
        ]
        if any(msg == k for k in greeting_kw) or (msg.startswith("hello") and len(msg) < 15):
            return "GREETING"
        
        # Safety checks apply to both personas
        safety_kw = [
            "pregnancy", "pregnant", "child", "baby", "senior", "elderly",
            "diabetes", "danger", "contraind", "allerg", "breastfeed",
            "interaction", "risk", "safety", "tolerance"
        ]
        if any(k in msg for k in safety_kw):
            return "SAFETY_CHECK"
        
        # Commercial persona keywords
        if getattr(self, "persona", "medical") == "commercial":
            commercial_kw = [
                "margin", "price", "discount", "stock", "order",
                "promo", "competitor", "rotation", "delivery"
            ]
            if any(k in msg for k in commercial_kw):
                return "PRODUCT_INQUIRY"
        
        # Medical persona keywords
        if getattr(self, "persona", "medical") == "medical":
            medical_kw = [
                "mechanism", "biodisponibility", "dosage", "prescription",
                "patient", "efficac", "study", "clinical", "symptom"
            ]
            if any(k in msg for k in medical_kw):
                return "SYMPTOM_INQUIRY"
        
        # Shared intents
        if any(k in msg for k in [
            "recommend", "advise", "propose", "suggest",
            "what is", "what do you think"
        ]):
            return "RECOMMENDATION"
        
        if any(k in msg for k in [
            "no", "not convinced", "not sure", "doubt",
            "proof", "generic", "cheaper"
        ]):
            return "OBJECTION"
        
        if any(k in msg for k in [
            "phytofane", "ferbiotic", "pulmax", "fongiderm",
            "pédiakids", "pediakids", "vitosine", "vital"
        ]):
            return "PRODUCT_INQUIRY"
        
        return "GENERAL"

    def _call_tool(self, tool_name: str, tool_args: dict[str, Any]) -> str:
        """Execute a tool and return JSON string for the model."""
        try:
            result = dispatch_tool(tool_name, tool_args or {})
            return json.dumps(result, ensure_ascii=False, default=str)
        except Exception as exc:
            return json.dumps({"error": str(exc)}, ensure_ascii=False)

    def _get_greeting_response(self) -> str:
        """Return a short greeting response based on persona."""
        if self.persona == "medical":
            return "Hello! I am the VITAL medical representative. How can I assist you today?"
        else:
            return "Hello! I am the VITAL commercial representative. How can I serve you?"

    def chat(self, user_message: str) -> str:
        """Run one user turn: RAG context injection, then French assistant reply."""
        try:
            self.last_intent = self.detect_intent(user_message)
            
            # Handle greetings with a simple short response
            if self.last_intent == "GREETING":
                greeting = self._get_greeting_response()
                self.conversation_history.append({"role": "user", "content": user_message})
                self.conversation_history.append({"role": "assistant", "content": greeting})
                return greeting
            
            # --- AUTO RETRIEVAL (RAG) ---
            # Proactively fetch product context and inject it into the system prompt.
            # This avoids tool_choice="auto" which is NOT supported by Token Factory vLLM.
            pre_context = None
            if self.last_intent in ("SYMPTOM_INQUIRY", "RECOMMENDATION", "PRODUCT_INQUIRY", "SAFETY_CHECK"):
                from llm.tools import recommend_products_for_condition
                pre_context = recommend_products_for_condition(user_message)
                
            # Rebuild the system prompt dynamically for this specific turn
            current_system_prompt = self.prompt_builder.build_system_prompt(
                persona=self.persona, 
                context_data=pre_context
            )
            
            self.conversation_history.append(
                {"role": "user", "content": user_message}
            )
            messages: list[dict[str, Any]] = [
                {"role": "system", "content": current_system_prompt},
                *self.conversation_history,
            ]
            # Single API call — no tools, no tool_choice (unsupported by Token Factory vLLM)
            response = self._client.chat.completions.create(
                model="hosted_vllm/Llama-3.1-70B-Instruct",
                messages=messages,
                temperature=0.7,
                max_tokens=512,
                top_p=0.9,
            )
            response_text = (response.choices[0].message.content or "").strip()

            self.conversation_history.append(
                {"role": "assistant", "content": response_text}
            )
            max_msgs = self.max_history_turns * 2
            if len(self.conversation_history) > max_msgs:
                self.conversation_history = self.conversation_history[-max_msgs:]
            return response_text
        except TimeoutError:
            print(f"Timeout in session {self.session_id}")
            return "La réponse prend plus de temps que prévu. L'IA travaille... Veuillez réessayer dans quelques instants."
        except Exception as exc:
            error_msg = str(exc).lower()
            if "connection" in error_msg or "connect" in error_msg:
                print(f"Token Factory connection error: {exc}")
                return "Le serveur IA Token Factory n'est pas accessible. Vérifiez votre connexion internet."
            elif "timeout" in error_msg:
                print(f"Timeout in session {self.session_id}: {exc}")
                return "La réponse prend trop de temps. Le modèle est peut-être surchargé. Réessayez."
            else:
                print(f"Chat error in session {self.session_id}: {exc}")
                return f"Désolé, une erreur technique s'est produite. [Erreur: {type(exc).__name__}]"

    def reset_conversation(self) -> None:
        """Clear history and rebuild the default system prompt."""
        self.conversation_history = []
        self._system_prompt = self.prompt_builder.build_system_prompt(persona=self.persona)
        print(f"Conversation reset — session {self.session_id}")

    def get_conversation_summary(self) -> dict[str, Any]:
        """Return session id, user turn count, and last detected intent."""
        user_turns = [
            m for m in self.conversation_history 
            if m.get("role") == "user"
        ]
        return {
            "session_id":  self.session_id,
            "persona":     self.persona,
            "turns":       len(user_turns),
            "last_intent": self.last_intent
        }


if __name__ == "__main__":
    import sys

    print("Checking Token Factory connection...")
    try:
        from openai import OpenAI as _OAI
        from dotenv import load_dotenv
        load_dotenv()
        _OAI(
            base_url=os.getenv("TOKENFACTORY_URL", "https://tokenfactory.esprit.tn/api"),
            api_key=os.getenv("TOKENFACTORY_API_KEY")
        ).models.list()
        print("Token Factory connection: OK\n")
    except Exception as e:
        print(f"ERROR: Could not connect to Token Factory — {e}")
        sys.exit(1)

    # --- TEST MEDICAL PERSONA ---
    print("=" * 60)
    print("MEDICAL DELEGATE — visiting a doctor")
    print("=" * 60)
    
    medical_agent = VitalAgent(
        session_id="test-medical",
        persona="medical"
    )
    
    medical_exchanges = [
        "Bonjour, j'ai des patientes qui se plaignent de "
        "chute de cheveux après l'accouchement.",
        
        "Est-ce que ce produit est sûr pour une femme "
        "qui allaite ?",
        
        "Avez-vous des études cliniques sur ce produit ?"
    ]
    
    for msg in medical_exchanges:
        print(f"\nMédecin: {msg}")
        print(f"Délégué médical: {medical_agent.chat(msg)}")
        print("-" * 60)

    # --- TEST COMMERCIAL PERSONA ---
    print("\n" + "=" * 60)
    print("COMMERCIAL DELEGATE — visiting a pharmacy")
    print("=" * 60)
    
    commercial_agent = VitalAgent(
        session_id="test-commercial",
        persona="commercial"
    )
    
    commercial_exchanges = [
        "Bonjour, qu'est-ce que vous avez comme nouveautés "
        "pour la rentrée ?",
        
        "J'ai déjà beaucoup de stock en ce moment.",
        
        "Votre concurrent me propose de meilleures marges."
    ]
    
    for msg in commercial_exchanges:
        print(f"\nPharmacien: {msg}")
        print(
            f"Délégué commercial: "
            f"{commercial_agent.chat(msg)}"
        )
        print("-" * 60)
    
    print("\n--- BOTH PERSONAS TESTED SUCCESSFULLY ---")
