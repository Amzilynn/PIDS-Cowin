import argparse
import glob
import json
import os
import pickle
import shutil
import sys
import cv2
import numpy as np
import torch
from tqdm import tqdm

# Add the root directory to sys.path to ensure absolute imports work
current_file_path = os.path.abspath(__file__)
project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_file_path)))
# Force project_root to be first in sys.path to prevent module shadowing
if project_root in sys.path:
    sys.path.remove(project_root)
sys.path.insert(0, project_root)

from avatars.musetalk.utils.preprocessing import get_landmark_and_bbox, read_imgs
from avatars.musetalk.utils.utils import load_all_model

try:
    from avatars.musetalk.utils.face_parsing import FaceParsing
except ImportError:
    from utils.face_parsing import FaceParsing

def video2imgs(vid_path, save_path, ext='.png', cut_frame=10000000):
    cap = cv2.VideoCapture(vid_path)
    count = 0
    while True:
        if count > cut_frame:
            break
        ret, frame = cap.read()
        if ret:
            cv2.putText(frame, "LiveTalking", (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.3, (128,128,128), 1)
            cv2.imwrite(f"{save_path}/{count:08d}.png", frame)
            count += 1
        else:
            break

def is_video_file(file_path):
    video_exts = ['.mp4', '.mkv', '.flv', '.avi', '.mov']
    file_ext = os.path.splitext(file_path)[1].lower()
    return file_ext in video_exts

def create_dir(dir_path):
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)

def create_musetalk_human(file, avatar_id):
    # Current working directory (usually the root of LiveTalking)
    current_dir = os.getcwd()
    
    save_path = os.path.join(current_dir, f'data/avatars/{avatar_id}')
    save_full_path = os.path.join(save_path, 'full_imgs')
    mask_out_path = os.path.join(save_path, 'mask')
    
    create_dir(save_path)
    create_dir(save_full_path)
    create_dir(mask_out_path)

    mask_coords_path = os.path.join(save_path, 'mask_coords.pkl')
    coords_path = os.path.join(save_path, 'coords.pkl')
    latents_out_path = os.path.join(save_path, 'latents.pt')

    with open(os.path.join(save_path, 'avator_info.json'), "w") as f:
        json.dump({
            "avatar_id": avatar_id,
            "video_path": file,
            "bbox_shift": args.bbox_shift
        }, f)

    if os.path.isfile(file):
        if is_video_file(file):
            video2imgs(file, save_full_path, ext='png')
        else:
            shutil.copyfile(file, os.path.join(save_full_path, os.path.basename(file)))
    else:
        files = os.listdir(file)
        files.sort()
        files = [f for f in files if f.split(".")[-1] == "png"]
        for filename in files:
            shutil.copyfile(os.path.join(file, filename), os.path.join(save_full_path, filename))
            
    input_img_list = sorted(glob.glob(os.path.join(save_full_path, '*.[jpJP][pnPN]*[gG]')))
    print("extracting landmarks with MediaPipe...")
    coord_list, frame_list = get_landmark_and_bbox(input_img_list, args.bbox_shift)
    
    input_latent_list = []
    idx = -1
    coord_placeholder = (0, 0, 0, 0)
    
    print("encoding latents to GPU...")
    for bbox, frame in zip(coord_list, frame_list):
        idx = idx + 1
        if bbox == coord_placeholder:
            continue
        x1, y1, x2, y2 = bbox
        if args.version == "v15":
            y2 = y2 + args.extra_margin
            y2 = min(y2, frame.shape[0])
            coord_list[idx] = [x1, y1, x2, y2]
            
        crop_frame = frame[y1:y2, x1:x2]
        # Ensure frame is not empty
        if crop_frame.size == 0:
            continue
            
        resized_crop_frame = cv2.resize(crop_frame, (256, 256), interpolation=cv2.INTER_LANCZOS4)
        
        # Prepare for VAE (Move to GPU/Half)
        def preprocess_img(img, half_mask=False):
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            img = img / 255.0
            if half_mask:
                img[img.shape[0]//2:, :] = -1
            return torch.from_numpy(img).float().permute(2, 0, 1).unsqueeze(0)
        img_tensor = preprocess_img(resized_crop_frame, half_mask=False).to(device=vae.vae.device, dtype=vae.vae.dtype)
        img_tensor_mask = preprocess_img(resized_crop_frame, half_mask=True).to(device=vae.vae.device, dtype=vae.vae.dtype)
        
        with torch.no_grad():
            ref_latents = vae.vae.encode(img_tensor).latent_dist.mode() * vae.vae.config.scaling_factor
            masked_latents = vae.vae.encode(img_tensor_mask).latent_dist.mode() * vae.vae.config.scaling_factor
            latents = torch.cat([masked_latents, ref_latents], dim=1)
            
        input_latent_list.append(latents.cpu()) # Save to CPU to avoid OOM during generation

    print("generating masks...")
    mask_coords_list_cycle = []
    for i, frame in enumerate(tqdm(frame_list)):
        x1, y1, x2, y2 = coord_list[i]
        
        # Determine mode
        mode = args.parsing_mode if args.version == "v15" else "raw"
        
        from avatars.musetalk.utils.blending import get_image_prepare_material
        mask, crop_box = get_image_prepare_material(frame, [x1, y1, x2, y2], fp=fp, mode=mode)
        cv2.imwrite(os.path.join(mask_out_path, f"{i:08d}.png"), mask)

        mask_coords_list_cycle.append(crop_box)

    with open(mask_coords_path, 'wb') as f:
        pickle.dump(mask_coords_list_cycle, f)
    with open(coords_path, 'wb') as f:
        pickle.dump(coord_list, f)
    torch.save(input_latent_list, latents_out_path)
    print(f"Avatar {avatar_id} created successfully!")

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", type=str, default='eya.mp4')
    parser.add_argument("--avatar_id", type=str, default='musetalk_avatar1')
    parser.add_argument("--version", type=str, default="v15")
    parser.add_argument("--gpu_id", type=int, default=0)
    parser.add_argument("--left_cheek_width", type=int, default=90)
    parser.add_argument("--right_cheek_width", type=int, default=90)
    parser.add_argument("--bbox_shift", type=int, default=0)
    parser.add_argument("--extra_margin", type=int, default=10)
    parser.add_argument("--parsing_mode", default='jaw')
    args = parser.parse_args()

    device = torch.device(f"cuda:{args.gpu_id}" if torch.cuda.is_available() else "cpu")

    # Load models with the synced utils
    vae, unet, pe = load_all_model(device=device)
    vae.vae = vae.vae.half().to(device)
    
    fp = FaceParsing(
        left_cheek_width=args.left_cheek_width,
        right_cheek_width=args.right_cheek_width
    )

    create_musetalk_human(args.file, args.avatar_id)
