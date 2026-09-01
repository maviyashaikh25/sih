import cv2
import numpy as np

def pad_and_resize(crop, target_size=(36, 48)):
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

def generate_exact_templates() -> dict[str, np.ndarray]:
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
        # Apply same padding normalization
        thresh = canvas.copy()
        c_box = cv2.boundingRect(thresh)
        if c_box[2] > 0 and c_box[3] > 0:
            char_crop = thresh[c_box[1]:c_box[1]+c_box[3], c_box[0]:c_box[0]+c_box[2]]
            templates[ch] = pad_and_resize(char_crop, (tw, th))
        else:
            templates[ch] = canvas
    return templates

TEMPLATES = generate_exact_templates()

def read_plate(img_path: str):
    img = cv2.imread(img_path)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY_INV)
    
    h, w = thresh.shape[:2]
    thresh[:, 0:int(w*0.10)] = 0
    thresh[0:int(h*0.05), :] = 0
    thresh[int(h*0.95):h, :] = 0
    
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    boxes = []
    for c in contours:
        cx, cy, cw, ch_h = cv2.boundingRect(c)
        aspect = float(cw) / float(ch_h)
        height_ratio = float(ch_h) / float(h)
        if 0.18 <= height_ratio <= 0.90 and 0.10 <= aspect <= 1.5:
            boxes.append((cx, cy, cw, ch_h))
            
    boxes = sorted(boxes, key=lambda b: b[0])
    
    extracted = []
    for cx, cy, cw, ch_h in boxes:
        crop = thresh[cy:cy+ch_h, cx:cx+cw]
        normalized_char = pad_and_resize(crop, (36, 48))
        
        best_score = -1
        best_ch = "?"
        for ch, t in TEMPLATES.items():
            # Normalized correlation coefficient
            score = cv2.matchTemplate(normalized_char, t, cv2.TM_CCOEFF_NORMED)[0][0]
            if score > best_score:
                best_score = score
                best_ch = ch
        extracted.append(best_ch)
    
    return "".join(extracted)

print("Reading scratch/debug_input.png...")
res = read_plate("scratch/debug_input.png")
print(f"Decoded: '{res}'")
