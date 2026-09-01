import cv2
import os
import sys
sys.path.insert(0, os.path.abspath("."))
import glob
import json
from ai_pipeline.detector import VehicleDetector
from ai_pipeline.ocr_engine import PlateOCREngine

det = VehicleDetector()
ocr = PlateOCREngine(use_deep_ocr=False)

videos = glob.glob('frontend/public/videos/*.mp4')
print('Found videos:', videos)

results = {}

for v in sorted(videos):
    cap = cv2.VideoCapture(v)
    fps = cap.get(cv2.CAP_PROP_FPS) or 25
    count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration = count / fps if fps > 0 else 0
    print(f"\nVideo: {v}, fps: {fps}, total frames: {count}, duration: {duration:.1f}s")
    
    # Process video every 0.5s or 1s
    video_events = []
    t = 0.0
    while t < duration:
        cap.set(cv2.CAP_PROP_POS_FRAMES, int(t * fps))
        ret, frame = cap.read()
        if not ret:
            break
        h, w = frame.shape[:2]
        dets = det.detect_vehicles(frame, conf_threshold=0.30)
        frame_detections = []
        for d in dets:
            bx1, by1, bx2, by2 = d["vehicle_bbox"]
            bw = bx2 - bx1
            bh = by2 - by1
            
            # Filter negligible bounding boxes (< 5% of screen)
            if bw < w * 0.05 or bh < h * 0.05:
                continue
                
            plate_str = None
            raw_ocr = ""
            conf = d["confidence"]
            
            if d.get("plate_crop") is not None and d["plate_crop"].size > 0:
                plate_str, ocr_c, raw_ocr = ocr.extract_text_from_plate(d["plate_crop"])
                if ocr_c > 0:
                    conf = max(conf, ocr_c)
                    
            frame_detections.append({
                "time": round(t, 2),
                "bbox": [bx1, by1, bx2, by2],
                "top": f"{round((by1/h)*100, 1)}%",
                "left": f"{round((bx1/w)*100, 1)}%",
                "width": f"{round((bw/w)*100, 1)}%",
                "height": f"{round((bh/h)*100, 1)}%",
                "vehicle_type": d["vehicle_type"],
                "vehicle_color": d["vehicle_color"],
                "confidence": round(conf, 2),
                "ocr_plate": plate_str or raw_ocr or None
            })
        if frame_detections:
            video_events.append({
                "time": round(t, 2),
                "detections": frame_detections
            })
        t += 0.5
    cap.release()
    results[os.path.basename(v)] = {
        "duration": round(duration, 2),
        "events": video_events
    }
    print(f"  Captured {len(video_events)} time points with vehicle detections.")

with open("scratch/detected_all_videos.json", "w") as f:
    json.dump(results, f, indent=2)
print("Saved all detections to scratch/detected_all_videos.json")
