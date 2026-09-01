import cv2
import os
import sys
sys.path.insert(0, os.path.abspath("."))
import json
from ai_pipeline.detector import VehicleDetector
from ai_pipeline.ocr_engine import PlateOCREngine

det = VehicleDetector()
ocr = PlateOCREngine(use_deep_ocr=False)

videos = {
    'CAM_KG_01': 'frontend/public/videos/cam_6.mp4',
    'CAM_CP_01': 'frontend/public/videos/cam_1.mp4',
    'CAM_IG_01': 'frontend/public/videos/cam_3.mp4',
    'CAM_AIIMS_01': 'frontend/public/videos/cam_5.mp4',
    'CAM_CP_02': 'frontend/public/videos/cam_2.mp4',
    'CAM_ITO_01': 'frontend/public/videos/cam_4.mp4',
    'CAM_HK_01': 'frontend/public/videos/cam_7.mp4',
    'CAM_NP_01': 'frontend/public/videos/cam_8.mp4',
}

results = {}

for cam_id, vpath in videos.items():
    if not os.path.exists(vpath):
        continue
    cap = cv2.VideoCapture(vpath)
    fps = cap.get(cv2.CAP_PROP_FPS) or 25
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration = total_frames / fps
    print(f"Processing {cam_id} ({vpath}) - {duration:.1f}s ...", flush=True)
    
    keyframes = []
    # Sample every 1.0s up to 15s
    t = 0.0
    while t < min(15.0, duration):
        fno = int(t * fps)
        cap.set(cv2.CAP_PROP_POS_FRAMES, fno)
        ret, frame = cap.read()
        if not ret:
            break
        h, w = frame.shape[:2]
        detected = det.detect_vehicles(frame, conf_threshold=0.30)
        
        frame_items = []
        for r in detected:
            bx1, by1, bx2, by2 = r['vehicle_bbox']
            bw = bx2 - bx1
            bh = by2 - by1
            
            if bw < w * 0.06 or bh < h * 0.06:
                continue
                
            left_pct = round((bx1 / w) * 100, 1)
            top_pct = round((by1 / h) * 100, 1)
            width_pct = round((bw / w) * 100, 1)
            height_pct = round((bh / h) * 100, 1)
            
            # Check OCR on plate crop if available
            plate_str = None
            if r.get('plate_crop') is not None and r['plate_crop'].size > 0:
                plate_str, ocr_c, _ = ocr.extract_text_from_plate(r['plate_crop'])
            
            frame_items.append({
                "vehicle_type": r['vehicle_type'],
                "vehicle_color": r['vehicle_color'],
                "conf": r['confidence'],
                "top": f"{top_pct}%",
                "left": f"{left_pct}%",
                "width": f"{width_pct}%",
                "height": f"{height_pct}%",
                "extracted_plate": plate_str
            })
            
        keyframes.append({
            "time": round(t, 1),
            "vehicles": frame_items
        })
        t += 1.0
        
    cap.release()
    results[cam_id] = {
        "duration": round(duration, 1),
        "keyframes": keyframes
    }
    print(f"  {cam_id}: {len(keyframes)} keyframes extracted.", flush=True)

with open("scratch/quick_detections.json", "w") as f:
    json.dump(results, f, indent=2)
print("Saved to scratch/quick_detections.json", flush=True)
