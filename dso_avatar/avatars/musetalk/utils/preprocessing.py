import sys
import os
import cv2
import numpy as np
import pickle
import mediapipe as mp
from tqdm import tqdm

# Initialize MediaPipe Face Mesh
mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(
    static_image_mode=True,
    max_num_faces=1,
    refine_landmarks=True,
    min_detection_confidence=0.5
)

# Marker if the bbox is not sufficient 
coord_placeholder = (0, 0, 0, 0)

def read_imgs(img_list):
    frames = []
    print('reading images...')
    for img_path in tqdm(img_list):
        frame = cv2.imread(img_path)
        if frame is None:
            print(f"Warning: Could not read {img_path}")
            continue
        frames.append(frame)
    return frames

def get_landmark_and_bbox(img_list, upperbondrange=0):
    frames = read_imgs(img_list)
    coords_list = []
    
    print('Processing landmarks with MediaPipe...')
    for frame in tqdm(frames):
        h, w = frame.shape[:2]
        # Convert to RGB for MediaPipe
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = face_mesh.process(rgb_frame)
        
        if not results.multi_face_landmarks:
            coords_list.append(coord_placeholder)
            continue
            
        # Get MediaPipe landmarks (normalized 0-1)
        landmarks = results.multi_face_landmarks[0].landmark
        
        # We need to map MediaPipe points to the logic MuseTalk expects
        # MuseTalk logic traditionally uses points from 68-point landmarkers
        # Point 29 is often used for vertical centering
        # Here we use a simpler bbox approach that mimics the expected offset
        
        points = []
        for lm in landmarks:
            points.append([lm.x * w, lm.y * h])
        points = np.array(points)
        
        # Face bounding box logic
        x_min, y_min = np.min(points, axis=0)
        x_max, y_max = np.max(points, axis=0)
        
        # MuseTalk specific: adjust upper bond
        # Point 197 in mediapipe is roughly nose bridge (comparable to point 29)
        nose_bridge = points[197]
        half_face_dist = y_max - nose_bridge[1]
        
        upper_bond = nose_bridge[1] - half_face_dist + upperbondrange
        upper_bond = max(0, upper_bond)
        
        # Ensure valid dimensions were found
        diff_x = x_max - x_min
        diff_y = y_max - upper_bond
        if diff_x <= 5 or diff_y <= 5: # Small threshold
            coords_list.append(coord_placeholder)
            continue
            
        bbox = (int(x_min), int(upper_bond), int(x_max), int(y_max))
        coords_list.append(bbox)
        
    return coords_list, frames

if __name__ == "__main__":
    # Test stub
    pass
