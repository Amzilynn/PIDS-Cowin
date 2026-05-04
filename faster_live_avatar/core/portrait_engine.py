import os
import torch
import numpy as np
import cv2
from base_repo.src.live_portrait_wrapper import LivePortraitWrapper
from base_repo.src.config.inference_config import InferenceConfig
from base_repo.src.config.crop_config import CropConfig
from base_repo.src.utils.cropper import Cropper

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

class LivePortraitEngine:
    def __init__(self, source_image_path: str):
        print(f"[Engine] SPEED-STREAM: Initializing with {source_image_path}")
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        print(f"[Engine] DEVICE: Using {self.device.upper()} mode.")
        
        cfg = InferenceConfig()
        cfg.checkpoint_F = os.path.join(ROOT_DIR, "base_repo/pretrained_weights/liveportrait/base_models/appearance_feature_extractor.pth")
        cfg.checkpoint_M = os.path.join(ROOT_DIR, "base_repo/pretrained_weights/liveportrait/base_models/motion_extractor.pth")
        cfg.checkpoint_W = os.path.join(ROOT_DIR, "base_repo/pretrained_weights/liveportrait/base_models/warping_module.pth")
        cfg.checkpoint_G = os.path.join(ROOT_DIR, "base_repo/pretrained_weights/liveportrait/base_models/spade_generator.pth")
        cfg.checkpoint_S = os.path.join(ROOT_DIR, "base_repo/pretrained_weights/liveportrait/retargeting_models/stitching_retargeting_module.pth")
        cfg.flag_use_half_precision = True
        cfg.flag_stitching = True
        cfg.flag_pasteback = True
        cfg.flag_do_crop = True
        self.cfg = cfg
        
        self.wrapper = LivePortraitWrapper(cfg)
        self.cropper = Cropper(crop_cfg=CropConfig(), device_id=0 if self.device == 'cuda' else -1)
        
        # 1. Load and Crop Ava Source
        from base_repo.src.utils.crop import prepare_paste_back, paste_back
        self.prepare_paste_back = prepare_paste_back
        self.paste_back = paste_back
        
        self.source_image = cv2.imread(source_image_path)
        if self.source_image is None:
            raise Exception(f"Could not load image at {source_image_path}")
            
        self.source_image_rgb = cv2.cvtColor(self.source_image, cv2.COLOR_BGR2RGB)
        
        # AUTO-CROP: Ensure we only focus on the face
        print(f"[Engine] AUTO-CROP: Detecting face in {source_image_path}...")
        crop_info = self.cropper.crop_source_image(self.source_image_rgb, CropConfig())
        
        if crop_info is None:
            print("[Engine] WARNING: No face detected. Using full image (expect distortion).")
            self.source_prepared = self.wrapper.prepare_source(self.source_image_rgb)
            self.crop_info = None
            self.mask_ori_float = None
        else:
            print("[Engine] SUCCESS: Face detected and cropped.")
            self.source_prepared = self.wrapper.prepare_source(crop_info['img_crop_256x256'])
            self.crop_info = crop_info
            # PREPARE PASTE BACK MASK
            self.mask_ori_float = self.prepare_paste_back(
                self.cfg.mask_crop, 
                crop_info['M_c2o'], 
                dsize=(self.source_image_rgb.shape[1], self.source_image_rgb.shape[0])
            )
        
        # 2. Extract Keypoints
        with torch.no_grad():
            self.feature_3d = self.wrapper.extract_feature_3d(self.source_prepared)
            self.source_kp_info = self.wrapper.get_kp_info(self.source_prepared)
            self.kp_source = self.wrapper.transform_keypoint(self.source_kp_info)
        
        self.lip_ratio = torch.zeros((1, 2), device=self.device, dtype=torch.float16 if cfg.flag_use_half_precision else torch.float32)
        self.eye_ratio = torch.zeros((1, 3), device=self.device, dtype=torch.float16 if cfg.flag_use_half_precision else torch.float32)
        # SMOOTHING BUFFER
        self.prev_exp = self.source_kp_info['exp'].clone()

    def render_frame(self, lip_open: float, lip_spread: float, lip_pucker: float, eye_blink: float, head_tilt: float = 0.0):
        with torch.no_grad():
            # ==========================================
            # FAST MODE (Absolute Stability + Life)
            # ==========================================
            # B. Lip Sync Math
            target_exp = self.source_kp_info['exp'].clone()
            target_exp[0, 19, 1] += float(lip_open) * 0.10  
            target_exp[0, 17, 1] += float(lip_spread) * 0.06 
            target_exp[0, 20, 1] += float(lip_pucker) * 0.12 
            
            # TEMPORAL SMOOTHING (40% Old, 60% New)
            self.prev_exp = (self.prev_exp * 0.40) + (target_exp * 0.60)
            self.prev_exp = torch.clamp(self.prev_exp, -1.2, 1.2)
            
            driving_kp_info = {k: v.clone() if isinstance(v, torch.Tensor) else v for k, v in self.source_kp_info.items()}
            driving_kp_info['exp'] = self.prev_exp
            
            # C. TRANSFORM TO KEYPOINTS (Temporarily remove translation for rotation)
            original_t = driving_kp_info['t'].clone()
            driving_kp_info['t'] = torch.zeros_like(original_t)
            
            kp_driving = self.wrapper.transform_keypoint(driving_kp_info)
            
            # D. APPLY 3D HEAD SWAY
            if head_tilt != 0.0:
                from base_repo.src.utils.camera import get_rotation_matrix
                # Convert the small sine wave into degrees (Max ~3 degrees yaw)
                yaw_deg = torch.tensor([float(head_tilt) * 150.0], device=self.device)
                pitch_deg = torch.tensor([abs(float(head_tilt)) * 50.0], device=self.device)
                roll_deg = torch.tensor([float(head_tilt) * -50.0], device=self.device)
                
                R_sway = get_rotation_matrix(pitch_deg, yaw_deg, roll_deg)
                kp_driving = kp_driving @ R_sway
                
            # Add translation back
            kp_driving[:, :, 0:2] += original_t[:, None, 0:2]
            
            # D. STITCHING (Blended 70/30 for safety)
            # MUST be applied BEFORE eye retargeting!
            if self.wrapper.stitching_retargeting_module is not None:
                kp_stitched = self.wrapper.stitching(self.kp_source, kp_driving)
                blend = 0.7
                kp_driving = (kp_driving * (1.0 - blend)) + (kp_stitched * blend)
                
            # E. PERFECT BLINK (Using AI's native retargeting module)
            # Must be applied AFTER stitching, or stitching will erase the blink!
            if eye_blink > 0 and self.wrapper.stitching_retargeting_module is not None:
                # A positive delta ratio forces the eyelids together (closing them). 
                # A negative delta ratio forces them open. We use +0.4 to ensure a tight squeeze.
                eye_ratio = torch.tensor([[0.4, 0.4, 0.0]], device=self.device, dtype=self.kp_source.dtype)
                eye_delta = self.wrapper.retarget_eye(self.kp_source, eye_ratio)
                # Apply the blink delta proportionally
                kp_driving += (eye_delta * float(eye_blink))

            # F. Warp and Decode
            ret_dct = self.wrapper.warp_decode(self.feature_3d, self.kp_source, kp_driving)
            img_crop_out = self.wrapper.parse_output(ret_dct['out'])[0]
            
            # G. PASTE BACK TO ORIGINAL IMAGE
            if self.crop_info is not None:
                full_frame = self.paste_back(img_crop_out, self.crop_info['M_c2o'], self.source_image_rgb, self.mask_ori_float)
            else:
                full_frame = img_crop_out
            
            # H. OPTIMIZED STREAMING: Resize for the Dashboard
            # We keep the aspect ratio but limit height to 512px for speed
            h, w = full_frame.shape[:2]
            new_h = 512
            new_w = int(w * (new_h / h))
            frame_final = cv2.resize(full_frame, (new_w, new_h))
            
            return cv2.cvtColor(frame_final, cv2.COLOR_RGB2BGR)
