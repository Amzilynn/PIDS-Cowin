import cv2
import numpy as np
import os

# Create scratch directory
os.makedirs('dso_avatar/scratch', exist_ok=True)

img_path = 'dso_avatar/data/avatars/musetalk_avatar1/full_imgs/00000000.png'
img = cv2.imread(img_path)

if img is None:
    print(f"Error: Could not load {img_path}")
    exit(1)

# Rotate image to vertical (as the engine now does)
img_vertical = cv2.rotate(img, cv2.ROTATE_90_CLOCKWISE)
h, w = img_vertical.shape[:2]

# Attempt to find face and mouth using Haar Cascades
# (Assuming standard OpenCV paths or just trying to find it)
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
mouth_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_smile.xml') # or mcs_mouth if available

gray = cv2.cvtColor(img_vertical, cv2.COLOR_BGR2GRAY)
faces = face_cascade.detectMultiScale(gray, 1.3, 5)

if len(faces) == 0:
    print("No faces detected with Haar.")
    # Fallback to a hardcoded guess based on typical human proportions in a vertical 576x1024 frame
    # Center X: 288. Mouth is usually around Y=750.
    new_bbox = [188, 650, 388, 850]
    print(f"USING_GUESS: {new_bbox}")
else:
    (x, y, fw, fh) = faces[0]
    # Estimate mouth based on face box: bottom third of the face
    mx = x + int(fw * 0.15)
    my = y + int(fh * 0.65)
    mw = int(fw * 0.7)
    mh = int(fh * 0.3)
    new_bbox = [mx, my, mx+mw, my+mh]
    print(f"DETECTED_BBOX: {new_bbox}")

# Save debug image
debug_img = img_vertical.copy()
cv2.rectangle(debug_img, (new_bbox[0], new_bbox[1]), (new_bbox[2], new_bbox[3]), (0, 255, 0), 3)
cv2.imwrite('dso_avatar/scratch/detected_mouth.png', debug_img)
