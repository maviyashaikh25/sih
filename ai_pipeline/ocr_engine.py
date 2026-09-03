import re
import cv2
import numpy as np
from typing import Tuple, Optional, List
from ai_pipeline.preprocessing import prepare_plate_for_ocr, get_ocr_variants, apply_clahe

INDIAN_STATE_CODES = [
    "AN", "AP", "AR", "AS", "BR", "CH", "CG", "DD", "DL", "DN", "GA", 
    "GJ", "HR", "HP", "JH", "JK", "KA", "KL", "LA", "LD", "MH", "ML", "MN", 
    "MP", "MZ", "NL", "OD", "PB", "PY", "RJ", "SK", "TN", "TR", "TS", "UK", 
    "UP", "WB"
]

DICT_CHAR_TO_INT = {
    'O': '0', 'D': '0', 'Q': '0',
    'I': '1', 'L': '1', 'T': '1', 'J': '1',
    'Z': '2',
    'E': '3',
    'A': '4',
    'S': '5',
    'G': '6', 'C': '0',
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

STATE_CORRECTIONS = {
    "K4": "KA", "K1": "KA", "KO": "KA", "K0": "KA",
    "0L": "DL", "OL": "DL", "D1": "DL",
    "M4": "MH", "NH": "MH", "HH": "MH",
    "U4": "UP", "DP": "UP", "OP": "UP",
    "H4": "HR", "UR": "HR",
    "G1": "GJ", "6J": "GJ",
    "T1": "TN", "TM": "TN", "1N": "TN",
    "W8": "WB", "HB": "WB", "MB": "WB",
    "A4": "AP", "AF": "AP",
    "T5": "TS", "1S": "TS",
    "R1": "RJ", "P1": "PB",
    "C4": "CG", "CH": "CH"
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

import torch

class PlateOCREngine:
    """
    State-of-the-Art Deep Learning License Plate OCR Engine.
    Combines EasyOCR PyTorch neural text recognizer, multi-scale image enhancement,
    and strict Indian HSRP positional grammar validation and error correction.
    """
    def __init__(self, use_deep_ocr: bool = True, gpu: Optional[bool] = None):
        self.templates = CHAR_TEMPLATES
        self.use_deep_ocr = use_deep_ocr
        self.easyocr_reader = None
        
        if gpu is None:
            gpu = bool(torch.cuda.is_available())
        
        if use_deep_ocr:
            try:
                import easyocr
                # Optimize PyTorch CPU threading
                if not gpu:
                    try:
                        torch.set_num_threads(min(4, os.cpu_count() or 4))
                    except Exception:
                        pass
                self.easyocr_reader = easyocr.Reader(['en'], gpu=gpu, verbose=False)
                device_str = "CUDA GPU" if gpu else "CPU"
                print(f"Deep Learning OCR (EasyOCR PyTorch backend on {device_str}) initialized successfully.")
            except Exception as e:
                print(f"Notice: EasyOCR fallback to high-speed morphological matcher ({e})")
                self.easyocr_reader = None

    def extract_text_from_plate(self, plate_crop: np.ndarray) -> Tuple[str, float, str]:
        """
        Runs multi-stage high-speed OCR extraction on plate crop:
        1. Fast dimension filter (skips non-plate artifacts)
        2. Contrast variant preprocessing
        3. Deep Learning OCR with early-exit on confident Indian plate match
        4. Strict Indian HSRP grammar normalization
        5. High-speed morphological fallback
        """
        if plate_crop is None or plate_crop.size == 0:
            return "", 0.0, ""

        ph, pw = plate_crop.shape[:2]
        if ph < 12 or pw < 28:
            return "", 0.0, ""

        variants = get_ocr_variants(plate_crop)
        if not variants:
            variants = [plate_crop]

        best_plate = ""
        best_conf = 0.0
        best_raw = ""

        # Stage 1: Try Deep Learning OCR with early exit
        if self.easyocr_reader is not None:
            with torch.inference_mode():
                for img_var in variants:
                    try:
                        results = self.easyocr_reader.readtext(
                            img_var,
                            allowlist='0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ/-. ',
                            detail=1,
                            paragraph=False,
                            batch_size=1
                        )
                        if results:
                            raw_combined = " ".join([res[1] for res in results])
                            avg_conf = float(np.mean([res[2] for res in results]))
                            
                            norm_plate, format_conf = self.normalize_indian_plate(raw_combined)
                            if norm_plate:
                                final_conf = round(avg_conf * 0.45 + format_conf * 0.55, 2)
                                if final_conf > best_conf:
                                    best_plate = norm_plate
                                    best_conf = final_conf
                                    best_raw = raw_combined
                                
                                # Early exit: Stop immediately if high-confidence plate read
                                if final_conf >= 0.75:
                                    return best_plate, best_conf, best_raw
                    except Exception:
                        pass

            if best_plate and best_conf >= 0.50:
                return best_plate, best_conf, best_raw

        # Stage 2: Fallback to high-speed morphological template matcher
        morph_plate, morph_conf, morph_raw = self._extract_text_morphological(variants[0])
        if morph_plate and morph_conf > best_conf:
            return morph_plate, morph_conf, morph_raw

        return best_plate, best_conf, best_raw

    def _extract_text_morphological(self, plate_crop: np.ndarray) -> Tuple[str, float, str]:
        if plate_crop is None or plate_crop.size == 0:
            return "", 0.0, ""

        gray = cv2.cvtColor(plate_crop, cv2.COLOR_BGR2GRAY) if len(plate_crop.shape) == 3 else plate_crop
        _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

        h, w = thresh.shape[:2]
        ind_strip_boundary = int(w * 0.06)
        thresh[:, 0:ind_strip_boundary] = 0
        thresh[0:max(1, int(h * 0.05)), :] = 0
        thresh[int(h * 0.95):h, :] = 0

        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        char_boxes = []

        for c in contours:
            cx, cy, cw, ch_h = cv2.boundingRect(c)
            aspect = float(cw) / float(ch_h) if ch_h > 0 else 0
            height_ratio = float(ch_h) / float(h)
            area = cw * ch_h

            if cx >= ind_strip_boundary and 0.25 <= height_ratio <= 0.90 and (area >= 0.005 * w * h):
                if 0.15 <= aspect <= 1.20:
                    char_boxes.append((cx, cy, cw, ch_h))

        char_boxes = sorted(char_boxes, key=lambda b: b[0])
        if len(char_boxes) < 4:
            return "", 0.0, ""

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

            if best_score >= 0.45 and best_ch != "?":
                extracted_chars.append(best_ch)
                confidences.append(max(0.60, min(0.99, float(best_score))))

        raw_plate = "".join(extracted_chars)
        if len(raw_plate) < 6:
            return "", 0.0, raw_plate

        avg_conf = float(np.mean(confidences)) if confidences else 0.50
        normalized_plate, format_conf = self.normalize_indian_plate(raw_plate)
        if not normalized_plate:
            return "", 0.0, raw_plate

        final_conf = round(avg_conf * 0.5 + format_conf * 0.5, 2)
        return normalized_plate, final_conf, raw_plate

    def normalize_indian_plate(self, text: str) -> Tuple[str, float]:
        """
        Applies strict Indian HSRP registration grammar rules & positional error auto-correction:
        Standard: [State: 2 letters][District: 2 digits][Series: 0-3 letters][Number: 1-4 digits]
        e.g. 'MH 20EE 7601' -> 'MH20EE7601'
             'UK07BA7252'   -> 'UK07BA7252'
             'MH02 DS 9365' -> 'MH02DS9365'
             '22BH1234AA'   -> '22BH1234AA'
        """
        if not text:
            return "", 0.0

        raw = re.sub(r'[^A-Za-z0-9]', '', str(text)).upper()
        if len(raw) < 5:
            return "", 0.0

        # Check for BH series: [0-9]{2}BH[0-9]{4}[A-Z]{1,2}
        bh_match = re.search(r'(\d{2})BH(\d{4})([A-Z]{1,2})', raw)
        if bh_match:
            bh_plate = f"{bh_match.group(1)}BH{bh_match.group(2)}{bh_match.group(3)}"
            return bh_plate, 0.98

        # 1. State Code Identification
        state = None
        state_start = -1

        # Direct 2-letter state code match near start of string
        for st in INDIAN_STATE_CODES:
            pos = raw.find(st)
            if pos != -1 and pos <= 3:
                state = st
                state_start = pos
                break

        # Common state OCR confusion corrections (e.g. K4 -> KA, OL -> DL)
        if not state:
            for sc, target_st in STATE_CORRECTIONS.items():
                pos = raw.find(sc)
                if pos != -1 and pos <= 3:
                    state = target_st
                    state_start = pos
                    break

        # Infer state from first 2 characters if lookalikes exist
        if not state and len(raw) >= 6:
            c0 = DICT_INT_TO_CHAR.get(raw[0], raw[0]) if raw[0].isdigit() else raw[0]
            c1 = DICT_INT_TO_CHAR.get(raw[1], raw[1]) if raw[1].isdigit() else raw[1]
            inferred = c0 + c1
            if inferred in INDIAN_STATE_CODES:
                state = inferred
                state_start = 0
            elif inferred in STATE_CORRECTIONS:
                state = STATE_CORRECTIONS[inferred]
                state_start = 0

        if not state:
            # Fallback simple normalization for international / atypical plates
            if 6 <= len(raw) <= 12:
                return raw, 0.65
            return "", 0.0

        remainder = raw[state_start + 2:]
        if len(remainder) < 3:
            return "", 0.0

        # 2. Extract trailing registration digits from the RIGHT (end of string)
        trailing_digits = ""
        rem_idx = len(remainder) - 1
        while rem_idx >= 0 and len(trailing_digits) < 4:
            c = remainder[rem_idx]
            if c.isdigit():
                trailing_digits = c + trailing_digits
            elif c in DICT_CHAR_TO_INT and len(trailing_digits) > 0:
                trailing_digits = DICT_CHAR_TO_INT[c] + trailing_digits
            else:
                break
            rem_idx -= 1

        mid = remainder[:rem_idx + 1] if rem_idx >= 0 else ""

        # 3. Extract district digits from start of mid
        dist_digits = ""
        mid_idx = 0
        while mid_idx < len(mid) and len(dist_digits) < 2:
            c = mid[mid_idx]
            if c.isdigit():
                dist_digits += c
            elif c in DICT_CHAR_TO_INT and len(dist_digits) < 2 and len(mid) > 2:
                dist_digits += DICT_CHAR_TO_INT[c]
            else:
                break
            mid_idx += 1

        if not dist_digits and trailing_digits and len(trailing_digits) > 4:
            dist_digits = trailing_digits[:2]
            trailing_digits = trailing_digits[2:]

        if len(dist_digits) == 1:
            dist_digits = "0" + dist_digits
        elif len(dist_digits) == 0:
            dist_digits = "01"

        # 4. Extract series letters (letters between district code and trailing digits)
        series_part = mid[mid_idx:]
        series_letters = ""
        for c in series_part:
            if c.isalpha():
                series_letters += c
            elif c.isdigit() and c in DICT_INT_TO_CHAR and len(series_letters) < 3:
                series_letters += DICT_INT_TO_CHAR[c]

        # Ensure trailing digits is padded if 1-3 digits
        if not trailing_digits:
            all_digits = re.findall(r'\d+', remainder)
            if all_digits:
                trailing_digits = all_digits[-1][-4:]

        if trailing_digits:
            if len(trailing_digits) < 4:
                trailing_digits = trailing_digits.zfill(4)
            normalized = f"{state}{dist_digits}{series_letters}{trailing_digits}"
            std_pattern = r'^[A-Z]{2}[0-9]{2}[A-Z]{0,3}[0-9]{4}$'
            if re.match(std_pattern, normalized):
                conf = 0.95 if state in INDIAN_STATE_CODES else 0.85
                return normalized, conf
            return normalized, 0.80

        normalized = f"{state}{dist_digits}{series_letters}"
        return normalized, 0.70
