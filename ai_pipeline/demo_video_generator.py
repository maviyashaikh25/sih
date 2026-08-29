import os
import sys
sys.path.insert(0, os.path.abspath("."))
import cv2
import numpy as np
import random
from ai_pipeline.test_pipeline import generate_synthetic_plate_image

def generate_sample_cctv_video(output_path: str = "data/sample_cctv_feed.mp4", num_frames: int = 150):
    """
    Generates a realistic CCTV traffic camera video clip containing moving vehicles,
    license plates (including the blacklisted DL01AB1234 vehicle), and roadside perspective.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    width, height = 960, 540
    fps = 25
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    writer = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

    # Pre-render 3 vehicle plates
    plates = [
        ("DL01AB1234", (30, 30, 30), "Black SUV"),       # Hotlist Scorpio
        ("HR26DQ9988", (230, 230, 230), "White Creta"),   # Hotlist Creta
        ("DL03CC8899", (180, 180, 180), "Silver Sedan"),  # Normal Car
    ]

    print(f"Generating synthetic CCTV video feed at {output_path} ({num_frames} frames)...")

    # Simulation vehicle trajectories across the camera view
    vehicles = [
        {"plate": "DL01AB1234", "color": (25, 25, 25), "type": "SUV", "start_frame": 10, "start_x": -180, "speed_x": 7, "y": 280, "w": 180, "h": 110},
        {"plate": "DL03CC8899", "color": (160, 160, 160), "type": "Car", "start_frame": 40, "start_x": -160, "speed_x": 6, "y": 380, "w": 160, "h": 95},
        {"plate": "HR26DQ9988", "color": (240, 240, 240), "type": "SUV", "start_frame": 85, "start_x": -190, "speed_x": 8, "y": 260, "w": 190, "h": 115},
    ]

    plate_cache = {}
    for p_text, _, _ in plates:
        p_img = generate_synthetic_plate_image(p_text, angle_deg=0.0, add_noise=False, darken=False)
        plate_cache[p_text] = p_img

    for f_idx in range(num_frames):
        # 1. Background Road Canvas (Asphalt grey + Road lane markings)
        frame = np.ones((height, width, 3), dtype="uint8") * 55
        
        # Road lane markings
        cv2.line(frame, (0, int(height * 0.45)), (width, int(height * 0.45)), (80, 80, 80), 2)
        for lx in range(0, width, 60):
            dash_x = (lx - (f_idx * 4)) % width
            cv2.line(frame, (dash_x, int(height * 0.68)), (dash_x + 30, int(height * 0.68)), (220, 220, 220), 3)

        # CCTV timestamp and camera watermark
        cv2.putText(frame, "CAM_CP_01 - CONNAUGHT PLACE RADIAL 1 [LIVE 4K]", (20, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 255, 255), 2)
        cv2.putText(frame, f"REC [●] 2026-08-29 16:45:{f_idx//25:02d}.{f_idx%25:02d}", (20, 65), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1)

        # 2. Render moving vehicles
        for v in vehicles:
            if f_idx >= v["start_frame"]:
                cur_x = v["start_x"] + (f_idx - v["start_frame"]) * v["speed_x"]
                if -200 <= cur_x <= width + 200:
                    vx, vy, vw, vh = cur_x, v["y"], v["w"], v["h"]
                    # Draw vehicle body
                    cv2.rectangle(frame, (vx, vy), (vx + vw, vy + vh), v["color"], -1)
                    cv2.rectangle(frame, (vx, vy), (vx + vw, vy + vh), (10, 10, 10), 2)
                    
                    # Vehicle windshield / cabin
                    cv2.rectangle(frame, (vx + 25, vy + 10), (vx + vw - 25, vy + int(vh * 0.5)), (40, 40, 40), -1)

                    # Mount license plate on lower bumper
                    p_img = plate_cache[v["plate"]]
                    pw, ph = int(vw * 0.45), int(vh * 0.25)
                    p_resized = cv2.resize(p_img, (pw, ph))
                    
                    px1 = vx + int((vw - pw) / 2)
                    py1 = vy + int(vh * 0.65)
                    
                    if 0 <= px1 and (px1 + pw) <= width and 0 <= py1 and (py1 + ph) <= height:
                        frame[py1:py1+ph, px1:px1+pw] = p_resized

        writer.write(frame)

    writer.release()
    print(f"Successfully generated sample CCTV video at {output_path}")

if __name__ == "__main__":
    generate_sample_cctv_video()
