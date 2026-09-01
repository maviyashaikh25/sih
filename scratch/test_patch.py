import torch._dynamo.utils
if not hasattr(torch._dynamo.utils, "NP_SUPPORTED_MODULES"):
    torch._dynamo.utils.NP_SUPPORTED_MODULES = ()

import torchvision
print("Torchvision imported successfully with patch!")

from ultralytics import YOLO
model = YOLO("yolov8n.pt")
print("Ultralytics YOLO loaded successfully!")
