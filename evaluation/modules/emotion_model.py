"""
Module Couche 2 : Modèle Deep Learning des Émotions (AffectNet)
Utilise PyTorch + Timm (EfficientNet-B4) pour inférer valence/arousal
et 11 classes d'émotions sur les visages recadrés en continu.
"""
import torch
import torchvision.transforms as transforms
import cv2
from PIL import Image
import numpy as np

class AffectNetEmotionModel:
    def __init__(self, model_name='enet_b4_8_best.pt', device=None):
        """
        Initialise le modèle EfficientNet-B4 fine-tuné sur AffectNet.
        :param model_name: Nom du fichier modèle attendu (optionnel pour l'instant)
        """
        self.device = device if device else ('cuda' if torch.cuda.is_available() else 'cpu')
        
        # Liste des émotions d'AffectNet souvent réduites à 8 ou 11
        self.emotion_labels = [
            'Neutral', 'Happy', 'Sad', 'Surprise', 'Fear', 'Disgust', 'Anger', 'Contempt'
        ]
        
        # Transformations standards pour un modèle PyTorch pré-entrainé sur ImageNet/AffectNet
        self.transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ])
        
        self.model_loaded = False
        self.model = None
        self._load_dummy_model() # Ou charger de HuggingFace/Local si existant

        print(f"AffectNetEmotionModel initialisé sur {self.device}.")

    def _load_dummy_model(self):
        """
        Si le fichier .pt lourd n'est pas trouvé (ce qui est le cas avant un téléchargement manuel),
        on évite un crash. Le modèle retournera un dictionnaire prédictif par défaut basé sur l'expression.
        (En production finale, on instancie via timm.create_model('tf_efficientnet_b4_ns', pretrained=True)).
        """
        print("INFO: Aucun poids local (.pt) spécifié pour EfficientNet-B4 AffectNet.")
        print("INFO: Mode Inférence émulée activé pour le développement de l'intégration.")
        pass

    def extract_face(self, frame, face_data):
        """
        Découpe le visage de l'image source à partir des données de RetinaFace ou MediaPipe.
        """
        if not face_data or not face_data.get("has_face"):
            return None
            
        h, w, _ = frame.shape
        x_min, y_min, x_max, y_max = 0, 0, w, h
        
        # RetinaFace Bbox Extraction
        if face_data.get("retina_faces"):
            for key, face in face_data["retina_faces"].items():
                x_min, y_min, x_max, y_max = face["facial_area"]
                break
        # MediaPipe Bbox Approximation via landmarks
        elif face_data.get("landmarks") is not None:
            lms = face_data["landmarks"]
            # Coordonnées min/max
            xs = [lm[0] * w for lm in lms]
            ys = [lm[1] * h for lm in lms]
            x_min, x_max = max(0, int(min(xs)) - 20), min(w, int(max(xs)) + 20)
            y_min, y_max = max(0, int(min(ys)) - 30), min(h, int(max(ys)) + 20)
        
        if x_max > x_min and y_max > y_min:
            return frame[y_min:y_max, x_min:x_max]
        return None

    def process_face(self, face_image, face_data=None):
        """
        Passe le visage croppé dans le réseau de neurones.
        Renvoie la valence [-1, 1], arousal [-1, 1], et l'émotion dominante.
        """
        results = {
            "valence": 0.0,
            "arousal": 0.0,
            "dominant_emotion": "Neutral",
            "emotion_probs": {e: 0.0 for e in self.emotion_labels}
        }
        
        if face_image is None or face_image.size == 0:
            return results
            
        # Conversion pour PyTorch
        pil_img = Image.fromarray(cv2.cvtColor(face_image, cv2.COLOR_BGR2RGB))
        input_tensor = self.transform(pil_img).unsqueeze(0).to(self.device)

        if self.model_loaded:
            with torch.no_grad():
                # Vraie inférence PyTorch ici quand le .pt est présent
                pass
        else:
            # === MODE ÉMULATION BASÉ SUR MEDIA PIPE ===
            # Si le .pt n'est pas fourni, on simule l'émotion dynamiquement avec la géométrie du visage
            if face_data and face_data.get("landmarks") is not None:
                lms = face_data["landmarks"]
                
                # Sourire : Distance entre les coins de la bouche (61 et 291)
                mouth_width = abs(lms[61][0] - lms[291][0])
                # Hauteur du visage pour l'échelle (front 10 à menton 152)
                face_height = abs(lms[10][1] - lms[152][1])
                
                # Sourcils : Distance entre nez (1) et sourcils (105 et 334)
                eyebrow_dist = (abs(lms[1][1] - lms[105][1]) + abs(lms[1][1] - lms[334][1])) / 2.0
                
                ratio_mouth = mouth_width / face_height
                ratio_brows = eyebrow_dist / face_height
                
                if ratio_mouth > 0.45:
                    results["dominant_emotion"] = "Happy"
                    results["valence"] = 0.8
                    results["arousal"] = 0.6
                elif ratio_brows < 0.20:
                    results["dominant_emotion"] = "Anger"
                    results["valence"] = -0.7
                    results["arousal"] = 0.7
                elif ratio_brows > 0.45:
                    results["dominant_emotion"] = "Surprise"
                    results["valence"] = 0.5
                    results["arousal"] = 0.8
                else:
                    results["dominant_emotion"] = "Neutral"
                    results["valence"] = 0.1
                    results["arousal"] = 0.1
                    
                # Débuggage pour ajuster selon le visage
                results["debug_ratios"] = {"mouth": ratio_mouth, "brows": ratio_brows}
                
                    
        return results

def run_test():
    print("--------------------------------------------------")
    print("Démarrage du test AffectNetEmotionModel...")
    print("Appuyez sur 'q' pour quitter la fenêtre vidéo.")
    print("--------------------------------------------------")
    
    # Import du FaceTracker pour découper le visage
    import sys, os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from modules.face_tracker import FaceTracker
    
    cap = cv2.VideoCapture(0)
    tracker = FaceTracker(use_retinaface=False)
    emotion_net = AffectNetEmotionModel()

    while cap.isOpened():
        success, frame = cap.read()
        if not success:
            break

        frame = cv2.flip(frame, 1)
        results_vision = tracker.process_frame(frame)
        
        # Le tracker classique
        annotated_frame = tracker.draw_landmarks(frame, results_vision)
        
        # Et la surcouche Emotion Model
        cropped_face = emotion_net.extract_face(frame, results_vision)
        emotion_results = emotion_net.process_face(cropped_face, face_data=results_vision)

        if cropped_face is not None:
             # On peut même afficher le visage croppé en haut à droite
             crop_resized = cv2.resize(cropped_face, (100, 100))
             annotated_frame[10:110, -110:-10] = crop_resized
             cv2.rectangle(annotated_frame, (annotated_frame.shape[1]-110, 10), (annotated_frame.shape[1]-10, 110), (255,0,0), 2)

        # Affichage valence et debug
        v, a = emotion_results["valence"], emotion_results["arousal"]
        dom = emotion_results["dominant_emotion"]
        cv2.putText(annotated_frame, f"Emotion: {dom} (V:{v:.2f} A:{a:.2f})", 
                    (20, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 100, 255), 2)
                    
        debug = emotion_results.get("debug_ratios", None)
        if debug:
            cv2.putText(annotated_frame, f"[Debug] Bouche: {debug['mouth']:.2f} | Sourcils: {debug['brows']:.2f}", 
                        (20, 150), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

        cv2.imshow('Vital Avatar - AffectNet Test', annotated_frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    run_test()
