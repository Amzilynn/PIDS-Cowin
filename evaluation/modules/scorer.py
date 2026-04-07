"""
Module Couche 4 : Moteur de Fusion Multimodale (Scorer)
Agrège les données de toutes les couches pour calculer un score global (0-100).
Enregistre l'historique de la session pour la timeline PDF.
"""
import time

class MultimodalScorer:
    def __init__(self, config_weights):
        """
        Initialise le moteur avec les pondérations par domaine venant de config.py
        """
        self.weights = config_weights
        self.history = [] # Historique frame-par-frame pour la génération du rapport PDF
        self.start_time = time.time()
        
    def calculate_score(self, vision_res, pose_res, gesture_res, emotion_res, audio_res, speech_res):
        """
        Calcule la performance en temps réel et détecte les moments critiques.
        On part d'un score parfait de 100% que l'on pénalise selon les erreurs du délégué.
        """
        score = 100.0
        penalties = []
        
        # --- 1. Évaluation Posture & Gestes (Ex: 15% d'impact) ---
        if gesture_res.get("is_stressed_posture"):
            score -= (100 * self.weights.get('layer4_gestures', 0.15))
            penalties.append("Posture fermée (Croisement/Visage)")
            
        # --- 2. Évaluation Émotion Faciale (Ex: 35% d'impact) ---
        valence = emotion_res.get("valence", 0.0)
        dom_emotion = emotion_res.get("dominant_emotion", "Neutral")
        
        if valence < -0.3 or dom_emotion in ["Anger", "Disgust", "Fear"]:
            # Expression agacée ou dégoûtée : très mauvais face au médecin !
            score -= (100 * self.weights.get('layer2_emotions', 0.35))
            penalties.append("Expression très négative")
        elif valence < 0.0:
            # Léger froncement : pénalité mineure
            score -= (40 * self.weights.get('layer2_emotions', 0.35)) 
            
        # --- 3. Évaluation Visuelle Globale (Ex: 20% d'impact) ---
        if not vision_res.get("has_face"):
            score -= (100 * self.weights.get('layer1_vision', 0.20))
            if "Visage non centré" not in penalties: # eviter duplication
                penalties.append("Visage non centré vers la caméra")
            
        # --- 4. Évaluation Vocale & Paralinguistique (Ex: 30% d'impact) ---
        confidence = speech_res.get("confidence_score", 0.5)
        is_speaking = audio_res.get("is_speaking", False)
        
        if is_speaking:
            if confidence < 0.4:
                # La voix tremble ou le volume est très bas/hésitant
                score -= (100 * self.weights.get('layer3_audio', 0.30))
                penalties.append("Hésitation vocale sévère")
            elif confidence < 0.6:
                score -= (40 * self.weights.get('layer3_audio', 0.30))

        # --- Fin : Consolidation ---
        final_score = max(0.0, min(100.0, score))
        
        current_session_time = time.time() - self.start_time
        
        frame_data = {
            "timestamp": current_session_time,
            "overall_score": final_score,
            "emotion": dom_emotion,
            "penalties": penalties,
            # Un moment est critique si le score chute sous 65/100
            "is_critical": len(penalties) > 0 and final_score < 65 
        }
        
        self.history.append(frame_data)
        return frame_data

    def get_session_summary(self):
        """
        Retourne la moyenne globale de la session. Utile pour le rapport final.
        """
        if not self.history:
            return 0
        scores = [f["overall_score"] for f in self.history]
        return sum(scores) / len(scores)

def run_test():
    import sys
    import os
    # Ajoute le dossier parent (evaluation) au chemin système pour trouver config.py
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    import random
    from config import SCORER_WEIGHTS
    
    print("Test du Scorer Multimodal...")
    scorer = MultimodalScorer(SCORER_WEIGHTS)
    
    print("Simulation d'une frame excellente...")
    res = scorer.calculate_score(
        vision_res={"has_face": True}, pose_res={"has_pose": True},
        gesture_res={"is_stressed_posture": False}, 
        emotion_res={"valence": 0.8, "dominant_emotion": "Happy"},
        audio_res={"is_speaking": True}, speech_res={"confidence_score": 0.9}
    )
    print(f"Score: {res['overall_score']} | Pénalités: {res['penalties']}")
    
    print("\nSimulation d'une frame catastrophique (Bras croisés, Voix hésitante)...")
    res = scorer.calculate_score(
        vision_res={"has_face": True}, pose_res={"has_pose": True},
        gesture_res={"is_stressed_posture": True}, 
        emotion_res={"valence": -0.1, "dominant_emotion": "Neutral"},
        audio_res={"is_speaking": True}, speech_res={"confidence_score": 0.3}
    )
    print(f"Score: {res['overall_score']} | Pénalités: {res['penalties']}")

if __name__ == "__main__":
    run_test()
