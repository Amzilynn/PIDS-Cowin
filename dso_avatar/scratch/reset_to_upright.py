import cv2
import pickle
import os
import glob
import numpy as np

# Config
src_video = 'dso_avatar/eya.mp4'
avatar_dir = 'dso_avatar/data/avatars/musetalk_avatar1'
img_out_dir = os.path.join(avatar_dir, 'full_imgs')
coords_out = os.path.join(avatar_dir, 'coords.pkl')
mask_coords_out = os.path.join(avatar_dir, 'mask_coords.pkl')

os.makedirs(img_out_dir, exist_ok=True)

print(f"Phase 1: Resetting frames in {img_out_dir} from {src_video}...")

# 1. Extract clean vertical frames
cap = cv2.VideoCapture(src_video)
count = 0
while True:
    ret, frame = cap.read()
    if not ret: break
    # NO ROTATION - just save as is
    out_path = os.path.join(img_out_dir, f'{count:08d}.png')
    cv2.imwrite(out_path, frame)
    count += 1
cap.release()
print(f"Extracted {count} upright frames.")

# 2. Re-detect bboxes on these upright frames
print("Phase 2: Scanning face bboxes on clean frames...")
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
img_list = sorted(glob.glob(os.path.join(img_out_dir, '*.png')))
new_coords = []
last_good = [160, 370, 410, 530] # Reasonable vertical fallback for this video

for i, path in enumerate(img_list):
    img = cv2.imread(path)
    if img is None:
        new_coords.append(last_good)
        continue
    
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, 1.2, 5)
    
    if len(faces) > 0:
        # Sort by size and take largest face
        (x, y, w, h) = sorted(faces, key=lambda f: f[2]*f[3], reverse=True)[0]
        # Mouth ROI logic
        mx = x + int(w * 0.15)
        my = y + int(h * 0.65)
        mw = int(w * 0.7)
        mh = int(h * 0.3)
        bbox = [mx, my, mx+mw, my+mh]
        last_good = bbox
        new_coords.append(bbox)
    else:
        new_coords.append(last_good)
        
    if i % 100 == 0:
        print(f"Processed {i}/{len(img_list)}...")

# 3. Fix masks (rotate them to match the vertical frames)
print("Phase 3: Rotating masks to upright orientation...")
mask_dir = os.path.join(avatar_dir, 'mask')
mask_list = glob.glob(os.path.join(mask_dir, '*.png'))
for m_path in mask_list:
    m_img = cv2.imread(m_path)
    if m_img is not None:
        # Rotate 90 CW to match the new vertical frames
        m_rot = cv2.rotate(m_img, cv2.ROTATE_90_CLOCKWISE)
        cv2.imwrite(m_path, m_rot)
print(f"Rotated {len(mask_list)} masks.")

# 4. Save coords
with open(coords_out, 'wb') as f:
    pickle.dump(new_coords, f)
with open(mask_coords_out, 'wb') as f:
    pickle.dump(new_coords, f)

print(f"DONE! Rebuilt map with {len(new_coords)} vertical entries.")
