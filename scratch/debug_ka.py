import sys
import os
sys.path.insert(0, os.path.abspath("."))
import cv2
import numpy as np
from ai_pipeline.test_pipeline import generate_synthetic_plate_image

img = generate_synthetic_plate_image("KA05MJ9876", angle_deg=0.0, add_noise=False, darken=False)
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
_, thresh = cv2.threshold(gray, 140, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

h, w = thresh.shape[:2]
ind_strip_boundary = int(w * 0.08)
thresh[:, 0:ind_strip_boundary] = 0
thresh[0:max(1, int(h * 0.05)), :] = 0
thresh[int(h * 0.95):h, :] = 0

contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
boxes = []
for c in contours:
    cx, cy, cw, ch_h = cv2.boundingRect(c)
    aspect = float(cw) / float(ch_h)
    height_ratio = float(ch_h) / float(h)
    print(f"Contour at x={cx}, y={cy}, w={cw}, h={ch_h}, aspect={aspect:.2f}, height_ratio={height_ratio:.2f}")
    if cx >= ind_strip_boundary and 0.16 <= height_ratio <= 0.92 and 0.08 <= aspect <= 1.6:
        boxes.append((cx, cy, cw, ch_h))

print(f"Total accepted boxes: {len(boxes)}")
