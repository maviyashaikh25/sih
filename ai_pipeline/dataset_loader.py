import os
import cv2
import glob
import shutil
import random
import numpy as np
from typing import List, Tuple, Optional

DATASET_HANDLE = "nimishshandilya/car-number-plate-video"
DATA_ROOT = os.path.abspath("data")
KAGGLE_DIR = os.path.join(DATA_ROOT, "kaggle_dataset")
YOLO_DATASET_DIR = os.path.join(DATA_ROOT, "yolo_plate_dataset")

# Sample Indian Plate numbers for synthetic augmentation
INDIAN_PLATE_TEMPLATES = [
    "DL01AB1234", "HR26DQ9988", "UP16AX5544", "MH12DE1432", "KA05MJ9876",
    "GJ01AB7788", "TN09AK4321", "WB02AZ6543", "RJ14CA9012", "CH01BK3456",
    "DL03CC8899", "HR10EA5678", "UP32BZ1122", "MH02CB3344", "KA01AB9900"
]

def apply_augmentations(image: np.ndarray) -> np.ndarray:
    """Applies realistic CCTV augmentations: motion blur, contrast/brightness jitter, perspective shear."""
    aug = image.copy()
    h, w = aug.shape[:2]

    # 1. Random Brightness / Contrast Jitter
    alpha = random.uniform(0.75, 1.30) # Contrast
    beta = random.randint(-25, 25)      # Brightness
    aug = np.clip(alpha * aug + beta, 0, 255).astype(np.uint8)

    # 2. Random Motion Blur
    if random.random() > 0.4:
        ksize = random.choice([3, 5])
        kernel = np.zeros((ksize, ksize))
        kernel[int((ksize - 1) / 2), :] = np.ones(ksize)
        kernel = kernel / ksize
        aug = cv2.filter2D(aug, -1, kernel)

    # 3. Slight Perspective Shear
    if random.random() > 0.5:
        dx = random.randint(2, max(4, int(w * 0.05)))
        dy = random.randint(2, max(4, int(h * 0.05)))
        pts1 = np.float32([[0, 0], [w, 0], [0, h], [w, h]])
        pts2 = np.float32([[dx, dy], [w - dx, 0], [0, h - dy], [w, h]])
        M = cv2.getPerspectiveTransform(pts1, pts2)
        aug = cv2.warpPerspective(aug, M, (w, h), borderMode=cv2.BORDER_REPLICATE)

    return aug

def generate_synthetic_plate_sample(plate_text: str, bg_size: Tuple[int, int] = (640, 480)) -> Tuple[np.ndarray, List[float]]:
    """
    Generates a realistic synthetic road frame with a vehicle and high-contrast license plate.
    Returns: (frame_img, [class_id, x_center, y_center, width, height] normalized)
    """
    w, h = bg_size
    frame = np.zeros((h, w, 3), dtype=np.uint8)
    
    # Asphalt road background with texture
    road_color = random.randint(35, 55)
    frame[:] = (road_color, road_color, road_color)
    
    # Add road lane markings
    lane_color = (220, 220, 220)
    cv2.line(frame, (w // 2, 0), (w // 2, h), lane_color, 4)

    # Vehicle body rectangle
    veh_w = random.randint(240, 360)
    veh_h = random.randint(160, 240)
    vx1 = (w - veh_w) // 2 + random.randint(-40, 40)
    vy1 = (h - veh_h) // 2 + random.randint(-30, 30)
    vx2 = vx1 + veh_w
    vy2 = vy1 + veh_h

    body_color = random.choice([
        (30, 30, 180),   # Red
        (180, 80, 30),   # Blue
        (30, 30, 30),    # Black
        (200, 200, 200), # White
        (120, 120, 120)  # Grey
    ])
    cv2.rectangle(frame, (vx1, vy1), (vx2, vy2), body_color, -1)
    cv2.rectangle(frame, (vx1, vy1), (vx2, vy2), (10, 10, 10), 2)

    # Rear/Front Windshield
    cv2.rectangle(frame, (vx1 + 20, vy1 + 15), (vx2 - 20, vy1 + int(veh_h * 0.45)), (60, 80, 90), -1)

    # License Plate ROI on lower bumper
    pw = random.randint(90, 140)
    ph = int(pw * random.uniform(0.28, 0.36))
    px1 = vx1 + (veh_w - pw) // 2
    py1 = vy1 + int(veh_h * 0.70)
    px2 = px1 + pw
    py2 = py1 + ph

    # White/Yellow Plate surface
    plate_bg = (245, 245, 245) if random.random() > 0.2 else (30, 220, 240)
    cv2.rectangle(frame, (px1, py1), (px2, py2), plate_bg, -1)
    cv2.rectangle(frame, (px1, py1), (px2, py2), (10, 10, 10), 2)
    # Blue IND strip
    cv2.rectangle(frame, (px1, py1), (px1 + max(4, int(pw * 0.08)), py2), (180, 60, 20), -1)

    # Render License Plate text
    font_scale = pw / 220.0
    cv2.putText(frame, plate_text, (px1 + int(pw * 0.12), py1 + int(ph * 0.75)),
                cv2.FONT_HERSHEY_SIMPLEX, font_scale, (10, 10, 10), 2, cv2.LINE_AA)

    # Apply realistic sensor noise & lighting
    frame = apply_augmentations(frame)

    # YOLO bounding box (class 0: license_plate) normalized [0..1]
    norm_x = (px1 + px2) / (2.0 * w)
    norm_y = (py1 + py2) / (2.0 * h)
    norm_w = pw / float(w)
    norm_h = ph / float(h)

    bbox_yolo = [0, round(norm_x, 6), round(norm_y, 6), round(norm_w, 6), round(norm_h, 6)]
    return frame, bbox_yolo

def extract_frames_from_videos(video_dir: str, max_frames_per_vid: int = 40) -> List[str]:
    """Extracts frames from any available video files in data directory."""
    video_files = glob.glob(os.path.join(video_dir, "*.mp4")) + glob.glob(os.path.join(video_dir, "*.avi"))
    saved_frames = []
    
    frames_out_dir = os.path.join(DATA_ROOT, "extracted_frames")
    os.makedirs(frames_out_dir, exist_ok=True)

    for vid_path in video_files:
        cap = cv2.VideoCapture(vid_path)
        count = 0
        saved_from_vid = 0
        vid_name = os.path.splitext(os.path.basename(vid_path))[0]

        while cap.isOpened() and saved_from_vid < max_frames_per_vid:
            ret, frame = cap.read()
            if not ret:
                break
            if count % 5 == 0:
                frame_path = os.path.join(frames_out_dir, f"{vid_name}_frame_{count}.jpg")
                cv2.imwrite(frame_path, frame)
                saved_frames.append(frame_path)
                saved_from_vid += 1
            count += 1
        cap.release()

    return saved_frames

def build_yolo_dataset(total_samples: int = 150):
    """Creates a complete YOLOv8 dataset with train/val/test splits and data.yaml."""
    print(f"Building YOLO License Plate Dataset with {total_samples} samples...")
    
    splits = {
        "train": int(total_samples * 0.70),
        "val": int(total_samples * 0.20),
        "test": total_samples - int(total_samples * 0.70) - int(total_samples * 0.20)
    }

    for split in ["train", "val", "test"]:
        os.makedirs(os.path.join(YOLO_DATASET_DIR, "images", split), exist_ok=True)
        os.makedirs(os.path.join(YOLO_DATASET_DIR, "labels", split), exist_ok=True)

    sample_idx = 0
    for split, count in splits.items():
        for i in range(count):
            plate_text = random.choice(INDIAN_PLATE_TEMPLATES)
            img, bbox = generate_synthetic_plate_sample(plate_text)
            
            img_filename = f"plate_{split}_{i:04d}.jpg"
            lbl_filename = f"plate_{split}_{i:04d}.txt"

            img_path = os.path.join(YOLO_DATASET_DIR, "images", split, img_filename)
            lbl_path = os.path.join(YOLO_DATASET_DIR, "labels", split, lbl_filename)

            cv2.imwrite(img_path, img)
            with open(lbl_path, "w") as f:
                f.write(f"{bbox[0]} {bbox[1]} {bbox[2]} {bbox[3]} {bbox[4]}\n")
            
            sample_idx += 1

    # Write data.yaml configuration file
    yaml_content = f"""path: {os.path.abspath(YOLO_DATASET_DIR).replace(os.sep, '/')}
train: images/train
val: images/val
test: images/test

names:
  0: license_plate
"""
    yaml_path = os.path.join(YOLO_DATASET_DIR, "data.yaml")
    with open(yaml_path, "w") as f:
        f.write(yaml_content)

    print(f"[SUCCESS] Dataset built at {YOLO_DATASET_DIR}")
    print(f"  - Train samples: {splits['train']}")
    print(f"  - Val samples:   {splits['val']}")
    print(f"  - Test samples:  {splits['test']}")
    print(f"  - Config YAML:   {yaml_path}")
    return yaml_path

def download_and_setup_dataset():
    """Tries kagglehub download, extracts video frames, and compiles YOLO dataset."""
    print(f"Checking Kaggle dataset '{DATASET_HANDLE}'...")
    os.makedirs(KAGGLE_DIR, exist_ok=True)

    try:
        import kagglehub
        download_path = kagglehub.dataset_download(DATASET_HANDLE)
        print(f"Kaggle dataset downloaded to: {download_path}")
        
        for root, _, filenames in os.walk(download_path):
            for fn in filenames:
                src_path = os.path.join(root, fn)
                dst_path = os.path.join(KAGGLE_DIR, fn)
                shutil.copy2(src_path, dst_path)
    except Exception as e:
        print(f"Kagglehub download notice ({e}). Using existing video & synthetic generator.")

    extract_frames_from_videos(DATA_ROOT)
    yaml_path = build_yolo_dataset(total_samples=160)
    return yaml_path

if __name__ == "__main__":
    download_and_setup_dataset()
