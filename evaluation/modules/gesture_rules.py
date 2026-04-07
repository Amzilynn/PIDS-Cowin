"""
Module Couche 4 partiel : Règles géométriques de gestes.
Analyse les points (pose / mains) issus du PoseTracker pour détecter des comportements non verbaux 
spécifiques (ex. bras croisés, stress avec main sur le visage, ouverture corporelle).
"""
import numpy as np

class GestureAnalyzer:
    def __init__(self):
        # Indices utiles MediaPipe Pose
        self.NOSE = 0
        self.LEFT_SHOULDER = 11
        self.RIGHT_SHOULDER = 12
        self.LEFT_ELBOW = 13
        self.RIGHT_ELBOW = 14
        self.LEFT_WRIST = 15
        self.RIGHT_WRIST = 16

    def check_crossed_arms(self, pose_landmarks):
        """
        Détecte si les bras sont croisés.
        Logique simplifiée: les poignets sont proches l'un de l'autre et plus proches 
        du centre du corps (axe X) que les coudes.
        """
        if pose_landmarks is None:
            return False
            
        try:
            l_wrist = pose_landmarks[self.LEFT_WRIST]
            r_wrist = pose_landmarks[self.RIGHT_WRIST]
            l_elbow = pose_landmarks[self.LEFT_ELBOW]
            r_elbow = pose_landmarks[self.RIGHT_ELBOW]

            # Vérifie la visibilité des points clés (score > 0.5)
            if (l_wrist[3] < 0.5 or r_wrist[3] < 0.5 or 
                l_elbow[3] < 0.5 or r_elbow[3] < 0.5):
                return False

            # Distance horizontale entre les poignets
            wrists_dist_x = abs(l_wrist[0] - r_wrist[0])
            
            # Distance entre les épaules comme référence de l'échelle du corps
            shoulders_dist_x = abs(pose_landmarks[self.LEFT_SHOULDER][0] - pose_landmarks[self.RIGHT_SHOULDER][0])
            
            # Si les poignets sont rapprochés (moins de la moitié de la largeur des épaules)
            # et qu'ils sont situés devant le torse (axe Y sous les épaules)
            if wrists_dist_x < (shoulders_dist_x * 0.5):
                # On s'assure que les mains ne sont pas en l'air
                if l_wrist[1] > pose_landmarks[self.LEFT_SHOULDER][1] and r_wrist[1] > pose_landmarks[self.RIGHT_SHOULDER][1]:
                    return True
            return False
        except Exception:
            return False

    def check_hand_on_face(self, pose_landmarks):
        """
        Détecte un signe de stress/réflexion intense : main(s) posée(s) près du visage/front.
        """
        if pose_landmarks is None:
            return False

        try:
            nose = pose_landmarks[self.NOSE]
            l_wrist = pose_landmarks[self.LEFT_WRIST]
            r_wrist = pose_landmarks[self.RIGHT_WRIST]
            
            # Distance euclidienne 2D nez-poignet
            dist_l = np.sqrt((nose[0] - l_wrist[0])**2 + (nose[1] - l_wrist[1])**2)
            dist_r = np.sqrt((nose[0] - r_wrist[0])**2 + (nose[1] - r_wrist[1])**2)
            
            # Seuil de proximité au visage (15% de l'image)
            threshold = 0.15
            
            is_touching = (dist_l < threshold and l_wrist[3] > 0.5) or (dist_r < threshold and r_wrist[3] > 0.5)
            return is_touching
        except Exception:
            return False

    def analyze(self, pose_data):
        """
        Prend le dictionnaire de sortie de PoseTracker et retourne l'état des gestes.
        """
        results = {
            "arms_crossed": False,
            "hand_on_face": False,
            "is_stressed_posture": False
        }
        
        if not pose_data["has_pose"]:
            return results
            
        pose_lm = pose_data["pose_landmarks"]
        
        results["arms_crossed"] = self.check_crossed_arms(pose_lm)
        results["hand_on_face"] = self.check_hand_on_face(pose_lm)
        
        # Logique métier: La posture est considérée comme "fermée/stressée" si bras croisés ou main sur le visage
        results["is_stressed_posture"] = results["arms_crossed"] or results["hand_on_face"]
        
        return results

# Ce script contient uniquement la logique d'analyse. 
# Il n'a pas besoin de script CV2 isolé de test car il s'adosse directement sur le PoseTracker.
