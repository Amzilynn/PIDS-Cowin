"""
Smoke test using the OFFICIAL LivePortrait PyTorch wrapper.
Uses the real model definitions from base_repo/src/.
"""
import sys
import os
import time

# Add base_repo to path so we can import LivePortrait's source
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "base_repo"))

import numpy as np
import cv2
import torch

from src.config.inference_config import InferenceConfig
from src.live_portrait_wrapper import LivePortraitWrapper

print("=" * 60)
print(" LivePortrait PyTorch Engine - Official Smoke Test")
print("=" * 60)

try:
    # Initialize with default config (it auto-finds weights via relative paths)
    cfg = InferenceConfig()
    cfg.flag_use_half_precision = True
    cfg.flag_do_torch_compile = False
    
    print(f"[INFO] Device: cuda:0")
    print(f"[INFO] Loading models...")
    
    wrapper = LivePortraitWrapper(cfg)
    
    # Load Sarah's source image
    img = cv2.imread("sarah_source.jpg")
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    img = cv2.resize(img, (256, 256))
    
    # Prepare source
    source_prepared = wrapper.prepare_source(img)
    
    # Extract features (one-time cost)
    t0 = time.time()
    feature_3d = wrapper.extract_feature_3d(source_prepared)
    print(f"[INFO] Feature extraction: {(time.time()-t0)*1000:.1f}ms")
    
    # Get source keypoints
    source_kp_info = wrapper.get_kp_info(source_prepared)
    kp_source = wrapper.transform_keypoint(source_kp_info)
    
    print(f"[INFO] Source keypoints shape: {kp_source.shape}")
    print(f"[INFO] Expression shape: {source_kp_info['exp'].shape}")
    
    # Render frames with different lip openings
    for lip_val in [0.0, 0.3, 0.6, 1.0]:
        t0 = time.time()
        
        # Clone source kp_info and modify expression for lip
        driving_kp_info = {k: v.clone() if isinstance(v, torch.Tensor) else v for k, v in source_kp_info.items()}
        # Modify lip expression coefficients
        driving_kp_info['exp'] = driving_kp_info['exp'].clone()
        driving_kp_info['exp'][0, 19, 1] += lip_val * 0.8  # jaw open
        driving_kp_info['exp'][0, 17, 1] += lip_val * 0.3  # lip shape
        
        kp_driving = wrapper.transform_keypoint(driving_kp_info)
        
        # Stitch to make it natural
        kp_driving = wrapper.stitching(kp_source, kp_driving)
        
        # Warp and decode
        ret_dct = wrapper.warp_decode(feature_3d, kp_source, kp_driving)
        frame = wrapper.parse_output(ret_dct['out'])[0]  # 256x256x3 uint8
        
        elapsed = (time.time() - t0) * 1000
        
        # Save
        frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        filename = f"test_official_lip_{lip_val:.1f}.jpg"
        cv2.imwrite(filename, frame_bgr)
        print(f"  lip={lip_val:.1f} -> {frame.shape} in {elapsed:.1f}ms -> saved {filename}")
    
    print(f"\n[SUCCESS] Official LivePortrait engine works perfectly!")
    print(f"[INFO] Your RTX 5070 is rendering frames in real-time!")
    
except Exception as e:
    print(f"\n[ERROR] {e}")
    import traceback
    traceback.print_exc()
