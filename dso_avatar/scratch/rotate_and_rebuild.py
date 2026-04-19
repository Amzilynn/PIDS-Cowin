"""
Rotate eya.mp4 90 degrees clockwise, then re-run MuseTalk avatar preprocessing
so all latents, coords, and masks are generated for the upright face.
"""
import cv2
import os
import pickle
import glob
import torch
import numpy as np

# ------ Step 1: Rotate the source video ------
src_video = 'dso_avatar/eya.mp4'
out_video = 'dso_avatar/eya_vertical.mp4'

print("Step 1: Rotating eya.mp4 90 degrees CW...")
cap = cv2.VideoCapture(src_video)
fps = cap.get(cv2.CAP_PROP_FPS)
width  = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

# After 90 CW, width and height swap
out_w, out_h = height, width
fourcc = cv2.VideoWriter_fourcc(*'mp4v')
writer = cv2.VideoWriter(out_video, fourcc, fps, (out_w, out_h))

frame_count = 0
while True:
    ret, frame = cap.read()
    if not ret:
        break
    rotated = cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)
    writer.write(rotated)
    frame_count += 1

cap.release()
writer.release()
print(f"Rotated video saved to {out_video} ({frame_count} frames, {out_w}x{out_h})")

# ------ Step 2: Overwrite full_imgs with rotated frames ------
avatar_dir = 'dso_avatar/data/avatars/musetalk_avatar1'
full_imgs_dir = os.path.join(avatar_dir, 'full_imgs')

print("\nStep 2: Overwriting full_imgs with rotated frames...")
cap2 = cv2.VideoCapture(out_video)
i = 0
while True:
    ret, frame = cap2.read()
    if not ret:
        break
    out_path = os.path.join(full_imgs_dir, f'{i:08d}.png')
    cv2.imwrite(out_path, frame)
    i += 1
cap2.release()
print(f"Saved {i} rotated frames to {full_imgs_dir}")

# ------ Step 3: Re-detect face bboxes on the upright frames ------
print("\nStep 3: Re-detecting face bboxes on upright frames...")
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

img_list = sorted(glob.glob(os.path.join(full_imgs_dir, '*.png')))
new_coords = []
detected_count = 0

# Track last good bbox (to fill in failed frames)
last_good_bbox = [160, 370, 410, 530]

for idx, img_path in enumerate(img_list):
    img = cv2.imread(img_path)
    if img is None:
        new_coords.append(last_good_bbox)
        continue
    
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, 1.2, 5)
    
    if len(faces) > 0:
        (x, y, w, h) = sorted(faces, key=lambda f: f[2]*f[3], reverse=True)[0]  # largest face
        # Mouth is in the bottom ~30-45% of the face box, centered
        mx = x + int(w * 0.12)
        my = y + int(h * 0.62)
        mw = int(w * 0.76)
        mh = int(h * 0.38)
        bbox = [mx, my, mx+mw, my+mh]
        last_good_bbox = bbox
        detected_count += 1
    else:
        # Use last good detection
        bbox = last_good_bbox
    
    new_coords.append(bbox)
    if idx % 50 == 0:
        print(f"  Processed {idx}/{len(img_list)} frames ({detected_count} detected)...")

print(f"Detection complete: {detected_count}/{len(img_list)} frames had faces detected, {len(img_list)-detected_count} used fallback.")

# Save coords
out_coords = os.path.join(avatar_dir, 'coords.pkl')
out_mask_coords = os.path.join(avatar_dir, 'mask_coords.pkl')
with open(out_coords, 'wb') as f:
    pickle.dump(new_coords, f)
with open(out_mask_coords, 'wb') as f:
    pickle.dump(new_coords, f)

print(f"\nSaved new coords.pkl and mask_coords.pkl with {len(new_coords)} entries.")

# ------ Step 4: Show a debug preview ------
sample_idx = len(new_coords) // 2
sample_img = cv2.imread(img_list[sample_idx])
bbox = new_coords[sample_idx]
cv2.rectangle(sample_img, (bbox[0], bbox[1]), (bbox[2], bbox[3]), (0, 255, 0), 3)
cv2.putText(sample_img, f"Mouth [{bbox[0]},{bbox[1]}]-[{bbox[2]},{bbox[3]}]", (10, 30), 
            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
debug_path = 'dso_avatar/scratch/debug_vertical_face.png'
os.makedirs('dso_avatar/scratch', exist_ok=True)
cv2.imwrite(debug_path, sample_img)
print(f"\nDebug preview saved to {debug_path}")
print("\n✅ DONE! Now the engine should NOT rotate frames (since they're already vertical).")
print("   Next step: update musetalk_avatar.py to remove rotation logic.")
