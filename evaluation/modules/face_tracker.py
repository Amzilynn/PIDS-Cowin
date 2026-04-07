"""
Module Couche 1 : Vision temps réel - Suivi du visage
Utilise MediaPipe FaceMesh (Legacy Solutions) pour les 478 landmarks (et micro-expressions estimées basiquement).
Intègre optionnellement RetinaFace pour la détection multi-angles.
"""
import cv2
import mediapipe as mp
import time
import numpy as np

class FaceTracker:
    def __init__(self, min_detection_confidence=0.5, min_tracking_confidence=0.5, use_retinaface=False):
        """
        Initialise le tracker de visage.
        :param use_retinaface: Si True, utilise RetinaFace pour la détection (lent mais robuste).
        """
        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            max_num_faces=1,
            refine_landmarks=True, # Active les repères des iris (pour le regard)
            min_detection_confidence=min_detection_confidence,
            min_tracking_confidence=min_tracking_confidence
        )
        self.use_retinaface = use_retinaface
        
        if self.use_retinaface:
            try:
                from retinaface import RetinaFace
                self.RetinaFace = RetinaFace
            except ImportError:
                print("⚠️ Attention: retina-face n'est pas installé. Fallback sur MediaPipe uniquement.")
                self.use_retinaface = False

    def process_frame(self, frame):
        """
        Analyse une frame (BGR) et retourne les points clés et un ratio d'ouverture des yeux.
        """
        results_data = {
            "has_face": False,
            "landmarks": None,
            "blink_ratio": 0.0,
            "retina_faces": None
        }

        # 1. RetinaFace (optionnel)
        if self.use_retinaface:
            # Note: RetinaFace attend souvent du RGB, mais accepte le BGR
            faces = self.RetinaFace.detect_faces(frame)
            if isinstance(faces, dict) and len(faces) > 0:
                results_data["retina_faces"] = faces
                results_data["has_face"] = True

        # 2. MediaPipe FaceMesh
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_results = self.face_mesh.process(rgb_frame)

        if mp_results.multi_face_landmarks:
            results_data["has_face"] = True
            face_landmarks = mp_results.multi_face_landmarks[0]
            
            # Format des landmarks : [478, 3] (x, y, z normés)
            landmarks_array = np.array([
                [lm.x, lm.y, lm.z] for lm in face_landmarks.landmark
            ])
            results_data["landmarks"] = landmarks_array
            
            # -- Calcul du ratio d'ouverture des yeux (Eye Aspect Ratio simplifié) --
            # Indices approximatifs : Oeil gauche (159/145), Oeil droit (386/374)
            left_eye_dist = abs(landmarks_array[159][1] - landmarks_array[145][1])
            right_eye_dist = abs(landmarks_array[386][1] - landmarks_array[374][1])
            avg_eye_dist = (left_eye_dist + right_eye_dist) / 2.0
            
            # Pour MediaPipe, une distance < 0.015 correspond souvent à un oeil fermé
            # On stocke tel quel pour le Scorer
            results_data["blink_ratio"] = avg_eye_dist
            
        return results_data

    def draw_landmarks(self, frame, results_data):
        """
        Dessine les landmarks sur l'image pour l'affichage visuel.
        """
        display_frame = frame.copy()
        
        # Dessin RetinaFace (Bounding Box)
        if results_data["retina_faces"]:
            for key, face in results_data["retina_faces"].items():
                facial_area = face["facial_area"] # [x1, y1, x2, y2]
                cv2.rectangle(display_frame, (facial_area[0], facial_area[1]), 
                              (facial_area[2], facial_area[3]), (255, 0, 0), 2)
        
        # Dessin MediaPipe (Points clés)
        h, w, _ = frame.shape
        if results_data["landmarks"] is not None:
            # On dessine 1 point sur 10 pour ne pas cacher visuellement le visage
            for i, lm in enumerate(results_data["landmarks"]):
                if i % 10 == 0: 
                    x, y = int(lm[0] * w), int(lm[1] * h)
                    cv2.circle(display_frame, (x, y), 1, (0, 255, 0), -1)

        return display_frame


def run_test():
    """
    Fonction de test autonome :
    Ouvre la webcam et lance la détection pour valider le tracking en temps réel.
    """
    print("--------------------------------------------------")
    print("Démarrage du module FaceTracker (Version Solutions)...")
    print("Appuyez sur 'q' pour quitter la fenêtre vidéo.")
    print("--------------------------------------------------")
    
    cap = cv2.VideoCapture(0)
    
    # RetinaFace est désactivé par défaut dans le test pour garder des FPS fluides.
    tracker = FaceTracker(use_retinaface=False) 
    
    prev_time = 0

    while cap.isOpened():
        success, frame = cap.read()
        if not success:
            print("❌ Impossible de lire la webcam.")
            break

        # On miroite l'image pour plus de naturalité
        frame = cv2.flip(frame, 1)

        # Calcul FPS
        current_time = time.time()
        fps = 1 / (current_time - prev_time) if current_time - prev_time > 0 else 0
        prev_time = current_time

        # Inférence
        results = tracker.process_frame(frame)

        # Rendu visuel
        annotated_frame = tracker.draw_landmarks(frame, results)

        # Affichage du HUD
        cv2.putText(annotated_frame, f"FPS: {int(fps)}", (20, 40), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
        
        if results["has_face"]:
            blink = results["blink_ratio"]
            status_text = "Ouv. yeux: OK" if blink > 0.015 else "CLIGNEMENT"
            color = (0, 255, 0) if blink > 0.015 else (0, 0, 255)
            
            cv2.putText(annotated_frame, f"Visage detecte - {status_text} ({blink:.4f})", 
                        (20, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
        else:
            cv2.putText(annotated_frame, "Aucun visage detecte", 
                        (20, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

        cv2.imshow('Vital Avatar - FaceTracker Test', annotated_frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    run_test()
