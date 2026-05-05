# Guide Technique : Pipeline DSO1 (Speech & Avatar)

Ce document explique le flux de données de l'intelligence artificielle et de la synthèse vocale pour l'intégration de l'avatar 3D.

## 🏗️ Architecture Globale
Le module DSO1 fonctionne comme un orchestrateur de session de formation. Il gère la transcription (STT), la réflexion (LLM) et la parole (TTS).

## 🔄 Pipeline de Réponse (Le flux "Cerveau -> Bouche")

### 1. Entrée Utilisateur (STT)
- **Fichier** : `dso1/src/api/routes/training.py`
- **Fonctionnement** : Le frontend envoie le texte transcrit via l'endpoint `/speech_text`.
- **Action** : Le texte est stocké via `avatar.stt.set_user_text`.

### 2. Génération du Texte (LLM)
- **Fichier** : `dso1/src/session.py` (Fonction `conversation_loop`)
- **Logique** : 
    - Le système récupère le texte utilisateur via `get_user_text()`.
    - Il interroge le LLM (Llama 3.1) via `ask_avatar`.
    - **Variable Clé** : `avatar_reply` contient la réponse textuelle brute de l'avatar.

### 3. Synthèse Vocale (TTS)
- **Fichier** : `dso1/src/avatar/voice.py`
- **Fonctionnement** : La fonction `speak_text(text, lang)` transforme le texte en audio.
- **Technologie** : Utilise `edge-tts` pour générer un fichier MP3 temporaire et `pygame.mixer` pour la lecture.
- **Point d'intégration 3D** : C'est ici que l'animation de l'avatar doit être déclenchée.

## 🎯 Points d'Intégration pour l'Avatar 3D

Pour animer l'avatar (Lip-sync / Visèmes), l'équipe 3D doit se concentrer sur :

1.  **Flag "Parle"** : Dans `dso1/src/session.py`, la méthode `eval_thread.set_avatar_speaking(True)` est appelée juste avant que l'audio ne commence. C'est le signal idéal pour activer une animation "Speaking" générique.
2.  **Audio Buffer** : Actuellement, le son est joué localement. Pour une intégration web avec avatar 3D, il faudra probablement modifier `dso1/src/avatar/voice.py` pour envoyer le flux audio (ou le chemin du MP3) au frontend via WebSocket ou un endpoint de streaming.
3.  **Extraction de Visèmes** : Si l'avatar utilise des blendshapes (morph targets), il faudra traiter l'audio généré dans `voice.py` pour extraire les données de mouvement des lèvres.

## 📂 Fichiers Clés à Consulter
- `dso1/src/session.py` : Cœur de la boucle de conversation.
- `dso1/src/avatar/voice.py` : Gestion de la voix et des drapeaux de lecture.
- `dso1/src/avatar/prompts.py` : Personnalité et instructions de l'avatar.
- `shared/models.py` : Modèles de données SQL (Délégués, Produits).
