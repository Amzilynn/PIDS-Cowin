"""
Configuration globale du pipeline d'évaluation multimodale.
Définit les seuils, chemins et paramètres des modèles pour l'évaluation.
"""
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ------------------------------------------------------------------
# CONFIGURATION VISION (Face & Pose)
# ------------------------------------------------------------------
VISION_CONFIG = {
    'video_resolution': (640, 480), # (width, height)
    'fps': 30,
    # MediaPipe
    'mediapipe_min_detection_confidence': 0.5,
    'mediapipe_min_tracking_confidence': 0.5,
    # RetinaFace
    'retinaface_quality': 'normal' # 'normal' ou 'high'
}

# ------------------------------------------------------------------
# CONFIGURATION ÉMOTIONS (OpenFace & AffectNet)
# ------------------------------------------------------------------
EMOTION_CONFIG = {
    'openface_executable_path': os.path.join(BASE_DIR, 'tools', 'OpenFace', 'FeatureExtraction.exe'),
    # Modèles
    'affectnet_model_name': 'enet_b4_8_best.pt', 
}

# ------------------------------------------------------------------
# CONFIGURATION AUDIO
# ------------------------------------------------------------------
AUDIO_CONFIG = {
    'sample_rate': 16000,
    'chunk_size': 1024,
    'wav2vec2_model_name': 'audeering/wav2vec2-large-robust-12-ft-emotion-msp-dim',
}

# ------------------------------------------------------------------
# SCORER & PONDÉRATION (%)
# ------------------------------------------------------------------
SCORER_WEIGHTS = {
    'layer1_vision': 0.20,       # Poids des clignements / regard
    'layer2_emotions': 0.35,     # Poids de la valence / arousal
    'layer3_audio': 0.30,        # Poids de l'assurance vocale (pitch, stress)
    'layer4_gestures': 0.15      # Poids de la posture (mains sur visage)
}

# Seuils critiques (0.0 à 1.0)
THRESHOLDS = {
    'high_stress_audio': 0.8,
    'low_confidence_voice': 0.3,
    'negative_valence_extreme': -0.5
}
