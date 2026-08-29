import os
import cv2
import time
import requests
import numpy as np
from datetime import datetime, timezone
from typing import Optional, Callable

from ai_pipeline.detector import VehicleDetector
from ai_pipeline.ocr_engine import PlateOCREngine
from ai_pipeline.multi_frame_voting import MultiFramePlateAggregator

class VideoStreamProcessor:
    def __init__(
        self,
        camera_id: str = "CAM_CP_01",
        api_base_url: str = "http://127.0.0.1:8000/api/v1",
        enable_api_post: bool = True
    ):
        self.camera_id = camera_id
        self.api_base_url = api_base_url
        self.enable_api_post = enable_api_post

        print(f"Initializing VideoStreamProcessor for {camera_id}...")
        self.detector = VehicleDetector()
        self.ocr_engine = PlateOCREngine()
        self.aggregator = MultiFramePlateAggregator()

    def process_frame(self, frame: np.ndarray, frame_idx: int = 0) -> tuple[np.ndarray, list[dict]]:
        """
        Processes a single video frame:
        1. Detects vehicles & colors
        2. Crops & rectifies license plate
        3. Runs OCR & normalizer
        4. Aggregates multi-frame vote
        5. Annotates bounding boxes & labels
        """
        annotated = frame.copy()
        detections = self.detector.detect_vehicles(frame)
        confirmed_detections = []

        for idx, det in enumerate(detections):
            vx1, vy1, vx2, vy2 = det["vehicle_bbox"]
            v_type = det["vehicle_type"]
            v_color = det["vehicle_color"]
            plate_crop = det["plate_crop"]

            # Draw vehicle bounding box (Cyan / Blue)
            cv2.rectangle(annotated, (vx1, vy1), (vx2, vy2), (255, 191, 0), 2)
            cv2.putText(
                annotated,
                f"{v_color} {v_type}",
                (vx1, max(20, vy1 - 8)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (255, 191, 0),
                2
            )

            # If plate crop found, run OCR
            if plate_crop is not None and plate_crop.size > 0:
                plate_text, conf, raw_text = self.ocr_engine.extract_text_from_plate(plate_crop)

                if plate_text and conf >= 0.60:
                    track_id = idx + 1 # Simple track identifier per vehicle slot
                    self.aggregator.add_frame_read(track_id, plate_text, conf)

                    resolved_result = self.aggregator.resolve_consensus_plate(track_id)
                    if resolved_result:
                        final_plate, final_conf, hit_count = resolved_result
                        
                        # Draw plate bounding box (Green)
                        if det["plate_bbox_in_frame"]:
                            px1, py1, px2, py2 = det["plate_bbox_in_frame"]
                            cv2.rectangle(annotated, (px1, py1), (px2, py2), (0, 255, 0), 2)
                        
                        # Draw plate text badge with dark background
                        badge_text = f"{final_plate} ({final_conf:.0%})"
                        (tw, th), _ = cv2.getTextSize(badge_text, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
                        badge_y1 = max(0, vy1 - 32)
                        cv2.rectangle(annotated, (vx1, badge_y1), (vx1 + tw + 10, badge_y1 + th + 10), (0, 0, 0), -1)
                        cv2.putText(
                            annotated,
                            badge_text,
                            (vx1 + 5, badge_y1 + th + 4),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.6,
                            (0, 255, 0),
                            2
                        )

                        detection_data = {
                            "camera_id": self.camera_id,
                            "plate_number": final_plate,
                            "raw_plate": raw_text or final_plate,
                            "confidence": final_conf,
                            "vehicle_type": v_type,
                            "vehicle_color": v_color,
                            "direction": "Northbound",
                            "speed_estimate_kmh": 46.0,
                            "timestamp": datetime.now(timezone.utc).isoformat()
                        }
                        confirmed_detections.append(detection_data)

                        # Send to backend API if enabled
                        if self.enable_api_post and frame_idx % 10 == 0:
                            self._send_to_backend(detection_data)

        return annotated, confirmed_detections

    def process_video_file(
        self,
        video_path: str,
        output_path: Optional[str] = None,
        max_frames: int = 200,
        display: bool = False
    ):
        """Processes a video file frame-by-frame."""
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video file {video_path} not found")

        cap = cv2.VideoCapture(video_path)
        fps = int(cap.get(cv2.CAP_PROP_FPS)) or 30
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        writer = None
        if output_path:
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            writer = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

        frame_count = 0
        total_detections = 0

        print(f"Starting video processing: {video_path} ({width}x{height} @ {fps}fps)")
        while cap.isOpened() and frame_count < max_frames:
            ret, frame = cap.read()
            if not ret:
                break

            frame_count += 1
            annotated_frame, detections = self.process_frame(frame, frame_idx=frame_count)
            total_detections += len(detections)

            if writer:
                writer.write(annotated_frame)

            if display:
                cv2.imshow("ANPR Live Processor", annotated_frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break

        cap.release()
        if writer:
            writer.release()
        if display:
            cv2.destroyAllWindows()

        print(f"Finished processing {frame_count} frames. Recorded {total_detections} plate detections.")

    def _send_to_backend(self, detection_data: dict):
        try:
            url = f"{self.api_base_url}/detections/ingest"
            requests.post(url, json=detection_data, timeout=1.0)
        except Exception:
            pass # Non-blocking if server is offline during offline testing
