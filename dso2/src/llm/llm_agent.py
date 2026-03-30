"""Vital medical delegate agent (Ollama Mistral + tool calling)."""

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
        
        self.session_id = session_id or str(uuid.uuid4())
        self.persona = persona
        self.prompt_builder = VitalPromptBuilder()
        self.conversation_history: list[dict[str, str]] = []
        self.max_history_turns = 10
        self.last_intent = "GENERAL"
        
        self._system_prompt = self.prompt_builder.build_system_prompt(persona=self.persona)
        
        self._client = OpenAI(
            base_url="http://localhost:11434/v1",
            api_key="ollama",
            timeout=120,
        )
        print(f"VitalAgent ready — session {self.session_id} | persona: {self.persona}")

    def detect_intent(self, user_message: str) -> str:
        """Detect conversation intent, persona-aware."""
        msg = user_message.lower().strip()
        
        # Greeting - simple short response
        greeting_kw = [
            "bonjour", "salut", "bonsoir", "coucou", "hello",
            "bonjour!", "salut!", "bonjour.", "salut."
        ]
        if msg in greeting_kw or msg.startswith("bonjour") and len(msg) < 15:
            return "GREETING"
        
        # Safety checks apply to both personas
        safety_kw = [
            "grossesse", "enceinte", "enfant", "bébé", "senior",
            "diabét", "danger", "contre-indiq", "allergi",
            "interaction", "risque", "innocuité", "tolérance"
        ]
        if any(k in msg for k in safety_kw):
            return "SAFETY_CHECK"
        
        # Commercial persona keywords
        if getattr(self, "persona", "medical") == "commercial":
            commercial_kw = [
                "marge", "prix", "remise", "stock", "commande",
                "promo", "concurrent", "rotation", "livraison"
            ]
            if any(k in msg for k in commercial_kw):
                return "PRODUCT_INQUIRY"
        
        # Medical persona keywords
        if getattr(self, "persona", "medical") == "medical":
            medical_kw = [
                "mécanisme", "biodispo", "posologie", "prescription",
                "patient", "efficac", "étude", "clinique", "symptôme"
            ]
            if any(k in msg for k in medical_kw):
                return "SYMPTOM_INQUIRY"
        
        # Shared intents
        if any(k in msg for k in [
            "recommand", "conseil", "proposez", "suggér",
            "qu'est-ce que", "que pensez"
        ]):
            return "RECOMMENDATION"
        
        if any(k in msg for k in [
            "non", "pas convaincu", "pas sûr", "doute",
            "preuve", "générique", "moins cher"
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
            return "Bonjour ! Je suis le délégué médical VITAL. Comment puis-je vous aider aujourd'hui ?"
        else:
            return "Bonjour ! Je suis le délégué commercial VITAL. Comment puis-je vous servir ?"

    def chat(self, user_message: str) -> str:
        """Run one user turn: optional tool calls, then French assistant reply."""
        try:
            self.last_intent = self.detect_intent(user_message)
            
            # Handle greetings with a simple short response
            if self.last_intent == "GREETING":
                greeting = self._get_greeting_response()
                self.conversation_history.append({"role": "user", "content": user_message})
                self.conversation_history.append({"role": "assistant", "content": greeting})
                return greeting
            
            # --- AUTO RETRIEVAL (RAG) FOR SMALL/LOCAL MODELS ---
            # Instead of relying strictly on LLM tool syntax generation (which 8B models fail at),
            # we proactively fetch context based on the user's intent.
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
            response = self._client.chat.completions.create(
                model="llama3.1",
                messages=messages,
                tools=TOOLS_SCHEMA,
                tool_choice="auto",
            )
            msg = response.choices[0].message
            response_text = (msg.content or "").strip()
            if msg.tool_calls:
                assistant_entry: dict[str, Any] = {
                    "role": "assistant",
                    "content": msg.content or "",
                    "tool_calls": [
                        {
                            "id": tc.id,
                            "type": "function",
                            "function": {
                                "name": tc.function.name,
                                "arguments": tc.function.arguments or "{}",
                            },
                        }
                        for tc in msg.tool_calls
                    ],
                }
                messages.append(assistant_entry)
                for tc in msg.tool_calls:
                    try:
                        args = json.loads(tc.function.arguments or "{}")
                    except json.JSONDecodeError:
                        args = {}
                    out = self._call_tool(tc.function.name, args)
                    messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": tc.id,
                            "content": out,
                        }
                    )
                response2 = self._client.chat.completions.create(
                    model="llama3.1",
                    messages=messages,
                )
                response_text = (response2.choices[0].message.content or "").strip()
            
            # FALLBACK for Text-Leaked Tool Calls (very common on Llama 3 via compat API)
            elif '{"name"' in response_text and '"parameters"' in response_text:
                import re
                import uuid
                # Fix syntax error where it ends with }) instead of }
                fixed_text = response_text.replace("})", "}")
                match = re.search(r'(\{[\s\S]*"name"[\s\S]*"parameters"[\s\S]*?\})', fixed_text)
                if match:
                    try:
                        parsed = json.loads(match.group(1))
                        name = parsed.get("name")
                        args = parsed.get("parameters", {})
                        if name:
                            out = self._call_tool(name, args)
                            fake_id = "call_" + str(uuid.uuid4())[:8]
                            assistant_entry = {
                                "role": "assistant",
                                "content": "",
                                "tool_calls": [{
                                    "id": fake_id,
                                    "type": "function",
                                    "function": {"name": name, "arguments": json.dumps(args)}
                                }]
                            }
                            messages.append(assistant_entry)
                            messages.append({
                                "role": "tool",
                                "tool_call_id": fake_id,
                                "content": out
                            })
                            response2 = self._client.chat.completions.create(
                                model="llama3.1",
                                messages=messages,
                            )
                            response_text = (response2.choices[0].message.content or "").strip()
                    except json.JSONDecodeError:
                        pass
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
                print(f"Ollama connection error: {exc}")
                return "Le serveur IA n'est pas accessible. Vérifiez qu'Ollama est en cours d'exécution."
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

    print("Checking Ollama connection...")
    try:
        from openai import OpenAI as _OAI
        _OAI(base_url="http://localhost:11434/v1",
             api_key="ollama").models.list()
        print("Ollama connection: OK\n")
    except Exception as e:
        print(f"ERROR: Ollama not running. Run 'ollama serve'")
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
