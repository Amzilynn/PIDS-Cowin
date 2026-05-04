# Pipeline d'Intégration DSO1 — Simulateur IA & Avatar 3D

Ce document détaille le fonctionnement interne du module DSO1 pour faciliter l'intégration d'un avatar 3D (Lip-sync, expressions faciales).

## 🏗️ Architecture Globale
Le système repose sur un moteur FastAPI unifié qui gère la logique métier et la communication bidirectionnelle avec le frontend.

### Flux de données (Data Pipeline)

1. **Entrée Utilisateur** : Le texte (STT) est envoyé au backend via `/api/training/speech_text`.
2. **Cerveau IA (`session.py`)** : 
   - L'IA génère une réponse en consultant le RAG (base de connaissances produits).
   - En parallèle, le thread d'évaluation analyse les émotions du délégué (caméra).
3. **Sortie Flux (SSE)** : Le backend pousse les réponses de l'avatar et les métriques en temps réel via un flux d'événements (Server-Sent Events) sur l'endpoint `/api/training/chat_feed`.

## 📂 Fichiers Clés pour l'Intégration Avatar
- **`dso1/src/session.py`** : Cœur de l'application. C'est ici que la boucle de conversation est gérée.
- **`dso1/src/api/routes/training.py`** : Définit les points d'entrée API. Le flux SSE (`chat_feed`) est l'endroit idéal pour injecter des codes d'animation.
- **`dso1/src/avatar/voice.py`** : Gère la synthèse vocale (TTS).
- **`dso1/src/evaluation/`** : Contient les analyseurs d'émotions. Si l'avatar doit réagir aux émotions de l'utilisateur, les données proviennent d'ici.

## 🎙️ Points de synchronisation pour l'Avatar 3D
Pour animer l'avatar, l'équipe doit écouter le flux SSE `/api/training/chat_feed`. Chaque message reçu contient :
```json
{
  "role": "assistant",
  "content": "Bonjour, comment allez-vous ?",
  "metrics": { "confidence": 0.85, "stress": 0.10 }
}
