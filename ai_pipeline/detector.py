import os
import cv2
import torch
import numpy as np
from typing import List, Tuple, Optional
from ultralytics import YOLO

# COCO vehicle class IDs in YOLO
VEHICLE_CLASSES = {
    2: "Car",
    3: "Motorcycle",
    5: "Bus",
    7: "Truck"
}

COLOR_RANGES = {
    "Red": [((0, 70, 50), (10, 255, 255)), ((170, 70, 50), (180, 255, 255))],
    "Blue": [((100, 60, 50), (130, 255, 255))],
    "Yellow": [((20, 100, 100), (35, 255, 255))],
    "Green": [((40, 50, 50), (85, 255, 255))],
    "White": [((0, 0, 180), (180, 40, 255))],
    "Black": [((0, 0, 0), (180, 255, 45))],
    "Grey": [((0, 0, 50), (180, 50, 180))],
    "Silver": [((0, 0, 150), (180, 30, 220))]
}

class VehicleDetector:
    """
    Cascaded Deep Learning Vehicle and License Plate Detector.
    Uses YOLOv8 for vehicle classification & localization, and fine-tuned YOLOv8-Plate model
    (or adaptive morphological localization) for precise plate bounding boxes.
    """
    def __init__(self, vehicle_model_name: str = "yolov8n.pt", plate_model_name: str = "ai_pipeline/best_plate_yolov8.pt"):
        print(f"Loading YOLO Vehicle Detector ({vehicle_model_name})...")
        self.vehicle_model = YOLO(vehicle_model_name)
        
        self.plate_model = None
        # Check primary and fallback locations for fine-tuned plate detector weights
        candidate_paths = [
            plate_model_name,
            os.path.join(os.path.dirname(__file__), "best_plate_yolov8.pt"),
            os.path.abspath("ai_pipeline/best_plate_yolov8.pt"),
            os.path.abspath("weights/best_plate_yolov8.pt"),
            os.path.join("weights", "best_plate_yolov8.pt"),
            os.path.join("runs", "detect", "plate_model_training", "weights", "best.pt"),
            os.path.join("runs", "detect", "runs", "detect", "plate_model_training", "weights", "best.pt")
        ]
        
        for candidate in candidate_paths:
            if candidate and os.path.exists(candidate):
                try:
                    print(f"Loading fine-tuned License Plate Model ({candidate})...")
                    self.plate_model = YOLO(candidate)
                    break
                except Exception as e:
                    print(f"Notice: Could not load plate model from {candidate} ({e}).")

        if self.plate_model is None:
            print("Notice: No trained plate model found. Operating with heuristic/morphological plate ROI detector.")

    def detect_vehicles(self, frame: np.ndarray, conf_threshold: float = 0.30) -> List[dict]:
        """
        Runs cascaded YOLO object detection:
        1. Localizes vehicles in the frame (Car, Bus, Truck, Motorcycle)
        2. Detects license plates across the whole frame & within vehicle crops
        3. Fuses bounding boxes and extracts high-resolution plate crops
        """
        h, w = frame.shape[:2]
        with torch.inference_mode():
            v_results = self.vehicle_model(frame, verbose=False, conf=conf_threshold, imgsz=640)[0]
        
        # Frame-level license plate detections
        frame_plates = []
        if self.plate_model is not None:
            try:
                with torch.inference_mode():
                    p_results = self.plate_model(frame, verbose=False, conf=0.18, imgsz=640)[0]
                for pbox in p_results.boxes:
                    px1, py1, px2, py2 = map(int, pbox.xyxy[0].tolist())
                    pconf = float(pbox.conf[0].item())
                    px1, py1 = max(0, px1), max(0, py1)
                    px2, py2 = min(w, px2), min(h, py2)
                    if px2 > px1 and py2 > py1:
                        frame_plates.append({
                            "bbox": (px1, py1, px2, py2),
                            "conf": pconf,
                            "crop": frame[py1:py2, px1:px2]
                        })
            except Exception:
                pass

        detections = []
        assigned_plates = set()

        for box in v_results.boxes:
            cls_id = int(box.cls[0].item())
            if cls_id in VEHICLE_CLASSES:
                x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
                conf = float(box.conf[0].item())
                vehicle_type = VEHICLE_CLASSES[cls_id]

                x1, y1 = max(0, x1), max(0, y1)
                x2, y2 = min(w, x2), min(h, y2)
                veh_crop = frame[y1:y2, x1:x2]
                veh_color = self.estimate_vehicle_color(veh_crop) if veh_crop.size > 0 else "Unknown"

                # Check if any frame-level plate is inside or close to this vehicle bbox
                matched_plate_bbox = None
                matched_plate_crop = None
                
                for idx, fp in enumerate(frame_plates):
                    if idx in assigned_plates:
                        continue
                    fpx1, fpy1, fpx2, fpy2 = fp["bbox"]
                    # Plate center
                    pcx, pcy = (fpx1 + fpx2) / 2.0, (fpy1 + fpy2) / 2.0
                    # Check if plate center is inside vehicle bbox (with slight margin)
                    if (x1 - 10) <= pcx <= (x2 + 10) and (y1 - 10) <= pcy <= (y2 + 10):
                        matched_plate_bbox = (fpx1, fpy1, fpx2, fpy2)
                        matched_plate_crop = fp["crop"]
                        assigned_plates.add(idx)
                        break

                # If no frame-level plate match, locate ROI within vehicle crop
                if matched_plate_crop is None or matched_plate_crop.size == 0:
                    crop_plate_box, crop_plate_img = self.locate_plate_roi(veh_crop)
                    if crop_plate_box and crop_plate_img is not None and crop_plate_img.size > 0:
                        matched_plate_bbox = (
                            x1 + crop_plate_box[0], y1 + crop_plate_box[1],
                            x1 + crop_plate_box[2], y1 + crop_plate_box[3]
                        )
                        matched_plate_crop = crop_plate_img

                detections.append({
                    "vehicle_bbox": (x1, y1, x2, y2),
                    "vehicle_type": vehicle_type,
                    "vehicle_color": veh_color,
                    "confidence": round(conf, 2),
                    "plate_bbox_in_frame": matched_plate_bbox,
                    "plate_crop": matched_plate_crop
                })

        return detections

    def locate_plate_roi(self, vehicle_crop: np.ndarray) -> Tuple[Optional[Tuple[int, int, int, int]], Optional[np.ndarray]]:
        """
        Locates the license plate candidate region within the vehicle bounding box crop.
        If a fine-tuned deep learning plate model is loaded, runs YOLO inference on the vehicle crop.
        Otherwise, applies morphological edge filtering and aspect ratio heuristics.
        """
        if vehicle_crop is None or vehicle_crop.size == 0:
            return None, None

        vh, vw = vehicle_crop.shape[:2]
        if vh < 25 or vw < 35:
            return None, None

        # 1. Try Deep Learning Plate Detector on vehicle crop
        if self.plate_model is not None:
            try:
                p_res = self.plate_model(vehicle_crop, verbose=False, conf=0.18)[0]
                if len(p_res.boxes) > 0:
                    best_p_box = max(p_res.boxes, key=lambda b: float(b.conf[0].item()))
                    px1, py1, px2, py2 = map(int, best_p_box.xyxy[0].tolist())
                    px1, py1 = max(0, px1), max(0, py1)
                    px2, py2 = min(vw, px2), min(vh, py2)
                    plate_crop = vehicle_crop[py1:py2, px1:px2]
                    if plate_crop.size > 0:
                        return (px1, py1, px2, py2), plate_crop
            except Exception:
                pass

        # 2. Morphological Edge & Gradient Localization (Fallback)
        lower_y = int(vh * 0.45)
        roi_h_end = int(vh * 0.95)
        roi_w_start = int(vw * 0.10)
        roi_w_end = int(vw * 0.90)
        
        roi = vehicle_crop[lower_y:roi_h_end, roi_w_start:roi_w_end]
        roi_h, roi_w = roi.shape[:2]

        if roi_h < 15 or roi_w < 30:
            return None, None

        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        
        # High-pass filter & Morphological Tophat to emphasize text / plate edges
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (17, 5))
        morph = cv2.morphologyEx(gray, cv2.MORPH_TOPHAT, kernel)

        sobelx = cv2.Sobel(morph, cv2.CV_8U, 1, 0, ksize=3)
        sobelx = cv2.GaussianBlur(sobelx, (5, 5), 0)
        _, thresh = cv2.threshold(sobelx, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        close_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (21, 5))
        closed = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, close_kernel)

        contours, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        contours = sorted(contours, key=cv2.contourArea, reverse=True)

        best_box = None
        best_crop = None

        for c in contours:
            x, y, w, h = cv2.boundingRect(c)
            aspect_ratio = float(w) / float(h) if h > 0 else 0
            area = w * h
            
            # Plate typically has aspect ratio between 2.2 and 5.5 and takes 2% to 35% of the ROI
            if 2.2 <= aspect_ratio <= 5.8 and (0.02 * roi_w * roi_h) <= area <= (0.35 * roi_w * roi_h):
                pad_x = int(w * 0.10)
                pad_y = int(h * 0.15)
                
                px1 = max(0, roi_w_start + x - pad_x)
                py1 = max(0, lower_y + y - pad_y)
                px2 = min(vw, roi_w_start + x + w + pad_x)
                py2 = min(vh, lower_y + y + h + pad_y)

                best_box = (px1, py1, px2, py2)
                best_crop = vehicle_crop[py1:py2, px1:px2]
                break

        # Fallback: Extract standard lower-center bumper window where license plates reside
        if best_crop is None or best_crop.size == 0:
            bw_w = int(vw * 0.65)
            bw_h = int(vh * 0.35)
            bx1 = int((vw - bw_w) / 2)
            by1 = int(vh * 0.52)
            bx2 = bx1 + bw_w
            by2 = min(vh, by1 + bw_h)
            best_box = (bx1, by1, bx2, by2)
            best_crop = vehicle_crop[by1:by2, bx1:bx2]

        return best_box, best_crop

    def estimate_vehicle_color(self, vehicle_crop: np.ndarray) -> str:
        """Estimates dominant color of vehicle using HSV histogram matching."""
        if vehicle_crop is None or vehicle_crop.size == 0:
            return "Unknown"

        vh, vw = vehicle_crop.shape[:2]
        center_crop = vehicle_crop[int(vh*0.25):int(vh*0.75), int(vw*0.25):int(vw*0.75)]
        if center_crop.size == 0:
            center_crop = vehicle_crop

        hsv = cv2.cvtColor(center_crop, cv2.COLOR_BGR2HSV)
        max_score = 0
        dominant_color = "Silver"

        for color_name, ranges in COLOR_RANGES.items():
            mask = np.zeros(hsv.shape[:2], dtype="uint8")
            for lower, upper in ranges:
                m = cv2.inRange(hsv, np.array(lower, dtype="uint8"), np.array(upper, dtype="uint8"))
                mask = cv2.bitwise_or(mask, m)
            score = cv2.countNonZero(mask)
            if score > max_score:
                max_score = score
                dominant_color = color_name

        return dominant_color
