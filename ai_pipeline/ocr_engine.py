import re
import cv2
import numpy as np
from typing import Tuple, Optional, List
from ai_pipeline.preprocessing import prepare_plate_for_ocr, apply_clahe

INDIAN_STATE_CODES = [
    "AN", "AP", "AR", "AS", "BR", "CH", "CG", "DD", "DL", "DN", "GA", 
    "GJ", "HR", "HP", "JH", "JK", "KA", "KL", "LA", "LD", "MH", "ML", "MN", 
    "MP", "MZ", "NL", "OD", "PB", "PY", "RJ", "SK", "TN", "TR", "TS", "UK", 
    "UP", "WB"
]

DICT_CHAR_TO_INT = {
    'O': '0', 'D': '0', 'Q': '0',
    'I': '1', 'L': '1', 'T': '1',
    'Z': '2',
    'E': '3',
    'A': '4',
    'S': '5',
    'G': '6',
    'B': '8',
}

DICT_INT_TO_CHAR = {
    '0': 'O',
    '1': 'I',
    '2': 'Z',
    '3': 'E',
    '4': 'A',
    '5': 'S',
    '6': 'G',
    '8': 'B',
}

def pad_and_resize_char(crop: np.ndarray, target_size: tuple[int, int] = (36, 48)) -> np.ndarray:
    tw, th = target_size
    ch, cw = crop.shape[:2]
    if ch == 0 or cw == 0:
        return np.zeros((th, tw), dtype="uint8")
    scale = min(tw / cw, th / ch) * 0.88
    nw, nh = max(1, int(cw * scale)), max(1, int(ch * scale))
    scaled = cv2.resize(crop, (nw, nh), interpolation=cv2.INTER_AREA)
    padded = np.zeros((th, tw), dtype="uint8")
    px = (tw - nw) // 2
    py = (th - nh) // 2
    padded[py:py+nh, px:px+nw] = scaled
    return padded

def build_character_templates() -> dict[str, np.ndarray]:
    chars = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    templates = {}
    tw, th = 36, 48
    for ch in chars:
        canvas = np.zeros((th, tw), dtype="uint8")
        font = cv2.FONT_HERSHEY_SIMPLEX
        (w, h), _ = cv2.getTextSize(ch, font, 1.2, 3)
        tx = max(0, int((tw - w) / 2))
        ty = int((th + h) / 2)
        cv2.putText(canvas, ch, (tx, ty), font, 1.2, 255, 3)
        c_box = cv2.boundingRect(canvas)
        if c_box[2] > 0 and c_box[3] > 0:
            char_crop = canvas[c_box[1]:c_box[1]+c_box[3], c_box[0]:c_box[0]+c_box[2]]
            templates[ch] = pad_and_resize_char(char_crop, (tw, th))
        else:
            templates[ch] = canvas
    return templates

CHAR_TEMPLATES = build_character_templates()

class PlateOCREngine:
    """
    Hybrid Deep-Learning + Morphological License Plate OCR Engine.
    Combines EasyOCR PyTorch neural text recognizer, adaptive CLAHE/dewarping preprocessor,
    and strict Indian HSRP positional syntax validation.
    """
    def __init__(self, use_deep_ocr: bool = True, gpu: bool = False):
        self.templates = CHAR_TEMPLATES
        self.use_deep_ocr = use_deep_ocr
        self.easyocr_reader = None
        
        if use_deep_ocr:
            try:
                import easyocr
                # Initialize EasyOCR reader for English alphanumeric characters
                self.easyocr_reader = easyocr.Reader(['en'], gpu=gpu, verbose=False)
                print("Deep Learning OCR (EasyOCR PyTorch backend) initialized successfully.")
            except Exception as e:
                print(f"Notice: EasyOCR fallback to high-speed morphological matcher ({e})")
                self.easyocr_reader = None

    def extract_text_from_plate(self, plate_crop: np.ndarray) -> Tuple[str, float, str]:
        """
        Runs multi-stage OCR extraction on plate crop:
        1. Preprocessing (CLAHE, perspective rectification, noise reduction)
        2. Deep Learning OCR / Neural recognizer
        3. Fallback character contour correlation matching
        4. Indian HSRP positional grammar normalization
        """
        if plate_crop is None or plate_crop.size == 0:
            return "", 0.0, ""

        # Preprocessing: CLAHE contrast boost and bilateral smoothing
        preprocessed = prepare_plate_for_ocr(plate_crop)

        # Stage 1: Try Deep Learning OCR if available
        if self.easyocr_reader is not None:
            try:
                results = self.easyocr_reader.readtext(
                    preprocessed,
                    allowlist='0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ',
                    detail=1,
                    paragraph=False
                )
                if results:
                    # Combine high confidence text chunks
                    detected_text = "".join([res[1] for res in results])
                    avg_conf = float(np.mean([res[2] for res in results]))
                    
                    cleaned_text = re.sub(r'[^A-Z0-9]', '', detected_text.upper())
                    if len(cleaned_text) >= 8:
                        norm_plate, format_conf = self.normalize_indian_plate(cleaned_text)
                        final_conf = round(avg_conf * 0.4 + format_conf * 0.6, 2)
                        return norm_plate, final_conf, cleaned_text
            except Exception:
                pass # Fallback to template matching

        # Stage 2: Robust Morphological & Correlation Segmentation OCR
        return self._extract_text_morphological(preprocessed)

    def _extract_text_morphological(self, plate_crop: np.ndarray) -> Tuple[str, float, str]:
        gray = cv2.cvtColor(plate_crop, cv2.COLOR_BGR2GRAY) if len(plate_crop.shape) == 3 else plate_crop
        _, thresh = cv2.threshold(gray, 140, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

        h, w = thresh.shape[:2]
        ind_strip_boundary = int(w * 0.08)
        thresh[:, 0:ind_strip_boundary] = 0
        thresh[0:max(1, int(h * 0.05)), :] = 0
        thresh[int(h * 0.95):h, :] = 0

        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        char_boxes = []

        for c in contours:
            cx, cy, cw, ch_h = cv2.boundingRect(c)
            aspect = float(cw) / float(ch_h)
            height_ratio = float(ch_h) / float(h)
            area = cw * ch_h

            if cx >= ind_strip_boundary and 0.16 <= height_ratio <= 0.85 and (area >= 0.002 * w * h):
                if aspect > 1.35 and cw > 35:
                    half_w = cw // 2
                    char_boxes.append((cx, cy, half_w, ch_h))
                    char_boxes.append((cx + half_w, cy, cw - half_w, ch_h))
                elif 0.08 <= aspect <= 1.35:
                    char_boxes.append((cx, cy, cw, ch_h))

        char_boxes = sorted(char_boxes, key=lambda b: b[0])

        extracted_chars = []
        confidences = []

        for cx, cy, cw, ch_h in char_boxes:
            crop = thresh[cy:cy+ch_h, cx:cx+cw]
            normalized_char = pad_and_resize_char(crop, (36, 48))

            best_score = -1.0
            best_ch = "?"

            for ch, t in self.templates.items():
                score = cv2.matchTemplate(normalized_char, t, cv2.TM_CCOEFF_NORMED)[0][0]
                if score > best_score:
                    best_score = score
                    best_ch = ch

            if best_ch in ('O', '0'):
                h_c, w_c = crop.shape[:2]
                if w_c > 8 and h_c > 10:
                    mid_left = crop[int(h_c*0.25):int(h_c*0.75), 0:max(1, int(w_c*0.25))]
                    density = float(np.mean(mid_left)) / 255.0
                    if density > 0.65:
                        best_ch = 'D'

            if best_score >= 0.20 and best_ch != "?":
                extracted_chars.append(best_ch)
                confidences.append(max(0.60, min(0.99, float(best_score))))

        raw_plate = "".join(extracted_chars)
        avg_conf = float(np.mean(confidences)) if confidences else 0.50

        normalized_plate, format_conf = self.normalize_indian_plate(raw_plate)
        final_conf = round(avg_conf * 0.5 + format_conf * 0.5, 2)

        return normalized_plate, final_conf, raw_plate

    def normalize_indian_plate(self, text: str) -> Tuple[str, float]:
        """
        Applies strict Indian HSRP registration grammar rules:
        - Pos 0-1: State Code ([A-Z]{2}) with fuzzy auto-correction to nearest valid state code
        - Pos 2-3: District RTO Code ([0-9]{2})
        - Pos 4..N-4: Series Code ([A-Z]{1,3})
        - Pos N-4..N: Vehicle Unique Digits ([0-9]{4})
        """
        cleaned = re.sub(r'[^A-Z0-9]', '', text.upper())
        if len(cleaned) < 8:
            return cleaned, 0.60

        if len(cleaned) > 10:
            cleaned = cleaned[-10:]

        char_list = list(cleaned)

        # 1. State Code (pos 0-1) -> Letters & Nearest valid state code lookup
        for i in range(min(2, len(char_list))):
            if char_list[i] in DICT_INT_TO_CHAR:
                char_list[i] = DICT_INT_TO_CHAR[char_list[i]]

        candidate_state = "".join(char_list[:2])
        if candidate_state not in INDIAN_STATE_CODES:
            for valid_st in INDIAN_STATE_CODES:
                if valid_st[1] == candidate_state[1]: # e.g. OL -> DL, UR -> HR
                    char_list[0] = valid_st[0]
                    break

        # 2. District Code (pos 2-3) -> Digits
        for i in range(2, min(4, len(char_list))):
            if char_list[i] in DICT_CHAR_TO_INT:
                char_list[i] = DICT_CHAR_TO_INT[char_list[i]]

        # 3. Unique Number (last 4 pos) -> Digits
        last_4_start = len(char_list) - 4
        for i in range(last_4_start, len(char_list)):
            if char_list[i] in DICT_CHAR_TO_INT:
                char_list[i] = DICT_CHAR_TO_INT[char_list[i]]

        # 4. Series Code (pos 4 to last_4_start) -> Letters
        for i in range(4, last_4_start):
            if char_list[i] in DICT_INT_TO_CHAR:
                char_list[i] = DICT_INT_TO_CHAR[char_list[i]]

        normalized = "".join(char_list)

        std_pattern = r'^[A-Z]{2}[0-9]{2}[A-Z]{1,3}[0-9]{4}$'
        bh_pattern = r'^[0-9]{2}BH[0-9]{4}[A-Z]{1,2}$'

        if re.match(std_pattern, normalized):
            state_code = normalized[:2]
            conf_boost = 0.98 if state_code in INDIAN_STATE_CODES else 0.92
            return normalized, conf_boost
        elif re.match(bh_pattern, normalized):
            return normalized, 0.95
        else:
            return normalized, 0.75
