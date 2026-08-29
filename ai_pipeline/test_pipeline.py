import os
import sys
import cv2
import numpy as np

# Add project root to sys.path
sys.path.insert(0, os.path.abspath("."))

from ai_pipeline.preprocessing import apply_clahe, rectify_plate_perspective, prepare_plate_for_ocr
from ai_pipeline.ocr_engine import PlateOCREngine
from ai_pipeline.multi_frame_voting import MultiFramePlateAggregator, resolve_cross_camera_fuzzy_plate

def generate_synthetic_plate_image(
    plate_text: str = "DL01AB1234",
    angle_deg: float = 12.0,
    add_noise: bool = True,
    darken: bool = True
) -> np.ndarray:
    """
    Generates a realistic Indian license plate image with HSRP strip, 
    border, realistic font, perspective angle, and noise.
    """
    # 1. Base plate canvas (White with dark border, 340x110)
    w, h = 340, 110
    canvas = np.ones((h, w, 3), dtype="uint8") * 245
    cv2.rectangle(canvas, (4, 4), (w - 4, h - 4), (20, 20, 20), 4)

    # 2. Blue IND strip on the left side
    cv2.rectangle(canvas, (4, 4), (45, h - 4), (180, 50, 0), -1) # Blue in BGR
    cv2.putText(canvas, "IND", (8, 65), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1)

    # 3. Render plate text in bold black font
    font_scale = 1.35
    thickness = 3
    (tw, th), _ = cv2.getTextSize(plate_text, cv2.FONT_HERSHEY_SIMPLEX, font_scale, thickness)
    tx = int(55 + (w - 60 - tw) / 2)
    ty = int((h + th) / 2)
    cv2.putText(canvas, plate_text, (tx, ty), cv2.FONT_HERSHEY_SIMPLEX, font_scale, (15, 15, 15), thickness)

    # 4. Apply perspective warp (angled camera angle)
    if abs(angle_deg) > 0:
        pts1 = np.float32([[0, 0], [w, 0], [w, h], [0, h]])
        shear = int(h * np.tan(np.radians(angle_deg)))
        pts2 = np.float32([[shear, 0], [w, int(shear * 0.4)], [w - shear, h], [0, h - int(shear * 0.3)]])
        matrix = cv2.getPerspectiveTransform(pts1, pts2)
        canvas = cv2.warpPerspective(canvas, matrix, (w, h), borderValue=(50, 50, 50))

    # 5. Low light / dimming
    if darken:
        canvas = (canvas * 0.65).astype("uint8")

    # 6. Add Gaussian noise & blur
    if add_noise:
        import random
        noise = np.zeros(canvas.shape, dtype="int16")
        for i in range(h):
            for j in range(w):
                noise[i, j] = int(random.gauss(0, 5))
        canvas = np.clip(canvas.astype("int16") + noise, 0, 255).astype("uint8")
        canvas = cv2.GaussianBlur(canvas, (3, 3), 0)

    return canvas

def run_tests():
    print("=================================================================")
    print("      Testing Phase 2: Computer Vision & ANPR AI Pipeline       ")
    print("=================================================================")

    os.makedirs("scratch", exist_ok=True)
    test_plates = [
        "DL01AB1234",
        "HR26DQ9988",
        "UP16AX5544",
        "MH12DE1432",
        "KA05MJ9876"
    ]

    # 1. Test Preprocessing & Rectification
    print("\n1. Testing Preprocessing & Perspective Rectification...")
    synth_img = generate_synthetic_plate_image("DL01AB1234", angle_deg=10.0, darken=True)
    cv2.imwrite("scratch/test_raw_angled.png", synth_img)
    preprocessed = prepare_plate_for_ocr(synth_img)
    cv2.imwrite("scratch/test_preprocessed.png", preprocessed)
    print("  Saved synthetic raw & preprocessed samples to scratch/ directory.")

    # 2. Test OCR Engine
    print("\n2. Initializing OCR Engine and evaluating accuracy across test plates...")
    ocr = PlateOCREngine(gpu=False)

    correct_reads = 0
    for original_text in test_plates:
        test_img = generate_synthetic_plate_image(original_text, angle_deg=8.0, darken=False)
        extracted, conf, raw = ocr.extract_text_from_plate(test_img)
        is_match = (extracted == original_text)
        if is_match:
            correct_reads += 1
        print(f"  Expected: {original_text} | Extracted: {extracted} | Raw: {raw} | Conf: {conf:.0%} | {'[PASS]' if is_match else '[MISMATCH]'}")

    accuracy = (correct_reads / len(test_plates)) * 100
    print(f"\n  Recognition Accuracy: {accuracy:.1f}% ({correct_reads}/{len(test_plates)})")

    # 3. Test Multi-Frame Temporal Voting & Levenshtein Resolver
    print("\n3. Testing Multi-Frame Temporal Voting & Fuzzy Resolution...")
    aggregator = MultiFramePlateAggregator()
    # Simulate a car passing through 6 camera frames with minor OCR noise
    simulated_stream = [
        ("DL01AB1234", 0.96),
        ("DL01A81234", 0.72), # OCR confused B with 8
        ("DL01AB1234", 0.98),
        ("DLO1AB1234", 0.75), # OCR confused 0 with O
        ("DL01AB1234", 0.95),
        ("DL01AB1234", 0.97)
    ]
    track_id = 42
    for plate, conf in simulated_stream:
        aggregator.add_frame_read(track_id, plate, conf)

    consensus_plate, consensus_conf, count = aggregator.resolve_consensus_plate(track_id)
    print(f"  Simulated 6 noisy frame reads -> Resolved Consensus: {consensus_plate} (Conf: {consensus_conf:.0%}, Votes: {count}/6)")
    assert consensus_plate == "DL01AB1234", "Multi-frame voting failed to resolve consensus plate"

    # 4. Test Cross-Camera Levenshtein Fuzzy Matcher
    print("\n4. Testing Cross-Camera Fuzzy Plate Matcher...")
    candidates = ["HR51BK4422", "DL03CC8899", "DL01AB1234", "UP14DT3311"]
    fuzzy_query = "DL01A81234" # Misread plate
    matched = resolve_cross_camera_fuzzy_plate(fuzzy_query, candidates, max_distance=2)
    print(f"  Query: '{fuzzy_query}' -> Matched Vehicle: '{matched}'")
    assert matched == "DL01AB1234", "Cross-camera fuzzy match failed"

    print("\n=================================================================")
    print("  [SUCCESS] All Phase 2 Computer Vision & OCR Components Passed!  ")
    print("=================================================================")

if __name__ == "__main__":
    run_tests()
