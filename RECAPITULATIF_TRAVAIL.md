# Récapitulatif du Projet : AI Training Simulator (PIDS-Cowin)

Ce document résume l'état actuel de l'avancement du projet, sa structure technique et le fonctionnement détaillé du pipeline d'intelligence artificielle.

---

## 1. Vision Globale du Projet
L'objectif est de créer un simulateur d'entraînement pour délégués médicaux. Un utilisateur (le délégué) interagit avec un avatar IA qui incarne un professionnel de santé (ex: Médecin, Pharmacien). Le système (RAG/NLP) évalue  le comportement non-verbal (Émotions, Posture, Ton de voix).

---

## 2. Structure Complète du Projet

Le projet est divisé en deux piliers principaux : le **Frontend** (Interface Utilisateur) et le **Backend** (Moteur IA).

### A. Frontend (React) - `front/`
- **Views** (`src/views/`) :
    - `delegate/` : Sélection du profil de l'IA (Délégués).
    - `training/` : L'interface de simulation avec flux vidéo et chat.
    - `EvaluationResults.jsx` : Présentation des scores finaux et graphiques de performance.
- **Components** (`src/components/`) :
    - `CameraPanel.jsx` : Gestion de la capture vidéo et affichage du flux analysé.
    - `ChatPanel.jsx` : Interface de discussion en temps réel.
- **Controllers** : Logique de communication avec l'API FastAPI.

### B. Backend (Python/FastAPI) - `dso1/src/`
- **API** (`api/routes/`) : 
    - `training.py` : Points d'entrée pour démarrer/arrêter une session, flux vidéo (`video_feed`) et flux chat (`chat_feed`).
- **NLP & Avatar** (`avatar/`, `nlp/`) :
    - `stt.py` : Transcription de la voix (Whisper).
    - `voice.py` : Synthèse vocale de l'avatar (Edge-TTS).
    - `rag/` : Moteur de recherche documentaire pour les connaissances produits/médicaments.
- **Évaluation** (`evaluation/`) :
    - `face_emotion.py` : Analyse des émotions faciales (EfficientNet).
    - `body_language.py` : Analyse de la posture et gestuelle (MediaPipe).
    - `tone_analysis.py` : Analyse du ton et du débit de parole.
    - `fusion.py` : Algorithme de fusion des scores pour une évaluation globale.
- **Orchestration** (`session.py`) :
    - Le cœur du système qui gère les threads de conversation et d'analyse.

---

## 3. Pipeline Complet de Simulation (Étape par Étape)

Le pipeline fonctionne de manière asynchrone pour garantir une fluidité maximale.

### Étape 1 : Initialisation
1.  L'utilisateur choisit un "Délégué" (IA) sur le Frontend.
2.  Le Front envoie une requête `POST /start` au Backend.
3.  Le Backend initialise le **RAG** (connaissances) et lance l'**EvaluationThread**.

### Étape 2 : L'Analyse en Continu (Thread 1)
- La caméra capture les images en temps réel.
- Les modules **Face**, **Body** et **Tone** tournent en boucle.
- Un **HUD** (affichage tête haute) est généré sur le flux vidéo pour montrer les scores en direct (Stress, Confiance, Engagement).
- **Principe de logging** : Le système ne logue les scores que lorsque le délégué parle (détecté par le flag `avatar_speaking`), afin de ne pas fausser l'évaluation par les réponses de l'IA.

### Étape 3 : La Boucle Conversationnelle (Thread 2)
1.  **Écoute (STT)** : Le système enregistre la voix de l'utilisateur et la transcrit avec Whisper.
2.  **Réflexion (LLM + RAG)** : 
    - Le texte est analysé. Si des mots-clés "Produit" sont détectés (ex: médicament, posologie), le RAG extrait les fiches techniques.
    - Le contexte est envoyé à **Groq (Llama 3)** pour générer une réponse fluide et experte.
3.  **Parole (TTS)** : L'avatar répond vocalement. Pendant ce temps, l'évaluation comportementale est mise en pause vis-à-vis du logging.

### Étape 4 : Conclusion et Rapport
1.  L'utilisateur termine la session.
2.  Le Backend compile les logs JSON, calcule les moyennes finales via la **Fusion**, et met à jour le score du délégué dans `delegues.csv`.
3.  Un **Rapport PDF** est généré automatiquement.
4.  Le Frontend affiche les résultats finaux avec des graphiques.

---

## 4. Technologies Clés
- **React + Vite** (Frontend)
- **FastAPI** (Backend API)
- **Groq Llama 3** (Cognition)
- **Whisper & Edge-TTS** (Voix)
- **OpenCV & MediaPipe** (Vision)
- **FAISS / SentenceTransformers** (RAG)

---
