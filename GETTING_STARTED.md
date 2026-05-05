# Guide de Démarrage : Avalive Unified Project

Ce guide explique comment lancer l'application complète (Backend unifié + Frontend React).

## 📋 Prérequis
- **Python 3.10+**
- **Node.js 18+**
- **MySQL** (avec la base `avalive_dso4` configurée)

## 🚀 Étape 1 : Lancer le Backend (Python)

Le backend unifié regroupe DSO1 (Entraînement), DSO3 (Expertise) et DSO4 (Optimisation).

1.  Ouvrez un terminal à la racine du projet (`integrationFront`).
2.  Activez l'environnement virtuel :
    ```powershell
    # Sur Windows
    .\venv\Scripts\activate
    ```
3.  Installez les dépendances (si ce n'est pas déjà fait) :
    ```bash
    pip install -r requirements.txt
    ```
4.  Lancez le serveur :
    ```bash
    python main_unified.py
    ```
    *Le backend sera accessible sur `http://localhost:8001`.*

## 💻 Étape 2 : Lancer le Frontend (React)

Le frontend gère l'interface utilisateur et communique avec le backend unifié.

1.  Ouvrez un **nouveau** terminal dans le dossier `front` :
    ```bash
    cd front
    ```
2.  Installez les modules Node :
    ```bash
    npm install
    ```
3.  Lancez l'application :
    ```bash
    npm run dev
    ```
    *L'interface sera accessible sur `http://localhost:5173` (ou le port affiché dans le terminal).*

## 🛠️ Rappels Techniques
- **Base de données** : Assurez-vous que votre serveur MySQL tourne et que les accès dans `shared/database.py` sont corrects.
- **Port API** : Le frontend est configuré pour taper sur le port **8001**. Ne changez pas le port dans `main_unified.py` sans mettre à jour `VisitPlanner.jsx`.
- **Caméra** : La session d'entraînement (DSO1) nécessite l'accès à la webcam.
