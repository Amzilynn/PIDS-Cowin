import numpy as np
import cv2
import copy

def get_image_blending(image,face,face_box,mask_array,crop_box):
    # Optimized numpy blending for real-time performance
    x, y, x1, y1 = face_box
    x_s, y_s, x_e, y_e = crop_box
    
    # Dynamic mask softening: 
    # Convert mask to grayscale and apply a soft Gaussian blur to remove sharp edges.
    mask_image = cv2.cvtColor(mask_array, cv2.COLOR_BGR2GRAY)
    
    # Kernel size based on face patch dimensions for balanced feathering
    # Reduced multiplier from 0.15 to 0.05 to decrease blurriness
    kernel_size = int(max(face.shape) * 0.05) | 1 
    mask_image = cv2.GaussianBlur(mask_image, (kernel_size, kernel_size), 0)
    
    # Normalize mask to 0-1 range
    mask_alpha = (mask_image / 255.0).astype(np.float32)
    mask_alpha = np.expand_dims(mask_alpha, axis=-1)
    
    # Get the target area (background)
    target_area = image[y_s:y_e, x_s:x_e].copy().astype(np.float32)
    
    # Prepare the face area (foreground)
    face_large = target_area.copy()
    h_f, w_f = face.shape[:2]
    
    # Ensure coordinates for pasting are clipped to target area boundaries to prevent crashes
    target_y1 = max(0, y - y_s)
    target_x1 = max(0, x - x_s)
    target_y2 = min(face_large.shape[0], target_y1 + h_f)
    target_x2 = min(face_large.shape[1], target_x1 + w_f)
    
    # Clip face patch
    face_patch = face[0:target_y2-target_y1, 0:target_x2-target_x1].astype(np.float32)
    
    # --- LUMINANCE MATCHING ---
    # Match the mean brightness of the face patch to the original target background area.
    # This removes the "white box" tint caused by lighting differences.
    background_roi = target_area[target_y1:target_y2, target_x1:target_x2]
    for i in range(3): # Process R, G, B channels
        mean_bg = np.mean(background_roi[:, :, i])
        mean_face = np.mean(face_patch[:, :, i])
        face_patch[:, :, i] = np.clip(face_patch[:, :, i] + (mean_bg - mean_face), 0, 255)
        
    face_large[target_y1:target_y2, target_x1:target_x2] = face_patch
    
    # Linear alpha blending with soft feathering
    blended = face_large * mask_alpha + target_area * (1 - mask_alpha)
    
    # Update the original image with the blended result
    out_image = image.copy()
    out_image[y_s:y_e, x_s:x_e] = blended.astype(np.uint8)
    
    return out_image