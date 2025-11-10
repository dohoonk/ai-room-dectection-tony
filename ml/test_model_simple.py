#!/usr/bin/env python3
"""Simple test script to diagnose model issues."""

from ultralytics import YOLO
import cv2
import numpy as np

# Load model
print("📦 Loading model...")
model = YOLO('ml/models/sagemaker/train/weights/best.pt')

# Test image
img_path = 'ml/datasets/yolo_format/images/val/1034.png'
print(f"🖼️  Testing on: {img_path}")

# Get image info
img = cv2.imread(img_path)
print(f"   Image size: {img.shape}")

# Run inference with different settings
print("\n🔍 Testing with different confidence thresholds...")

for conf in [0.1, 0.05, 0.01]:
    print(f"\n   Confidence: {conf}")
    results = model(img_path, conf=conf, imgsz=1024, verbose=False)
    
    result = results[0]
    print(f"   Detections: {len(result.boxes) if result.boxes is not None else 0}")
    
    if result.masks is not None:
        print(f"   Masks found: {len(result.masks)}")
        for i, mask in enumerate(result.masks):
            print(f"      Mask {i}: shape {mask.data.shape}")
    else:
        print(f"   No masks found")

# Try with training image
print("\n🖼️  Testing on training image...")
train_img = 'ml/datasets/yolo_format/images/train/1.png'
results = model(train_img, conf=0.1, imgsz=1024, verbose=False)
result = results[0]
print(f"   Detections: {len(result.boxes) if result.boxes is not None else 0}")
if result.masks is not None:
    print(f"   Masks: {len(result.masks)}")
else:
    print(f"   No masks")

print("\n💡 If no detections, the model may need:")
print("   1. More training epochs")
print("   2. Different hyperparameters")
print("   3. Check training metrics to see final mAP")


