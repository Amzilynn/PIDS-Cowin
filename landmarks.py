import cv2
import mediapipe as mp
import numpy as np
import pandas as pd

mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(static_image_mode=False,
                                  max_num_faces=1,
                                  refine_landmarks=True,
                                  min_detection_confidence=0.5,
                                  min_tracking_confidence=0.5)

cap = cv2.VideoCapture(0)

data = []  # pour stocker features + label

print("Appuie sur 't' pour tired, 's' pour stressed, 'n' pour neutral, 'q' pour quitter")

while True:
    ret, frame = cap.read()
    if not ret:
        break
    
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = face_mesh.process(frame_rgb)
    
    if results.multi_face_landmarks:
        face_landmarks = results.multi_face_landmarks[0]
        landmarks = np.array([[lm.x, lm.y, lm.z] for lm in face_landmarks.landmark])
        
        # Features simples
        left_eye = landmarks[33]
        right_eye = landmarks[263]
        top_eye = landmarks[159]
        bottom_eye = landmarks[145]
        eye_ratio = (bottom_eye[1] - top_eye[1]) / (right_eye[0] - left_eye[0])
        
        left_mouth = landmarks[78]
        right_mouth = landmarks[308]
        top_mouth = landmarks[13]
        bottom_mouth = landmarks[14]
        mouth_ratio = (bottom_mouth[1] - top_mouth[1]) / (right_mouth[0] - left_mouth[0])
        
        left_brow = landmarks[65]
        right_brow = landmarks[295]
        brow_distance = np.linalg.norm(left_brow[:2] - right_brow[:2])
        
        # Affiche sur la frame
        cv2.putText(frame, f"Eye:{eye_ratio:.2f} Mouth:{mouth_ratio:.2f} Brow:{brow_distance:.2f}",
                    (10,30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,255,0),2)
        
        # Si tu appuies sur une touche, tu stockes la donnée
        key = cv2.waitKey(1) & 0xFF
        if key == ord('t'):
            data.append([eye_ratio, mouth_ratio, brow_distance, "tired"])
            print("Saved: tired")
        elif key == ord('s'):
            data.append([eye_ratio, mouth_ratio, brow_distance, "stressed"])
            print("Saved: stressed")
        elif key == ord('n'):
            data.append([eye_ratio, mouth_ratio, brow_distance, "neutral"])
            print("Saved: neutral")
        elif key == ord('q'):
            break
    
    cv2.imshow("Capture Features", frame)

cap.release()
cv2.destroyAllWindows()

# Sauvegarde dans un CSV
df = pd.DataFrame(data, columns=["eye_ratio","mouth_ratio","brow_distance","label"])
df.to_csv("face_dataset.csv", index=False)
print("Dataset saved to face_dataset.csv")