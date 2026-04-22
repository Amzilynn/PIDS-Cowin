import os
import cv2
import numpy as np
import pickle
import shutil
from pathlib import Path

# Paths
project_root = r"c:\Users\Rayen\Desktop\testforfum\ESPRIT-PI-4DS10-25-26-Co_Win\dso_avatar"
source_img_path = os.path.join(project_root, "avalive.jpg")
avatar_id = "sarah_static"
output_dir = os.path.join(project_root, "data", "avatars", avatar_id)

# 1. Create structure
full_imgs_path = os.path.join(output_dir, "full_imgs")
face_imgs_path = os.path.join(output_dir, "face_imgs")
os.makedirs(full_imgs_path, exist_ok=True)
os.makedirs(face_imgs_path, exist_ok=True)

print(f"[*] Processing Sarah Khalil: {source_img_path}")
img = cv2.imread(source_img_path)
if img is None:
    print("[!] Error: Could not find avalive.jpg")
    exit(1)

# 2. Simple Face Detection for Wav2Lip (using Haar Cascades for speed/reliability in scratch)
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
faces = face_cascade.detectMultiScale(gray, 1.1, 4)

if len(faces) == 0:
    print("[!] Error: No face detected in avalive.jpg. Using fallback coordinates.")
    # Fallback for Sarah's specific photo if detection fails
    h, w = img.shape[:2]
    # Rough estimate for Sarah's face in avalive.jpg
    bx, by, bw, bh = int(w*0.3), int(h*0.15), int(w*0.4), int(h*0.45)
else:
    # Use the largest face found
    bx, by, bw, bh = sorted(faces, key=lambda f: f[2]*f[3], reverse=True)[0]
    # Expand slightly for Wav2Lip
    bx = max(0, bx - int(bw*0.1))
    by = max(0, by - int(bh*0.1))
    bw = int(bw * 1.2)
    bh = int(bh * 1.2)

# Wav2Lip Format: [y1, y2, x1, x2]
coords = [by, by+bh, bx, bx+bw]
face_crop = img[by:by+bh, bx:bx+bw]

print(f"[*] Detected Face at: {coords}")

# 3. Generate 100 frames (loop)
coord_list = []
for i in range(100):
    fname = f"{i:08d}.png"
    cv2.imwrite(os.path.join(full_imgs_path, fname), img)
    cv2.imwrite(os.path.join(face_imgs_path, fname), face_crop)
    coord_list.append(coords)

# 4. Save Coords
with open(os.path.join(output_dir, "coords.pkl"), "wb") as f:
    pickle.dump(coord_list, f)

print(f"[✓] Sarah Khalil avatar created at: {output_dir}")
