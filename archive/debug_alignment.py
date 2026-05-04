import pickle
import cv2
import os

# Paths
avatar_dir = 'dso_avatar/data/avatars/musetalk_avatar1'
img_path = os.path.join(avatar_dir, 'full_imgs/00000000.png')
coords_path = os.path.join(avatar_dir, 'coords.pkl')

# Load data
img = cv2.imread(img_path)
if img is None:
    print(f"Error: Could not load image {img_path}")
    exit(1)
h, w = img.shape[:2]
with open(coords_path, 'rb') as f:
    coords = pickle.load(f)

bbox = coords[0] # [x1, y1, x2, y2]
print(f"Original Video Size: {w}x{h}")
print(f"Original Bbox: {bbox}")

# --- TEST 90 CW ---
def rotate_bbox_90cw(bbox, old_h):
    x1, y1, x2, y2 = bbox
    # x' = H - y, y' = x
    nx1, ny1 = old_h - y2, x1
    nx2, ny2 = old_h - y1, x2
    return [nx1, ny1, nx2, ny2]

new_bbox_cw = rotate_bbox_90cw(bbox, h)
print(f"Bbox after 90 CW: {new_bbox_cw} (Target size {h}x{w})")

# --- TEST 90 CCW ---
def rotate_bbox_90ccw(bbox, old_w):
    x1, y1, x2, y2 = bbox
    # x' = y, y' = W - x
    nx1, ny1 = y1, old_w - x2
    nx2, ny2 = y2, old_w - x1
    return [nx1, ny1, nx2, ny2]

new_bbox_ccw = rotate_bbox_90ccw(bbox, w)
print(f"Bbox after 90 CCW: {new_bbox_ccw} (Target size {h}x{w})")

# --- TEST 180 ---
def rotate_bbox_180(bbox, old_w, old_h):
    x1, y1, x2, y2 = bbox
    # x' = W - x, y' = H - y
    nx1, ny1 = old_w - x2, old_h - y2
    nx2, ny2 = old_w - x1, old_h - y1
    return [nx1, ny1, nx2, ny2]

new_bbox_180 = rotate_bbox_180(bbox, w, h)
print(f"Bbox after 180: {new_bbox_180} (Target size {w}x{h})")
