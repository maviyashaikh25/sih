import sys
import os
sys.path.insert(0, os.path.abspath("."))
import cv2
import numpy as np
from ai_pipeline.ocr_engine import CHAR_TEMPLATES

img = cv2.imread("scratch/debug_thresh_clean.png", cv2.IMREAD_GRAYSCALE)
contours, _ = cv2.findContours(img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
boxes = []
for c in contours:
    cx, cy, cw, ch_h = cv2.boundingRect(c)
    aspect = float(cw) / float(ch_h)
    height_ratio = float(ch_h) / float(img.shape[0])
    if 0.20 <= height_ratio <= 0.90 and 0.10 <= aspect <= 1.25:
        boxes.append((cx, cy, cw, ch_h))

boxes = sorted(boxes, key=lambda b: b[0])
print(f"Sorted boxes: {len(boxes)}")

read_chars = []
tw, th = 24, 36
for cx, cy, cw, ch_h in boxes:
    crop = img[cy:cy+ch_h, cx:cx+cw]
    resized = cv2.resize(crop, (tw, th))
    
    scores = []
    for ch, t in CHAR_TEMPLATES.items():
        score = cv2.matchTemplate(resized, t, cv2.TM_CCORR_NORMED)[0][0]
        scores.append((ch, score))
    
    scores = sorted(scores, key=lambda x: x[1], reverse=True)
    best_ch, best_s = scores[0]
    print(f"Box at x={cx}: Best match = '{best_ch}' (score={best_s:.2f}), Top 3: {scores[:3]}")
    read_chars.append(best_ch)

print(f"Full string read: {''.join(read_chars)}")
