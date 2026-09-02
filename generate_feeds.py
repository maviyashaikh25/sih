import os
import cv2
import numpy as np
from datetime import datetime, timedelta

def extract_car_rgba(image_path: str, spill_replace_color=(180, 180, 180)):
    """Extracts a car from green screen with alpha transparency and spill reduction."""
    img = cv2.imread(image_path)
    if img is None:
        raise FileNotFoundError(f"Could not load image: {image_path}")
    
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    lower_green = np.array([35, 40, 40])
    upper_green = np.array([88, 255, 255])
    
    mask = cv2.inRange(hsv, lower_green, upper_green)
    car_mask = cv2.bitwise_not(mask)
    
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    car_mask = cv2.morphologyEx(car_mask, cv2.MORPH_CLOSE, kernel)
    car_mask = cv2.GaussianBlur(car_mask, (3, 3), 0)
    
    coords = cv2.findNonZero(car_mask)
    if coords is None:
        return img, car_mask
        
    x, y, w, h = cv2.boundingRect(coords)
    car_cropped = img[y:y+h, x:x+w].copy()
    mask_cropped = car_mask[y:y+h, x:x+w]
    
    # Spill reduction on borders
    hsv_crop = cv2.cvtColor(car_cropped, cv2.COLOR_BGR2HSV)
    spill_mask = cv2.inRange(hsv_crop, lower_green, upper_green)
    car_cropped[spill_mask > 0] = spill_replace_color
    
    b, g, r = cv2.split(car_cropped)
    rgba = cv2.merge([b, g, r, mask_cropped])
    return rgba

def create_indian_license_plate(text="KA 05 MH 8899", width=140, height=36, is_yellow=True):
    """Creates a photorealistic Indian HSRP license plate with IND blue strip and bold characters."""
    plate = np.zeros((height, width, 3), dtype=np.uint8)
    
    # Background color: Commercial Yellow or Private White
    if is_yellow:
        plate[:] = (20, 215, 255) # BGR Yellow
    else:
        plate[:] = (248, 248, 248) # BGR White
        
    # Outer black border
    cv2.rectangle(plate, (0, 0), (width-1, height-1), (15, 15, 15), 2)
    
    # Left blue IND strip (High Security Registration Plate style)
    blue_width = int(width * 0.12)
    cv2.rectangle(plate, (2, 2), (blue_width, height-3), (160, 40, 20), -1)
    cv2.putText(plate, "IND", (4, height//2 + 3), cv2.FONT_HERSHEY_SIMPLEX, 0.28, (255, 255, 255), 1)
    
    # Registration Text
    text_x = blue_width + 6
    text_y = int(height * 0.72)
    font_scale = 0.55 * (height / 36.0)
    cv2.putText(plate, text, (text_x, text_y), cv2.FONT_HERSHEY_DUPLEX, font_scale, (10, 10, 10), 2, cv2.LINE_AA)
    
    return plate

def attach_plate_to_car(car_rgba, plate_text="KA 05 MH 8899", rel_pos=(0.04, 0.62), rel_size=(0.14, 0.085), is_yellow=True, angle=-2):
    """Attaches a license plate to the car RGBA sprite with correct position and tilt."""
    car_h, car_w, _ = car_rgba.shape
    pw = int(car_w * rel_size[0])
    ph = int(car_h * rel_size[1])
    
    plate_img = create_indian_license_plate(plate_text, width=pw, height=ph, is_yellow=is_yellow)
    
    if angle != 0:
        center = (pw // 2, ph // 2)
        M = cv2.getRotationMatrix2D(center, angle, 1.0)
        plate_img = cv2.warpAffine(plate_img, M, (pw, ph), borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0))
    
    px = int(car_w * rel_pos[0])
    py = int(car_h * rel_pos[1])
    
    car_bgr = car_rgba[:, :, :3].copy()
    car_alpha = car_rgba[:, :, 3].copy()
    
    # Composite plate onto car
    if 0 <= py and (py + ph) <= car_h and 0 <= px and (px + pw) <= car_w:
        car_bgr[py:py+ph, px:px+pw] = plate_img
        car_alpha[py:py+ph, px:px+pw] = 255
        
    b, g, r = cv2.split(car_bgr)
    return cv2.merge([b, g, r, car_alpha])

def overlay_car_on_background(bg, car_rgba, x, y, scale=1.0, flip_h=False, brightness=1.0, tint=(1.0, 1.0, 1.0), shadow=True):
    """Overlays the car sprite onto the background with soft contact shadow, scaling, and lighting."""
    bg_h, bg_w, _ = bg.shape
    car_h, car_w, _ = car_rgba.shape
    
    scaled_w = max(10, int(car_w * scale))
    scaled_h = max(10, int(car_h * scale))
    
    resized_car = cv2.resize(car_rgba, (scaled_w, scaled_h), interpolation=cv2.INTER_AREA)
    if flip_h:
        resized_car = cv2.flip(resized_car, 1)
        
    car_rgb = resized_car[:, :, :3].astype(np.float32)
    car_a = (resized_car[:, :, 3].astype(np.float32) / 255.0)[:, :, np.newaxis]
    
    # Lighting & tint adjustment (e.g. night amber tint or darkened)
    car_rgb[:, :, 0] *= (brightness * tint[0])
    car_rgb[:, :, 1] *= (brightness * tint[1])
    car_rgb[:, :, 2] *= (brightness * tint[2])
    car_rgb = np.clip(car_rgb, 0, 255)
    
    # Contact shadow under the car
    if shadow:
        shadow_w = int(scaled_w * 0.9)
        shadow_h = int(scaled_h * 0.25)
        shadow_x = x + int(scaled_w * 0.05)
        shadow_y = y + int(scaled_h * 0.82)
        
        sx1 = max(0, shadow_x)
        sy1 = max(0, shadow_y)
        sx2 = min(bg_w, shadow_x + shadow_w)
        sy2 = min(bg_h, shadow_y + shadow_h)
        
        if sx2 > sx1 and sy2 > sy1:
            shadow_patch = bg[sy1:sy2, sx1:sx2].astype(np.float32)
            bg[sy1:sy2, sx1:sx2] = np.clip(shadow_patch * 0.45, 0, 255).astype(np.uint8)
            
    # Calculate clipping boundaries
    x1, y1 = max(0, x), max(0, y)
    x2, y2 = min(bg_w, x + scaled_w), min(bg_h, y + scaled_h)
    
    if x2 <= x1 or y2 <= y1:
        return bg
        
    cx1 = x1 - x
    cy1 = y1 - y
    cx2 = cx1 + (x2 - x1)
    cy2 = cy1 + (y2 - y1)
    
    bg_roi = bg[y1:y2, x1:x2].astype(np.float32)
    car_roi = car_rgb[cy1:cy2, cx1:cx2]
    alpha_roi = car_a[cy1:cy2, cx1:cx2]
    
    blended = (car_roi * alpha_roi) + (bg_roi * (1.0 - alpha_roi))
    bg[y1:y2, x1:x2] = np.clip(blended, 0, 255).astype(np.uint8)
    return bg

def apply_rain_and_atmosphere(frame, intensity=0.3, is_night=False):
    """Renders authentic rain streaks, wet surface reflections, and atmospheric noise."""
    h, w, _ = frame.shape
    
    # Rain streak layer
    rain_layer = np.zeros((h, w), dtype=np.uint8)
    num_drops = int(2500 * intensity)
    
    drop_x = np.random.randint(0, w, num_drops)
    drop_y = np.random.randint(0, h, num_drops)
    drop_len = np.random.randint(12, 28, num_drops)
    
    for i in range(num_drops):
        cv2.line(rain_layer, 
                 (drop_x[i], drop_y[i]), 
                 (drop_x[i] + int(drop_len[i] * 0.25), drop_y[i] + drop_len[i]), 
                 200, 1)
                 
    rain_bgr = cv2.merge([rain_layer, rain_layer, rain_layer])
    frame = cv2.addWeighted(frame, 0.90, rain_bgr, 0.25, 0)
    
    # Camera sensor grain
    noise = np.random.normal(0, 3.5, (h, w, 3)).astype(np.float32)
    frame = np.clip(frame.astype(np.float32) + noise, 0, 255).astype(np.uint8)
    return frame

def draw_cctv_hud(frame, cam_id, location, coords, timestamp, is_live=True):
    """Draws realistic professional CCTV surveillance HUD header & footer overlay."""
    h, w, _ = frame.shape
    
    # Semi-transparent top HUD bar
    hud_bar = frame[0:55, 0:w].copy()
    overlay = np.zeros_like(hud_bar)
    cv2.rectangle(overlay, (0, 0), (w, 55), (10, 10, 15), -1)
    frame[0:55, 0:w] = cv2.addWeighted(hud_bar, 0.35, overlay, 0.65, 0)
    
    # REC blinking dot
    milli = timestamp.microsecond // 1000
    if milli < 650:
        cv2.circle(frame, (35, 27), 9, (0, 0, 230), -1)
        cv2.circle(frame, (35, 27), 4, (255, 255, 255), -1)
        
    cv2.putText(frame, "REC", (54, 34), cv2.FONT_HERSHEY_DUPLEX, 0.62, (240, 240, 240), 2)
    cv2.putText(frame, f"|  {cam_id}  -  {location}  [{coords}]", (110, 34), 
                cv2.FONT_HERSHEY_DUPLEX, 0.58, (220, 220, 220), 1, cv2.LINE_AA)
                
    time_str = timestamp.strftime("%Y-%m-%d  %H:%M:%S") + f".{milli:03d}"
    cv2.putText(frame, time_str, (w - 340, 34), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 255, 200), 2, cv2.LINE_AA)
                
    # Bottom HUD status
    cv2.putText(frame, "ANPR INTELLIGENCE SYSTEM // 1080p 30FPS // OPTICAL FLOW ACTIVE", 
                (30, h - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (180, 180, 180), 1, cv2.LINE_AA)
    return frame

def generate_realistic_feed(config, suv_sprite, sedan_sprite):
    filename = config['filename']
    cam_id = config['cam_id']
    location = config['location']
    coords = config['coords']
    start_time = config['start_time']
    time_of_day = config.get('time_of_day', 'day')
    weather = config.get('weather', 'clear')
    bg_path = config['bg_path']
    trajectory = config['trajectory']
    
    width, height = 1920, 1080
    fps = 30
    duration = 8  # 8 seconds = 240 frames
    total_frames = fps * duration
    
    # Load realistic background image
    base_bg = cv2.imread(bg_path)
    if base_bg is None:
        raise FileNotFoundError(f"Background image not found: {bg_path}")
    base_bg = cv2.resize(base_bg, (width, height))
    
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(filename, fourcc, fps, (width, height))
    
    print(f"Generating realistic CCTV feed: {filename} ({total_frames} frames)...")
    
    # Lighting profile
    brightness = 0.55 if time_of_day == 'night' else 1.0
    tint = (0.85, 0.95, 1.1) if time_of_day == 'night' else (1.0, 1.0, 1.0)
    
    # Trajectory points for target SUV
    p_start = trajectory['suv_start']
    p_end = trajectory['suv_end']
    scale_start = trajectory.get('suv_scale_start', 0.45)
    scale_end = trajectory.get('suv_scale_end', 0.55)
    
    # Trajectory for distractor sedan
    distractor = config.get('distractor', None)
    
    for f_idx in range(total_frames):
        frame = base_bg.copy()
        progress = f_idx / float(total_frames)
        
        # 1. Distractor Car (Red Sedan)
        if distractor:
            d_progress = (f_idx - distractor.get('start_frame', 0)) / float(total_frames)
            if 0.0 <= d_progress <= 1.2:
                dx = int(distractor['start_x'] + d_progress * (distractor['end_x'] - distractor['start_x']))
                dy = int(distractor['start_y'] + d_progress * (distractor['end_y'] - distractor['start_y']))
                d_scale = distractor.get('scale', 0.38)
                frame = overlay_car_on_background(
                    frame, sedan_sprite, dx, dy, 
                    scale=d_scale, flip_h=distractor.get('flip', False),
                    brightness=brightness, tint=tint, shadow=True
                )
                
        # 2. Target Car: Silver SUV with KA-05-MH-8899
        car_x = int(p_start[0] + progress * (p_end[0] - p_start[0]))
        car_y = int(p_start[1] + progress * (p_end[1] - p_start[1]))
        car_scale = scale_start + progress * (scale_end - scale_start)
        
        frame = overlay_car_on_background(
            frame, suv_sprite, car_x, car_y, 
            scale=car_scale, flip_h=trajectory.get('suv_flip', False),
            brightness=brightness, tint=tint, shadow=True
        )
        
        # 3. Environmental overlays (Rain / Night)
        if weather == 'rain':
            frame = apply_rain_and_atmosphere(frame, intensity=0.45, is_night=(time_of_day == 'night'))
            
        # 4. CCTV HUD
        curr_timestamp = start_time + timedelta(seconds=f_idx / fps)
        frame = draw_cctv_hud(frame, cam_id, location, coords, curr_timestamp)
        
        out.write(frame)
        
    out.release()
    print(f"[OK] Generated photorealistic CCTV video: {filename}")

def main():
    assets_dir = "data/realistic_assets"
    
    # 1. Prepare Vehicle Sprites with High-Resolution Indian License Plates
    raw_suv = extract_car_rgba(os.path.join(assets_dir, "car_silver_suv.jpg"))
    suv_with_plate = attach_plate_to_car(
        raw_suv, 
        plate_text="KA 05 MH 8899", 
        rel_pos=(0.045, 0.62), 
        rel_size=(0.14, 0.085), 
        is_yellow=True,
        angle=-1
    )
    
    raw_sedan = extract_car_rgba(os.path.join(assets_dir, "car_red_sedan.jpg"))
    sedan_with_plate = attach_plate_to_car(
        raw_sedan, 
        plate_text="DL 01 AB 1234", 
        rel_pos=(0.91, 0.62), 
        rel_size=(0.12, 0.08), 
        is_yellow=False,
        angle=1
    )
    
    # 2. Camera Trajectory Configurations across Real Environments
    camera_configs = [
        {
            "filename": "cam_01_north_avenue.mp4",
            "cam_id": "CAM-101",
            "location": "North Avenue Intersection",
            "coords": "12.9716 N, 77.5946 E",
            "start_time": datetime(2026, 9, 2, 14, 10, 0),
            "time_of_day": "day",
            "weather": "clear",
            "bg_path": os.path.join(assets_dir, "bg_cam1.jpg"),
            "trajectory": {
                "suv_start": (-600, 680),
                "suv_end": (1950, 720),
                "suv_scale_start": 0.50,
                "suv_scale_end": 0.55,
                "suv_flip": False
            },
            "distractor": {
                "start_frame": 20,
                "start_x": 1950,
                "start_y": 420,
                "end_x": -500,
                "end_y": 450,
                "scale": 0.35,
                "flip": True
            }
        },
        {
            "filename": "cam_02_central_junction.mp4",
            "cam_id": "CAM-204",
            "location": "Central Metro Junction",
            "coords": "12.9782 N, 77.6011 E",
            "start_time": datetime(2026, 9, 2, 14, 18, 30),
            "time_of_day": "day",
            "weather": "rain",
            "bg_path": os.path.join(assets_dir, "bg_cam2.jpg"),
            "trajectory": {
                "suv_start": (-600, 690),
                "suv_end": (1950, 730),
                "suv_scale_start": 0.52,
                "suv_scale_end": 0.56,
                "suv_flip": False
            },
            "distractor": {
                "start_frame": 10,
                "start_x": 1950,
                "start_y": 410,
                "end_x": -500,
                "end_y": 430,
                "scale": 0.34,
                "flip": True
            }
        },
        {
            "filename": "cam_03_east_boulevard.mp4",
            "cam_id": "CAM-309",
            "location": "East Boulevard Flyover",
            "coords": "12.9845 N, 77.6150 E",
            "start_time": datetime(2026, 9, 2, 14, 27, 15),
            "time_of_day": "night",
            "weather": "clear",
            "bg_path": os.path.join(assets_dir, "bg_cam3.jpg"),
            "trajectory": {
                "suv_start": (-600, 680),
                "suv_end": (1950, 710),
                "suv_scale_start": 0.50,
                "suv_scale_end": 0.54,
                "suv_flip": False
            },
            "distractor": {
                "start_frame": 35,
                "start_x": 1950,
                "start_y": 460,
                "end_x": -500,
                "end_y": 480,
                "scale": 0.36,
                "flip": True
            }
        },
        {
            "filename": "cam_04_south_expressway.mp4",
            "cam_id": "CAM-412",
            "location": "South Expressway Toll",
            "coords": "12.9910 N, 77.6298 E",
            "start_time": datetime(2026, 9, 2, 14, 38, 0),
            "time_of_day": "night",
            "weather": "rain",
            "bg_path": os.path.join(assets_dir, "bg_cam4.jpg"),
            "trajectory": {
                "suv_start": (-600, 700),
                "suv_end": (1950, 730),
                "suv_scale_start": 0.52,
                "suv_scale_end": 0.56,
                "suv_flip": False
            },
            "distractor": {
                "start_frame": 0,
                "start_x": 1950,
                "start_y": 480,
                "end_x": -500,
                "end_y": 500,
                "scale": 0.36,
                "flip": True
            }
        }
    ]
    
    for cfg in camera_configs:
        generate_realistic_feed(cfg, suv_with_plate, sedan_with_plate)
        
    print("\n[SUCCESS] All 4 realistic CCTV videos generated successfully!")

if __name__ == "__main__":
    main()
