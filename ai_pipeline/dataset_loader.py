import os
import cv2
import glob
import shutil
import random
import xml.etree.ElementTree as ET
from typing import List, Tuple, Optional

DATASET_HANDLE = "saisirishan/indian-vehicle-dataset"
DATA_ROOT = os.path.abspath("data")
KAGGLE_DIR = os.path.join(DATA_ROOT, "kaggle_dataset")
YOLO_DATASET_DIR = os.path.join(DATA_ROOT, "yolo_plate_dataset")

# Known default cache location on Windows
DEFAULT_KAGGLE_CACHE = r"C:\Users\Maviya Shaikh\.cache\kagglehub\datasets\saisirishan\indian-vehicle-dataset\versions\1"

def find_kaggle_dataset_dir() -> Optional[str]:
    """Locates the downloaded Indian Vehicle Dataset directory."""
    # 1. Check explicit default path if present
    if os.path.exists(DEFAULT_KAGGLE_CACHE):
        return os.path.abspath(DEFAULT_KAGGLE_CACHE)

    # 2. Check local data root
    if os.path.exists(KAGGLE_DIR) and len(os.listdir(KAGGLE_DIR)) > 0:
        return os.path.abspath(KAGGLE_DIR)

    # 3. Check user home cache directory
    home = os.path.expanduser("~")
    cache_path = os.path.join(home, ".cache", "kagglehub", "datasets", "saisirishan", "indian-vehicle-dataset", "versions", "1")
    if os.path.exists(cache_path):
        return os.path.abspath(cache_path)

    # 4. Fallback to kagglehub download if network/auth permits
    try:
        import kagglehub
        download_path = kagglehub.dataset_download(DATASET_HANDLE)
        if os.path.exists(download_path):
            return os.path.abspath(download_path)
    except Exception as e:
        print(f"Notice from kagglehub: {e}")
        
    return None

def parse_voc_xml(xml_path: str, img_w: int, img_h: int) -> List[List[float]]:
    """
    Parses Pascal VOC XML and converts plate bounding boxes to YOLO format.
    Format: [class_id, x_center, y_center, width, height] normalized [0..1]
    """
    boxes = []
    if img_w <= 0 or img_h <= 0:
        return boxes

    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()
        for obj in root.findall("object"):
            bnd = obj.find("bndbox")
            if bnd is not None:
                xmin_elem = bnd.find("xmin")
                ymin_elem = bnd.find("ymin")
                xmax_elem = bnd.find("xmax")
                ymax_elem = bnd.find("ymax")

                if xmin_elem is None or ymin_elem is None or xmax_elem is None or ymax_elem is None:
                    continue

                xmin = float(xmin_elem.text)
                ymin = float(ymin_elem.text)
                xmax = float(xmax_elem.text)
                ymax = float(ymax_elem.text)

                # Clamp to image boundaries
                xmin = max(0.0, min(float(img_w), xmin))
                xmax = max(0.0, min(float(img_w), xmax))
                ymin = max(0.0, min(float(img_h), ymin))
                ymax = max(0.0, min(float(img_h), ymax))

                bw = xmax - xmin
                bh = ymax - ymin

                # Discard zero or degenerate boxes
                if bw >= 2 and bh >= 2:
                    x_center = (xmin + xmax) / (2.0 * img_w)
                    y_center = (ymin + ymax) / (2.0 * img_h)
                    norm_w = bw / float(img_w)
                    norm_h = bh / float(img_h)

                    # Ensure strictly within [0..1]
                    x_center = min(max(x_center, 0.0), 1.0)
                    y_center = min(max(y_center, 0.0), 1.0)
                    norm_w = min(max(norm_w, 0.0), 1.0)
                    norm_h = min(max(norm_h, 0.0), 1.0)

                    boxes.append([0, round(x_center, 6), round(y_center, 6), round(norm_w, 6), round(norm_h, 6)])
    except Exception as e:
        print(f"Warning parsing {xml_path}: {e}")

    return boxes

def build_yolo_dataset_from_kaggle(seed: int = 42, max_samples: Optional[int] = None, dataset_dir: Optional[str] = None) -> str:
    """
    Loads real Indian vehicle images and VOC XML annotations from Kaggle dataset,
    converts to YOLO format, splits into train/val/test, and writes data.yaml.
    """
    if not dataset_dir:
        dataset_dir = find_kaggle_dataset_dir()
    if not dataset_dir or not os.path.exists(dataset_dir):
        raise FileNotFoundError("Could not find downloaded Indian Vehicle Dataset.")

    print(f"Scanning Indian Vehicle Dataset from: {dataset_dir}")
    
    # Collect all image-xml pairs
    pairs = []
    for root, _, files in os.walk(dataset_dir):
        for f in files:
            if f.endswith(".xml"):
                xml_path = os.path.join(root, f)
                base_no_ext = os.path.splitext(xml_path)[0]
                img_path = None
                for ext in [".jpg", ".jpeg", ".png", ".JPG", ".JPEG", ".PNG"]:
                    cand = base_no_ext + ext
                    if os.path.exists(cand):
                        img_path = cand
                        break
                if not img_path and (f.endswith(".jpg.xml") or f.endswith(".png.xml") or f.endswith(".jpeg.xml")):
                    cand = xml_path[:-4]
                    if os.path.exists(cand):
                        img_path = cand
                
                if img_path:
                    pairs.append((img_path, xml_path))

    print(f"Total matching Image-XML pairs found: {len(pairs)}")
    if len(pairs) == 0:
        raise ValueError(f"No valid image-xml pairs found in {dataset_dir}")

    random.seed(seed)
    random.shuffle(pairs)

    if max_samples and max_samples < len(pairs):
        pairs = pairs[:max_samples]

    # Split: 80% train, 10% val, 10% test
    n_total = len(pairs)
    n_train = int(n_total * 0.80)
    n_val = int(n_total * 0.10)
    n_test = n_total - n_train - n_val

    splits_data = {
        "train": pairs[:n_train],
        "val": pairs[n_train:n_train + n_val],
        "test": pairs[n_train + n_val:]
    }

    # Setup directories
    if os.path.exists(YOLO_DATASET_DIR):
        shutil.rmtree(YOLO_DATASET_DIR)

    for split in ["train", "val", "test"]:
        os.makedirs(os.path.join(YOLO_DATASET_DIR, "images", split), exist_ok=True)
        os.makedirs(os.path.join(YOLO_DATASET_DIR, "labels", split), exist_ok=True)

    saved_counts = {"train": 0, "val": 0, "test": 0}

    for split, split_pairs in splits_data.items():
        for idx, (img_path, xml_path) in enumerate(split_pairs):
            img = cv2.imread(img_path)
            if img is None:
                continue
            h, w = img.shape[:2]
            boxes = parse_voc_xml(xml_path, w, h)
            if not boxes:
                continue

            file_stem = f"indian_plate_{split}_{idx:04d}"
            out_img_name = f"{file_stem}.jpg"
            out_lbl_name = f"{file_stem}.txt"

            dst_img_path = os.path.join(YOLO_DATASET_DIR, "images", split, out_img_name)
            dst_lbl_path = os.path.join(YOLO_DATASET_DIR, "labels", split, out_lbl_name)

            cv2.imwrite(dst_img_path, img)
            with open(dst_lbl_path, "w", encoding="utf-8") as f:
                for b in boxes:
                    f.write(f"{b[0]} {b[1]} {b[2]} {b[3]} {b[4]}\n")

            saved_counts[split] += 1

    # Generate data.yaml
    abs_yolo_path = os.path.abspath(YOLO_DATASET_DIR).replace(os.sep, "/")
    yaml_content = f"""path: {abs_yolo_path}
train: images/train
val: images/val
test: images/test

names:
  0: license_plate
"""
    yaml_path = os.path.join(YOLO_DATASET_DIR, "data.yaml")
    with open(yaml_path, "w", encoding="utf-8") as f:
        f.write(yaml_content)

    print("=================================================================")
    print("      YOLO Indian License Plate Dataset Compiled Successfully    ")
    print("=================================================================")
    print(f"  • Train Set: {saved_counts['train']} images with labels")
    print(f"  • Val Set:   {saved_counts['val']} images with labels")
    print(f"  • Test Set:  {saved_counts['test']} images with labels")
    print(f"  • Config:    {yaml_path}")
    print("=================================================================")

    return yaml_path

if __name__ == "__main__":
    build_yolo_dataset_from_kaggle()
