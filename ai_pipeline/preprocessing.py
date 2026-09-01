import cv2
import numpy as np
from typing import Tuple, List, Optional

def apply_clahe(image: np.ndarray, clip_limit: float = 2.0, tile_grid_size: tuple[int, int] = (8, 8)) -> np.ndarray:
    """
    Applies Contrast Limited Adaptive Histogram Equalization (CLAHE)
    to enhance license plate visibility in poor lighting, shadows, or glare.
    """
    if image is None or image.size == 0:
        return image

    if len(image.shape) == 3:
        lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=tile_grid_size)
        l_enhanced = clahe.apply(l)
        enhanced_lab = cv2.merge((l_enhanced, a, b))
        return cv2.cvtColor(enhanced_lab, cv2.COLOR_LAB2BGR)
    else:
        clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=tile_grid_size)
        return clahe.apply(image)

def upscale_plate_if_needed(plate_crop: np.ndarray, target_height: int = 72) -> np.ndarray:
    """
    Upscales small license plate crops using high-quality bicubic interpolation
    so that OCR neural nets and morphological extractors have sufficient pixel resolution.
    """
    if plate_crop is None or plate_crop.size == 0:
        return plate_crop
        
    h, w = plate_crop.shape[:2]
    if h < target_height:
        scale = target_height / float(h)
        new_w = int(w * scale)
        return cv2.resize(plate_crop, (new_w, target_height), interpolation=cv2.INTER_CUBIC)
    return plate_crop

def prepare_plate_for_ocr(plate_img: np.ndarray) -> np.ndarray:
    """
    Full robust preprocessing pipeline:
    1. Upscale low-res crops
    2. CLAHE contrast enhancement
    3. Bilateral edge-preserving noise smoothing
    """
    if plate_img is None or plate_img.size == 0:
        return plate_img

    upscaled = upscale_plate_if_needed(plate_img, target_height=80)
    enhanced = apply_clahe(upscaled, clip_limit=2.5)
    smoothed = cv2.bilateralFilter(enhanced, d=5, sigmaColor=50, sigmaSpace=50)
    return smoothed

def get_ocr_variants(plate_img: np.ndarray) -> List[np.ndarray]:
    """
    Generates enhanced image variants (Color enhanced, Grayscale CLAHE, and Otsu Binarized)
    for multi-pass OCR recognition.
    """
    if plate_img is None or plate_img.size == 0:
        return []

    base = prepare_plate_for_ocr(plate_img)
    gray = cv2.cvtColor(base, cv2.COLOR_BGR2GRAY) if len(base.shape) == 3 else base
    
    # Variant 1: Enhanced color / grayscale
    clahe_gray = apply_clahe(gray, clip_limit=3.0)
    
    # Variant 2: Adaptive Otsu thresholded (clean black text on white background)
    _, otsu = cv2.threshold(clahe_gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    
    # Variant 3: Inverted threshold (if plate has white text on dark background or vice versa)
    otsu_inv = cv2.bitwise_not(otsu)

    return [base, clahe_gray, otsu, otsu_inv]
