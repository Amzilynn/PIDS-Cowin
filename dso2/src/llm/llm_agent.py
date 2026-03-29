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

    def __init__(self, session_id: str | None = None) -> None:
        """Initialize session, system prompt, and empty user/assistant history."""
        self.session_id = session_id or str(uuid.uuid4())
        self.prompt_builder = VitalPromptBuilder()
        self.conversation_history: list[dict[str, str]] = []
        self.max_history_turns = 10
        self.last_intent = "GENERAL"
        self._system_prompt = self.prompt_builder.build_system_prompt(None)
        self._client = OpenAI(
            base_url="http://localhost:11434/v1",
            api_key="ollama",
        )
        print(f"VitalAgent ready — session {self.session_id}")

    def detect_intent(self, user_message: str) -> str:
        """Keyword-based intent label for logging (no LLM call)."""
        m = user_message.lower()
        safety_kw = [
            "grossesse",
            "enceinte",
            "enfant",
            "bébé",
            "bebe",
            "senior",
            "diabét",
            "danger",
            "contre-indiq",
            "allergi",
            "interaction",
            "risque",
        ]
        reco_kw = [
            "recommand",
            "conseil",
            "proposez",
            "suggér",
            "qu'est-ce que",
            "que pensez",
        ]
        symptom_kw = [
            "symptôme",
            "souffre",
            "problème",
            "traitement",
            "patient",
            "pathologi",
            "maladie",
            "douleur",
        ]
        product_kw = [
            "phytofane",
            "ferbiotic",
            "pulmax",
            "fongiderm",
            "pédiakids",
            "pediakids",
            "vitosine",
            "vaseline",
            "vital",
        ]
        objection_kw = [
            "pas convaincu",
            "pas sûr",
            "doute",
            "preuve",
            "étude",
            "concurrent",
            "moins cher",
            "générique",
            "efficac",
        ]
        if any(k in m for k in safety_kw):
            return "SAFETY_CHECK"
        if any(k in m for k in reco_kw):
            return "RECOMMENDATION"
        if any(k in m for k in symptom_kw):
            return "SYMPTOM_INQUIRY"
        if any(k in m for k in product_kw):
            return "PRODUCT_INQUIRY"
        if any(k in m for k in objection_kw) or re.search(r"\bnon\b", m):
            return "OBJECTION"
        return "GENERAL"

    def _call_tool(self, tool_name: str, tool_args: dict[str, Any]) -> str:
        """Execute a tool and return JSON string for the model."""
        try:
            result = dispatch_tool(tool_name, tool_args or {})
            return json.dumps(result, ensure_ascii=False, default=str)
        except Exception as exc:
            return json.dumps({"error": str(exc)}, ensure_ascii=False)

    def chat(self, user_message: str) -> str:
        """Run one user turn: optional tool calls, then French assistant reply."""
        try:
            self.last_intent = self.detect_intent(user_message)
            self.conversation_history.append(
                {"role": "user", "content": user_message}
            )
            messages: list[dict[str, Any]] = [
                {"role": "system", "content": self._system_prompt},
                *self.conversation_history,
            ]
            response = self._client.chat.completions.create(
                model="mistral",
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
                    model="mistral",
                    messages=messages,
                )
                response_text = (response2.choices[0].message.content or "").strip()
            self.conversation_history.append(
                {"role": "assistant", "content": response_text}
            )
            max_msgs = self.max_history_turns * 2
            if len(self.conversation_history) > max_msgs:
                self.conversation_history = self.conversation_history[-max_msgs:]
            return response_text
        except Exception as exc:
            print(exc)
            return (
                "Je suis désolé, je n'ai pas pu traiter votre "
                "demande. Pourriez-vous reformuler?"
            )

    def reset_conversation(self) -> None:
        """Clear history and rebuild the default system prompt."""
        self.conversation_history = []
        self._system_prompt = self.prompt_builder.build_system_prompt(None)
        print(f"Conversation reset — session {self.session_id}")

    def get_conversation_summary(self) -> dict[str, Any]:
        """Return session id, user turn count, and last detected intent."""
        turns = sum(1 for m in self.conversation_history if m.get("role") == "user")
        return {
            "session_id": self.session_id,
            "turns": turns,
            "last_intent": self.last_intent,
        }


if __name__ == "__main__":
    import sys as _sys

    print("Checking Ollama connection...")
    try:
        from openai import OpenAI as _OC

        test_client = _OC(
            base_url="http://localhost:11434/v1",
            api_key="ollama",
        )
        test_client.models.list()
        print("Ollama connection: OK")
    except Exception as e:
        print("ERROR: Ollama is not running.")
        print("Run 'ollama serve' in a separate terminal first.")
        print(f"Detail: {e}")
        _sys.exit(1)

    agent = VitalAgent(session_id="test-001")
    print("\n--- CONVERSATION TESTS ---\n")

    exchanges = [
        "Bonjour, je cherche quelque chose pour la chute "
        "de cheveux chez mes patients.",
        "Est-ce que ce produit est adapté pour une femme "
        "enceinte ?",
        "Quelles sont les interactions médicamenteuses "
        "possibles avec la vitamine E ?",
        "Qu'est-ce que vous recommandez pour un enfant "
        "qui a une toux persistante ?",
        "Je ne suis pas convaincu de l'efficacité des "
        "compléments alimentaires en général.",
    ]

    for message in exchanges:
        print(f"Médecin: {message}")
        response = agent.chat(message)
        print(f"Délégué VITAL: {response}")
        print("-" * 60)
        # On réinitialise l'historique pour le prochain test indépendant
        agent.reset_conversation()

    print(f"\nSummary: {agent.get_conversation_summary()}")
    print("\n--- TESTS COMPLETE ---")
