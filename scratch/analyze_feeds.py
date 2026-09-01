import cv2
import os
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
    'CAM_LP_01': 'frontend/public/videos/cam_6.mp4',
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
    print(f"=== {cam_id} ({vpath}): {total_frames} frames, {fps:.1f} fps, {duration:.1f}s ===")
    
    cam_keyframes = []
    # Sample every 0.5 sec up to duration or 20s
    sample_interval_sec = 0.5
    t = 0.0
    while t < min(25.0, duration):
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
            
            # Filter tiny background boxes
            if bw < w * 0.08 and bh < h * 0.08:
                continue
                
            left_pct = round((bx1 / w) * 100, 1)
            top_pct = round((by1 / h) * 100, 1)
            width_pct = round((bw / w) * 100, 1)
            height_pct = round((bh / h) * 100, 1)
            
            frame_items.append({
                "type": f"{r['vehicle_color']} {r['vehicle_type']}",
                "vehicle_type": r['vehicle_type'],
                "vehicle_color": r['vehicle_color'],
                "conf": r['confidence'],
                "left": f"{left_pct}%",
                "top": f"{top_pct}%",
                "width": f"{width_pct}%",
                "height": f"{height_pct}%",
            })
            
        cam_keyframes.append({
            "time": round(t, 2),
            "boxes": frame_items
        })
        t += sample_interval_sec
        
    cap.release()
    results[cam_id] = {
        "duration": round(duration, 2),
        "keyframes": cam_keyframes
    }
    print(f"  Processed {len(cam_keyframes)} keyframe steps for {cam_id}")

with open("scratch/video_detections.json", "w") as f:
    json.dump(results, f, indent=2)
print("Saved to scratch/video_detections.json")
