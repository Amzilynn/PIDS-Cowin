import cv2
import os
import numpy as np
import pickle
from tqdm import tqdm

def rebuild_sarah_clone():
    print("[*] Performing Structural Clone: Sarah Khalil -> Chinese Avatar Format...")
    
    avatar_dir = "data/avatars/sarah_static"
    # Clean old ones first
    import shutil
    if os.path.exists(f"{avatar_dir}/full_imgs"): shutil.rmtree(f"{avatar_dir}/full_imgs")
    if os.path.exists(f"{avatar_dir}/face_imgs"): shutil.rmtree(f"{avatar_dir}/face_imgs")
    
    os.makedirs(f"{avatar_dir}/full_imgs", exist_ok=True)
    os.makedirs(f"{avatar_dir}/face_imgs", exist_ok=True)
    
    # 1. Load the golden source image
    img_path = "avalive.jpg"
    img_orig = cv2.imread(img_path)
    if img_orig is None:
        print("[!] Error: avalive.jpg not found!")
        return
    
    # 2. MATCH CHINESE AVATAR RESOLUTION: 768x576
    print(f"[*] Resizing to Chinese Avatar standard: 768x576")
    img = cv2.resize(img_orig, (576, 768)) # Benchmark was (768, 576, 3) which is H=768, W=576
    h_scaled, w_scaled = img.shape[:2]

    # 3. Face Detection on scaled image
    cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
    face_cascade = cv2.CascadeClassifier(cascade_path)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, 1.1, 4)
    
    if len(faces) == 0:
        print("[!] Detection failed, using manual clone-mapping...")
        bw = int(w_scaled * 0.5)
        bx1 = (w_scaled // 2) - (bw // 2)
        by1 = int(h_scaled * 0.1)
        bx2 = bx1 + bw
        by2 = by1 + int(bw * 1.3)
    else:
        x, y, w, h = sorted(faces, key=lambda f: f[2]*f[3], reverse=True)[0]
        padding = 0.2
        bx1 = max(0, int(x - w * padding))
        by1 = max(0, int(y - h * padding))
        bx2 = min(w_scaled, int(x + w * (1 + padding)))
        by2 = min(h_scaled, int(y + h * (1 + padding)))

    print(f"[*] Clone Face BBox: ({bx1}, {by1}, {bx2}, {by2})")
    
    # 4. Generate 550 frames in PNG format with 8-digit padding
    coords = []
    
    for i in tqdm(range(550), desc="Cloning Dataset"):
        # Save Full Image as PNG (matches Chinese avatar naming)
        name = f"{i:08d}.png"
        full_path = f"{avatar_dir}/full_imgs/{name}"
        cv2.imwrite(full_path, img)
        
        # Extract Face Crop (256x256 matches Chinese benchmark)
        face_crop = img[by1:by2, bx1:bx2]
        face_resized = cv2.resize(face_crop, (256, 256))
        face_path = f"{avatar_dir}/face_imgs/{name}"
        cv2.imwrite(face_path, face_resized)
        
        # Store Coords: (y1, y2, x1, x2)
        coords.append((by1, by1+face_crop.shape[0], bx1, bx1+face_crop.shape[1]))

    # 5. Save coords.pkl
    with open(f"{avatar_dir}/coords.pkl", "wb") as f:
        pickle.dump(coords, f)
        
    print(f"\n[✓] Structural Clone Complete!")
    print(f"[i] Dataset matches benchmark 'wav2lip256_avatar1' exactly.")
    print(f"[i] Frames: 550 | Resolution: 768x576 | Format: PNG")

if __name__ == "__main__":
    rebuild_sarah_clone()
