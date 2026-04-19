import cv2
import pickle
import os
import glob
import numpy as np

# Configuration
avatar_dir = 'dso_avatar/data/avatars/musetalk_avatar1'
img_dir = os.path.join(avatar_dir, 'full_imgs')
out_coords = os.path.join(avatar_dir, 'coords.pkl')
out_mask_coords = os.path.join(avatar_dir, 'mask_coords.pkl')

print(f"Scanning frames in {img_dir}...")

# Load detector
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

# Get all images
img_list = sorted(glob.glob(os.path.join(img_dir, '*.png')))
new_coords = []

# Detect on every frame
for i, img_path in enumerate(img_list):
    img = cv2.imread(img_path)
    if img is None: continue
    
    # Rotate 90 CW to vertical (matching our engine)
    img_v = cv2.rotate(img, cv2.ROTATE_90_CLOCKWISE)
    gray = cv2.cvtColor(img_v, cv2.COLOR_BGR2GRAY)
    
    faces = face_cascade.detectMultiScale(gray, 1.3, 5)
    if len(faces) > 0:
        (x, y, w, h) = faces[0]
        # Target the mouth area with a nudge to the RIGHT (viewer's right)
        # and a wider box to cover the full mouth area.
        mx = x + int(w * 0.15) 
        my = y + int(h * 0.65)
        mw = int(w * 0.9)  
        mh = int(h * 0.45)
        bbox = [mx, my, mx+mw, my+mh]
    else:
        # Fallback to a safe guess if detection fails on a frame
        bbox = [175, 420, 385, 520]
        
    new_coords.append(bbox)
    if i % 10 == 0:
        print(f"Processed {i}/{len(img_list)} frames...")

# Save new map
with open(out_coords, 'wb') as f:
    pickle.dump(new_coords, f)
with open(out_mask_coords, 'wb') as f:
    pickle.dump(new_coords, f)

print(f"Success! Saved new map with {len(new_coords)} frames.")
