import json
from openai import OpenAI

class NLPEvaluator:
    """
    Système de Fact-Checking et d'évaluation NLP Avancé.
    Agit comme un "LLM-as-a-Judge" déterministe en comparant strictement
    la transcription du délégué à la vérité documentaire (Base de données).
    """

    def __init__(self, client: OpenAI, model_name: str = "hosted_vllm/Llama-3.1-70B-Instruct"):
        self.client = client
        self.model_name = model_name

    def _normalize_transcript(self, text: str) -> str:
        """Normalise les variantes STT courantes pour améliorer la précision du fact-checking."""
        import re
        replacements = [
            # Laboratoire
            (r'\bvitelle\b', 'Vital'), (r'\bvitale\b', 'Vital'),
            (r'\bveetale\b', 'Vital'), (r'\bvittale\b', 'Vital'),
            # Produits
            (r'\bbactole\b', 'Bactol'), (r'\bbectol\b', 'Bactol'),
            (r'\bpactole\b', 'Bactol'), (r'\bbacktol\b', 'Bactol'),
            (r'\bcalmos\b', 'Calmoss'), (r'\bcalmosse\b', 'Calmoss'),
            # Composants
            (r'\bbenzalkon[iy]um\b', 'benzalkonium'),
        ]
        result = text
        for pattern, repl in replacements:
            result = re.sub(pattern, repl, result, flags=re.IGNORECASE)
        return result

    def evaluate_session(self, messages: list, product: dict) -> dict:
        """
        Compare les affirmations de l'utilisateur avec la Fiche Produit.
        """
        # 1. Extraction du discours
        user_texts = [m["content"] for m in messages if m["role"] == "user"]
        if not user_texts:
            return self._empty_result()
            
        # Normalisation des variantes STT avant évaluation
        normalized_texts = [self._normalize_transcript(t) for t in user_texts]
        full_transcript = "\n".join(f"- Délégué: {txt}" for txt in normalized_texts)
        
        # 2. Base de Vérité (Ground Truth)
        if not product:
            product_str = "ATTENTION: Aucun produit n'a été spécifié en base. Évaluez de manière générique."
        else:
            product_str = f"""
NOM DU PRODUIT : {product.get('name', 'N/A')}
DESCRIPTION : {product.get('description', 'N/A')}
INDICATIONS : {product.get('indications', 'N/A')}
COMPOSITIONS : {product.get('compositions', 'N/A')}
CONSEILS D'UTILISATION : {product.get('usage_advice', 'N/A')}
"""

        # 3. Prompt de Fact-Checking strict
        prompt = f"""
Tu es un Evaluateur Expert et un Médecin Formateur intraitable.
Ton rôle est de faire un FACT-CHECKING RIGOUREUX du discours d'un délégué commercial par rapport à la FICHE RÉFÉRENCE de son produit.

--- FICHE PRODUIT DE RÉFÉRENCE (LA VÉRITÉ ABSOLUE) ---
{product_str}

--- DISCOURS DU DÉLÉGUÉ ---
{full_transcript}

--- INSTRUCTIONS D'ANALYSE ---
1. Isole chaque information médicale ou commerciale donnée par le délégué.
2. Vérifie si elle correspond EXACTEMENT aux données de la Fiche Produit.
3. Repère les INVENTIONS (Allégations mensongères ou hallucination de principe actif).
4. Repère les OMISSIONS GRAVES (Ex: Il a parlé du produit mais a oublié de donner la posologie ou l'indication principale).

--- FORMAT DE SORTIE OBLIGATOIRE ---
RETOURNE UNIQUEMENT UN JSON VALIDE avec la structure exacte suivante, rien de plus. Ta réponse doit commencer par {{ et finir par }}.

{{
    "product_knowledge_score": 0.0, // (NOTE de 0.0 à 1.0) Sanctionne lourdement les mensonges et oublis.
    "vocabulary_richness": 0.0, // (NOTE de 0.0 à 1.0) Richesse lexicale, fluidité et vocabulaire médical.
    "feedback_summary": "...", // Résumé global (2 phrases max).
    "mistakes": [
        // Liste précise (String) des erreurs : ce qui a été dit vs ce qui aurait dû être dit. Ex: "A dit X au lieu de Y", "A omis l'ingrédient X". Laisse vide si parfait.
    ],
    "correct_points": [
        // Liste précise (String) des bonnes informations placées.
    ]
}}
"""
        
        try:
            res = self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0 # Température 0 pour un maximum de factualité déterministe
            )
            content = res.choices[0].message.content.strip()
            print(f"[NLPEvaluator] Reponse brute du LLM : {content[:200]}...")
            
            # Nettoyage Markdown au cas où
            if content.startswith("```json"):
                content = content[7:-3]
            elif content.startswith("```"):
                content = content[3:-3]
                
            data = json.loads(content)
            
            # Validation de la structure
            return {
                "product_knowledge_score": float(data.get("product_knowledge_score", 0.0)),
                "vocabulary_richness":     float(data.get("vocabulary_richness",     0.0)),
                "feedback_summary":        str(data.get("feedback_summary", "")),
                "mistakes":                list(data.get("mistakes", [])),
                "correct_points":          list(data.get("correct_points", []))
            }
            
        except Exception as e:
            print(f"[NLPEvaluator] Erreur LLM: {e}")
            return self._empty_result()
            
    def _empty_result(self) -> dict:
        return {
            "product_knowledge_score": 0.0,
            "vocabulary_richness": 0.0,
            "feedback_summary": "Aucune prise de parole détectée ou erreur d'analyse.",
            "mistakes": [],
            "correct_points": []
        }
