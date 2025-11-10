# ML Training Directory

This directory contains all machine learning training code, datasets, and models for room detection.

## 📁 Directory Structure

```
ml/
├── scripts/              # Training and inference scripts
│   ├── convert_cubicasa_to_yolo.py
│   ├── extract_polygons.py
│   └── add_ocr_labels.py
├── datasets/            # YOLOv8 formatted datasets
│   └── yolo_format/     # Converted CubiCasa5K dataset
│       ├── images/
│       ├── labels/
│       └── data.yaml
├── models/              # Trained model weights
│   └── best.pt          # Best model from training
├── runs/                # Training outputs (auto-created by YOLOv8)
│   └── segment/
│       └── train/
└── results/             # Inference results
    ├── results.json
    └── labeled_results.json
```

## 🚀 Quick Start

1. **Convert dataset:**
   ```bash
   python ml/scripts/convert_cubicasa_to_yolo.py \
     --input /path/to/cubicasa5k \
     --output ml/datasets/yolo_format
   ```

2. **Train model:**
   ```bash
   yolo segment train \
     model=yolov8n-seg.pt \
     data=ml/datasets/yolo_format/data.yaml \
     epochs=50 \
     imgsz=1024
   ```

3. **Extract polygons:**
   ```bash
   python ml/scripts/extract_polygons.py \
     --model ml/models/best.pt \
     --image path/to/floorplan.png \
     --output ml/results/results.json
   ```

## 📚 Documentation

- **Training Guide**: See `../TRAINING_GUIDE.md` in project root
- **Quick Start**: See `../QUICK_START.md` in project root
- **Summary**: See `../YOLOV8_TRAINING_SUMMARY.md` in project root

## 📝 Notes

- Training outputs (runs/) are created automatically by YOLOv8
- Best model is typically saved to `runs/segment/train/weights/best.pt`
- Copy trained models to `ml/models/` for easier access
- Results are saved to `ml/results/` for organization


