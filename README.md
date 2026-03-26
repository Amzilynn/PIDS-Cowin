# Projet Speech-to-Speech avec RAG (Délégué médical)

Ce MVP permet à un délégué médical de répondre à un médecin à partir de documents produits (PDF/TXT/CSV) via un pipeline:

1. **Ingestion RAG** des documents (découpage + index TF-IDF)
2. **Question en texte ou audio**
3. **Retrieval** des passages pertinents
4. **Réponse** (avec OpenAI si clé disponible, sinon mode fallback basé documents)
5. **Synthèse vocale** de la réponse

Par défaut, le projet est configuré pour utiliser **Ollama en local**.

---

## 1) Installation

Depuis le dossier `speech_rag_delegate`:

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Copiez ensuite `.env.example` vers `.env` et adaptez si besoin.

---

## 1.1) Démarrer Ollama local

Dans un terminal séparé:

```bash
ollama serve
```

Téléchargez ensuite un modèle (exemple):

```bash
ollama pull llama3.1:8b
```

Le `.env` par défaut pointe vers `http://127.0.0.1:11434/v1`.

---

## 2) Préparer les données

- Placez vos fichiers PDF/TXT/CSV dans le dossier `knowledge/`
- Exemple:

```text
knowledge/
  produit_A.pdf
  produit_B.txt
  produits.csv
```

---

## 3) Construire l'index RAG

```bash
python build_index.py
```

Cela génère un dossier `index/` avec:

- `chunks.json`
- `vectorizer.pkl`
- `tfidf.pkl`

---

## 4) Lancer l'application Speech-to-Speech

```bash
python gradio_app.py
```

Puis ouvrez l'URL locale affichée (souvent http://127.0.0.1:7860).

---

## 5) Notes importantes (médical)

- Le système doit rester **strictement ancré** aux documents.
- Toujours vérifier les informations critiques (posologie, CI, interactions) dans la source officielle.
- En production: journalisation, contrôle qualité, traçabilité, et validation réglementaire sont nécessaires.

---

## 6) Option OpenAI

Par défaut: `LLM_PROVIDER=ollama`.
La génération de réponse passe par **LangChain** par défaut (`USE_LANGCHAIN=true`).

Si vous voulez OpenAI:

- mettez `LLM_PROVIDER=openai`
- configurez `OPENAI_API_KEY`

Si aucun provider valide n'est disponible, le projet fonctionne en mode fallback extractif.

Vous pouvez désactiver LangChain (mode SDK direct) avec:

```env
USE_LANGCHAIN=false
```

---

## 7) Mémoire de conversation

L'application conserve les derniers tours de dialogue pour améliorer les questions de suivi.

- Variable: `MEMORY_TURNS`
- Valeur par défaut: `4` (soit 4 tours utilisateur + assistant)

Exemple dans `.env`:

```env
MEMORY_TURNS=6
```
