import cv2
import numpy as np

def apply_clahe(image: np.ndarray, clip_limit: float = 2.5, tile_grid_size: tuple[int, int] = (8, 8)) -> np.ndarray:
    """
    Applies Contrast Limited Adaptive Histogram Equalization (CLAHE)
    to enhance license plate visibility in poor lighting, nighttime, or rain/fog conditions.
    """
    if len(image.shape) == 3:
        # Convert to LAB color space and apply CLAHE to the L (luminance) channel
        lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=tile_grid_size)
        l_enhanced = clahe.apply(l)
        enhanced_lab = cv2.merge((l_enhanced, a, b))
        return cv2.cvtColor(enhanced_lab, cv2.COLOR_LAB2BGR)
    else:
        clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=tile_grid_size)
        return clahe.apply(image)

def rectify_plate_perspective(plate_crop: np.ndarray, target_size: tuple[int, int] = (300, 100)) -> np.ndarray:
    """
    Detects 4-corner polygon contour of an angled license plate and performs
    perspective warp transformation to rectify it flat before OCR.
    """
    if plate_crop is None or plate_crop.size == 0:
        return plate_crop

    h, w = plate_crop.shape[:2]
    if h < 20 or w < 40:
        return cv2.resize(plate_crop, target_size, interpolation=cv2.INTER_CUBIC)

    gray = cv2.cvtColor(plate_crop, cv2.COLOR_BGR2GRAY) if len(plate_crop.shape) == 3 else plate_crop
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    edged = cv2.Canny(blurred, 50, 200)

    contours, _ = cv2.findContours(edged, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    contours = sorted(contours, key=cv2.contourArea, reverse=True)[:5]

    quad_contour = None
    for c in contours:
        peri = cv2.arcLength(c, True)
        approx = cv2.approxPolyDP(c, 0.04 * peri, True)
        if len(approx) == 4 and cv2.contourArea(c) > (w * h * 0.2):
            quad_contour = approx
            break

    if quad_contour is not None:
        pts = quad_contour.reshape(4, 2).astype("float32")
        # Order points: top-left, top-right, bottom-right, bottom-left
        rect = order_points(pts)
        dst = np.array([
            [0, 0],
            [target_size[0] - 1, 0],
            [target_size[0] - 1, target_size[1] - 1],
            [0, target_size[1] - 1]
        ], dtype="float32")

        M = cv2.getPerspectiveTransform(rect, dst)
        warped = cv2.warpPerspective(plate_crop, M, target_size)
        return warped

    # If no 4-point quadrilateral detected, return bicubic resized crop
    return cv2.resize(plate_crop, target_size, interpolation=cv2.INTER_CUBIC)

def order_points(pts: np.ndarray) -> np.ndarray:
    rect = np.zeros((4, 2), dtype="float32")
    s = pts.sum(axis=1)
    rect[0] = pts[np.argmin(s)] # Top-left has smallest sum
    rect[2] = pts[np.argmax(s)] # Bottom-right has largest sum

    diff = np.diff(pts, axis=1)
    rect[1] = pts[np.argmin(diff)] # Top-right has smallest diff
    rect[3] = pts[np.argmax(diff)] # Bottom-left has largest diff
    return rect

def prepare_plate_for_ocr(plate_img: np.ndarray) -> np.ndarray:
    """
    Full preprocessing pipeline: CLAHE boost + perspective rectification + bilateral smoothing.
    """
    rectified = rectify_plate_perspective(plate_img)
    enhanced = apply_clahe(rectified, clip_limit=2.0)
    smoothed = cv2.bilateralFilter(enhanced, d=7, sigmaColor=75, sigmaSpace=75)
    return smoothed
