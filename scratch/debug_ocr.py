import sys
import os
sys.path.insert(0, os.path.abspath("."))
import cv2
import numpy as np
from ai_pipeline.test_pipeline import generate_synthetic_plate_image
from ai_pipeline.preprocessing import prepare_plate_for_ocr

img = generate_synthetic_plate_image("DL01AB1234", angle_deg=0.0, add_noise=False, darken=False)
cv2.imwrite("scratch/debug_input.png", img)

processed = prepare_plate_for_ocr(img)
cv2.imwrite("scratch/debug_processed.png", processed)

gray = cv2.cvtColor(processed, cv2.COLOR_BGR2GRAY) if len(processed.shape) == 3 else processed
_, thresh = cv2.threshold(gray, 120, 255, cv2.THRESH_BINARY_INV)
cv2.imwrite("scratch/debug_thresh.png", thresh)

h, w = thresh.shape[:2]
left_margin = int(w * 0.12)
thresh[:, 0:left_margin] = 0
thresh[0:int(h*0.05), :] = 0
thresh[int(h*0.95):h, :] = 0
cv2.imwrite("scratch/debug_thresh_clean.png", thresh)

contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
print(f"Total contours: {len(contours)}")
boxes = []
for c in contours:
    cx, cy, cw, ch_h = cv2.boundingRect(c)
    aspect = float(cw) / float(ch_h)
    height_ratio = float(ch_h) / float(h)
    print(f"  Contour at ({cx},{cy}), size ({cw}x{ch_h}), aspect={aspect:.2f}, height_ratio={height_ratio:.2f}")
    if 0.25 <= height_ratio <= 0.90 and 0.10 <= aspect <= 1.2:
        boxes.append((cx, cy, cw, ch_h))

print(f"Filtered character boxes: {len(boxes)}")
