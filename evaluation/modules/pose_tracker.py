"""
Module Couche 1 : Vision temps réel - Posture corporelle et mains
Utilise MediaPipe Holistic (Legacy Solutions) pour le corps (33 keypoints) et les mains (21 keypoints par main).
"""
import cv2
import mediapipe as mp
import time
import numpy as np

class PoseTracker:
    def __init__(self, min_detection_confidence=0.5, min_tracking_confidence=0.5):
        """
        Initialise le tracker Holistic (Corps + Mains).
        """
        self.mp_holistic = mp.solutions.holistic
        self.mp_drawing = mp.solutions.drawing_utils
        self.mp_drawing_styles = mp.solutions.drawing_styles
        
        self.holistic = self.mp_holistic.Holistic(
            min_detection_confidence=min_detection_confidence,
            min_tracking_confidence=min_tracking_confidence,
            model_complexity=1 # 1 est un bon compromis vitesse/précision pour PC
        )

    def process_frame(self, frame):
        """
        Analyse une frame (BGR) et retourne la posture et les mains normées.
        """
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Inférence complète du corps
        results = self.holistic.process(rgb_frame)
        
        results_data = {
            "has_pose": False,
            "pose_landmarks": None,
            "left_hand": None,
            "right_hand": None
        }

        # Conversion des landmarks en numpy arrays pour traitement mathématique
        if results.pose_landmarks:
            results_data["has_pose"] = True
            # Corps : 33 points [x, y, z, visibilité]
            results_data["pose_landmarks"] = np.array([
                [lm.x, lm.y, lm.z, lm.visibility] for lm in results.pose_landmarks.landmark
            ])
            
        if results.left_hand_landmarks:
            # Main Gauche : 21 points [x, y, z]
            results_data["left_hand"] = np.array([
                [lm.x, lm.y, lm.z] for lm in results.left_hand_landmarks.landmark
            ])
            
        if results.right_hand_landmarks:
            # Main Droite : 21 points [x, y, z]
            results_data["right_hand"] = np.array([
                [lm.x, lm.y, lm.z] for lm in results.right_hand_landmarks.landmark
            ])

        # On retourne aussi l'objet 'results' de MediaPipe utile pour le dessin automatique
        return results_data, results

    def draw_landmarks(self, frame, mp_results):
        """
        Dessine les lignes du corps et les squelettes des mains.
        """
        display_frame = frame.copy()
        
        # 1. Pose (corps)
        self.mp_drawing.draw_landmarks(
            display_frame,
            mp_results.pose_landmarks,
            self.mp_holistic.POSE_CONNECTIONS,
            landmark_drawing_spec=self.mp_drawing_styles.get_default_pose_landmarks_style()
        )
        
        # 2. Main Gauche
        self.mp_drawing.draw_landmarks(
            display_frame,
            mp_results.left_hand_landmarks,
            self.mp_holistic.HAND_CONNECTIONS,
            self.mp_drawing_styles.get_default_hand_landmarks_style(),
            self.mp_drawing_styles.get_default_hand_connections_style()
        )
        
        # 3. Main Droite
        self.mp_drawing.draw_landmarks(
            display_frame,
            mp_results.right_hand_landmarks,
            self.mp_holistic.HAND_CONNECTIONS,
            self.mp_drawing_styles.get_default_hand_landmarks_style(),
            self.mp_drawing_styles.get_default_hand_connections_style()
        )

        return display_frame


def run_test():
    """
    Fonction de test isolée pour valider le suivi corporel en direct.
    """
    print("--------------------------------------------------")
    print("Démarrage du module PoseTracker (MediaPipe Holistic)...")
    print("Reculez un peu pour que la caméra capte votre buste et vos mains !")
    print("Appuyez sur 'q' pour quitter la fenêtre vidéo.")
    print("--------------------------------------------------")
    
    cap = cv2.VideoCapture(0)
    tracker = PoseTracker()
    prev_time = 0

    while cap.isOpened():
        success, frame = cap.read()
        if not success:
            print("❌ Impossible de lire la webcam.")
            break

        frame = cv2.flip(frame, 1)

        current_time = time.time()
        fps = 1 / (current_time - prev_time) if current_time - prev_time > 0 else 0
        prev_time = current_time

        # Analyse
        data, mp_results = tracker.process_frame(frame)
        
        # Rendu
        annotated_frame = tracker.draw_landmarks(frame, mp_results)

        # Affichage Infos (HUD)
        cv2.putText(annotated_frame, f"FPS: {int(fps)}", (20, 40), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
        
        status_text = "OK" if data["has_pose"] else "X"
        left_h = "OK" if data["left_hand"] is not None else "X"
        right_h = "OK" if data["right_hand"] is not None else "X"
        
        info_str = f"Corps: {status_text} | Main G: {left_h} | Main D: {right_h}"
        color = (0, 255, 0) if data["has_pose"] else (0, 0, 255)
        cv2.putText(annotated_frame, info_str, (20, 80), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)

        cv2.imshow('Vital Avatar - PoseTracker Test', annotated_frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    run_test()
