import os
import shutil
import torch
from ultralytics import YOLO

YOLO_DATA_CONFIG = os.path.abspath("data/yolo_plate_dataset/data.yaml")
OUTPUT_WEIGHTS_AI = os.path.abspath("ai_pipeline/best_plate_yolov8.pt")
OUTPUT_WEIGHTS_WEIGHTS = os.path.abspath("weights/best_plate_yolov8.pt")

def train_plate_detector(
    epochs: int = 15,
    imgsz: int = 640,
    batch_size: int = 16,
    device: str = "auto",
    lr0: float = 0.01,
    lrf: float = 0.01,
    workers: int = 2
):
    """
    Fine-tunes YOLOv8n on license plate dataset frames.
    Exports trained weights to ai_pipeline/best_plate_yolov8.pt and weights/best_plate_yolov8.pt.
    Runs validation evaluation for Precision, Recall, and mAP@50 metrics.
    """
    print("=================================================================")
    print("      Fine-Tuning YOLOv8 License Plate Detector                  ")
    print("=================================================================")
    
    cuda_available = torch.cuda.is_available()
    if device == "auto":
        if cuda_available:
            selected_device = 0
            gpu_name = torch.cuda.get_device_name(0)
            gpu_mem = torch.cuda.get_device_properties(0).total_memory / (1024**3)
            print(f"  [CUDA DETECTED] Using GPU: {gpu_name} ({gpu_mem:.1f} GB VRAM)")
        else:
            selected_device = "cpu"
            print("  [CPU DETECTED] CUDA not available, training on CPU.")
    else:
        selected_device = 0 if (device == "0" and cuda_available) else device
        print(f"  Using specified device: {selected_device}")

    print(f"Dataset Config: {YOLO_DATA_CONFIG}")
    print(f"Epochs: {epochs} | Image Size: {imgsz} | Batch Size: {batch_size} | Device: {selected_device} | Workers: {workers}")

    if not os.path.exists(YOLO_DATA_CONFIG):
        raise FileNotFoundError(f"Dataset config not found at {YOLO_DATA_CONFIG}. Run dataset_loader.py first.")

    # Initialize model with pre-trained yolov8n weights
    model = YOLO("yolov8n.pt")

    # Train model with robust hyperparameters
    results = model.train(
        data=YOLO_DATA_CONFIG,
        epochs=epochs,
        imgsz=imgsz,
        batch=batch_size,
        device=selected_device,
        workers=workers,
        lr0=lr0,
        lrf=lrf,
        momentum=0.937,
        weight_decay=0.0005,
        warmup_epochs=2.0,
        project="runs/detect",
        name="plate_model_training",
        exist_ok=True,
        verbose=True
    )

    # Locate best or last weights dynamically
    save_dir = getattr(results, "save_dir", None) or (getattr(model, "trainer", None) and getattr(model.trainer, "save_dir", None))
    candidate_weight_dirs = []
    if save_dir:
        candidate_weight_dirs.append(os.path.join(str(save_dir), "weights"))
    candidate_weight_dirs.extend([
        os.path.join("runs", "detect", "plate_model_training", "weights"),
        os.path.join("runs", "detect", "runs", "detect", "plate_model_training", "weights")
    ])
    
    source_weights = None
    for wdir in candidate_weight_dirs:
        best_p = os.path.join(wdir, "best.pt")
        last_p = os.path.join(wdir, "last.pt")
        if os.path.exists(best_p):
            source_weights = best_p
            break
        elif os.path.exists(last_p) and not source_weights:
            source_weights = last_p

    if source_weights:
        # Export to ai_pipeline/best_plate_yolov8.pt
        os.makedirs(os.path.dirname(OUTPUT_WEIGHTS_AI), exist_ok=True)
        shutil.copy2(source_weights, OUTPUT_WEIGHTS_AI)
        print(f"\n[SUCCESS] Exported weights to: {OUTPUT_WEIGHTS_AI}")

        # Export to weights/best_plate_yolov8.pt
        os.makedirs(os.path.dirname(OUTPUT_WEIGHTS_WEIGHTS), exist_ok=True)
        shutil.copy2(source_weights, OUTPUT_WEIGHTS_WEIGHTS)
        print(f"[SUCCESS] Exported weights to: {OUTPUT_WEIGHTS_WEIGHTS}")
    else:
        print("\n[WARNING] Trained weight files not found in expected run directory.")

    # Evaluate validation metrics
    print("\nRunning Model Validation Evaluation...")
    val_metrics = model.val(data=YOLO_DATA_CONFIG, imgsz=imgsz, device=selected_device)
    
    mp = float(val_metrics.box.mp)   # Mean Precision
    mr = float(val_metrics.box.mr)   # Mean Recall
    map50 = float(val_metrics.box.map50) # mAP@0.5
    map95 = float(val_metrics.box.map)   # mAP@0.5:0.95

    print("\n=================================================================")
    print("         Model Evaluation & Performance Metrics                  ")
    print("=================================================================")
    print(f"  • Precision:  {mp * 100:.2f}%")
    print(f"  • Recall:     {mr * 100:.2f}%")
    print(f"  • mAP@50:     {map50 * 100:.2f}%")
    print(f"  • mAP@50-95:  {map95 * 100:.2f}%")
    print("=================================================================\n")

    return {
        "precision": mp,
        "recall": mr,
        "map50": map50,
        "map50_95": map95,
        "weights_path": OUTPUT_WEIGHTS_AI
    }

if __name__ == "__main__":
    train_plate_detector(epochs=10, imgsz=640, batch_size=16, device="auto")

