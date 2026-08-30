import os
import shutil
import torch
from ultralytics import YOLO

YOLO_DATA_CONFIG = os.path.abspath("data/yolo_plate_dataset/data.yaml")
OUTPUT_WEIGHTS = os.path.abspath("ai_pipeline/best_plate_yolov8.pt")

def train_plate_detector(epochs: int = 15, imgsz: int = 640, batch_size: int = 16, device: str = "0"):
    """
    Fine-tunes YOLOv8n on license plate dataset frames using NVIDIA GPU (CUDA).
    Saves trained weights to ai_pipeline/best_plate_yolov8.pt.
    """
    print("=================================================================")
    print("      Fine-Tuning YOLOv8 License Plate Detector (GPU)           ")
    print("=================================================================")
    
    cuda_available = torch.cuda.is_available()
    if cuda_available:
        gpu_name = torch.cuda.get_device_name(0)
        gpu_mem = torch.cuda.get_device_properties(0).total_memory / (1024**3)
        print(f"  [CUDA DETECTED] Using GPU: {gpu_name} ({gpu_mem:.1f} GB VRAM)")
        selected_device = 0
    else:
        print(f"  [WARNING] CUDA not detected. Falling back to device='{device}'")
        selected_device = device

    print(f"Dataset Config: {YOLO_DATA_CONFIG}")
    print(f"Epochs: {epochs} | Image Size: {imgsz} | Batch Size: {batch_size} | Device: {selected_device}")

    if not os.path.exists(YOLO_DATA_CONFIG):
        raise FileNotFoundError(f"Dataset config not found at {YOLO_DATA_CONFIG}. Run dataset_loader.py first.")

    # Initialize model with pre-trained yolov8n weights
    model = YOLO("yolov8n.pt")

    # Train model on GPU
    results = model.train(
        data=YOLO_DATA_CONFIG,
        epochs=epochs,
        imgsz=imgsz,
        batch=batch_size,
        device=selected_device,
        workers=2,
        project="runs/detect",
        name="plate_model_gpu",
        exist_ok=True,
        verbose=True
    )

    # Locate best weights
    best_weights_path = os.path.join("runs", "detect", "plate_model_gpu", "weights", "best.pt")
    if os.path.exists(best_weights_path):
        shutil.copy2(best_weights_path, OUTPUT_WEIGHTS)
        print(f"\n[SUCCESS] Best trained GPU weights saved to: {OUTPUT_WEIGHTS}")
    else:
        last_weights_path = os.path.join("runs", "detect", "plate_model_gpu", "weights", "last.pt")
        if os.path.exists(last_weights_path):
            shutil.copy2(last_weights_path, OUTPUT_WEIGHTS)
            print(f"\n[SUCCESS] Last GPU weights saved to: {OUTPUT_WEIGHTS}")

    # Evaluate validation metrics
    print("\nRunning GPU Validation Evaluation...")
    val_metrics = model.val(device=selected_device)
    
    mp = val_metrics.box.mp   # Mean Precision
    mr = val_metrics.box.mr   # Mean Recall
    map50 = val_metrics.box.map50 # mAP@0.5
    map95 = val_metrics.box.map   # mAP@0.5:0.95

    print("\n=================================================================")
    print("         GPU Model Evaluation & Performance Metrics              ")
    print("=================================================================")
    print(f"  • Precision:  {mp * 100:.1f}%")
    print(f"  • Recall:     {mr * 100:.1f}%")
    print(f"  • mAP@50:     {map50 * 100:.1f}%")
    print(f"  • mAP@50-95:  {map95 * 100:.1f}%")
    print("=================================================================\n")

    return {
        "precision": mp,
        "recall": mr,
        "map50": map50,
        "map50_95": map95,
        "weights_path": OUTPUT_WEIGHTS
    }

if __name__ == "__main__":
    train_plate_detector(epochs=10, imgsz=640, batch_size=16, device="0")
