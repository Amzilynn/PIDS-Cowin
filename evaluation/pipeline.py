"""
Orchestrateur Principal : Pipeline d'Évaluation Multimodale
Charge tous les modules et unifie l'analyse des frames et de l'audio.
"""
from evaluation.config import SCORER_WEIGHTS
from evaluation.modules.face_tracker import FaceTracker
from evaluation.modules.pose_tracker import PoseTracker
from evaluation.modules.gesture_rules import GestureAnalyzer
from evaluation.modules.emotion_model import AffectNetEmotionModel
from evaluation.modules.audio_analyzer import AudioAnalyzer
from evaluation.modules.speech_emotion import SpeechEmotionModel
from evaluation.modules.scorer import MultimodalScorer

class AvatarEvaluationPipeline:
    def __init__(self):
        """
        Assemble et instancie tous les sous-systèmes.
        Cette étape peut prendre 1 à 2 secondes si le deep learning est activé.
        """
        print("[Pipeline] Initialisation des Cerveaux IA en cours...")
        self.face_tracker = FaceTracker(use_retinaface=False)
        self.pose_tracker = PoseTracker()
        self.gesture_analyzer = GestureAnalyzer()
        self.emotion_model = AffectNetEmotionModel()
        self.audio_analyzer = AudioAnalyzer(sample_rate=16000)
        self.speech_model = SpeechEmotionModel()
        
        # Le chef d'orchestre
        self.scorer = MultimodalScorer(SCORER_WEIGHTS)
        print("[Pipeline] Tous les modules IA sont prêts.")

    def process_tick(self, frame, audio_chunk=None):
        """
        Moteur principal. Fait passer l'image et le son dans toutes les couches.
        Renvoie un méga-dictionnaire avec les prédictions et la note /100.
        """
        # ========================================
        # COUCHE 1 : VISION & POSTURE
        # ========================================
        vis_res = self.face_tracker.process_frame(frame)
        pose_res, mp_pose_results = self.pose_tracker.process_frame(frame)
        
        # ========================================
        # COUCHE 2 : ÉMOTION & COMPORTEMENT 
        # ========================================
        gest_res = self.gesture_analyzer.analyze(pose_res)
        
        cropped_face = self.emotion_model.extract_face(frame, vis_res)
        emo_res = self.emotion_model.process_face(cropped_face, face_data=vis_res)
        
        # ========================================
        # COUCHE 3 : AUDIO 
        # ========================================
        aud_res = {"is_speaking": False, "energy": 0}
        speech_res = {"confidence_score": 0.5, "emotion": "Neutral"}
        
        if audio_chunk is not None and len(audio_chunk) > 0:
            aud_res = self.audio_analyzer.process_chunk(audio_chunk)
            speech_res = self.speech_model.process_chunk(audio_chunk)
            
        # ========================================
        # COUCHE 4 : SCORER
        # ========================================
        step_score = self.scorer.calculate_score(
            vis_res, pose_res, gest_res, emo_res, aud_res, speech_res
        )
        
        return {
            "score_data": step_score,
            "vision": vis_res,
            "pose": pose_res,
            "mp_pose_results": mp_pose_results,
            "gesture": gest_res,
            "emotion": emo_res,
            "audio": aud_res,
            "speech": speech_res
        }
        
    def get_session_history(self):
        """Récupère l'historique complet pour générer le rapport PDF"""
        return self.scorer.history
