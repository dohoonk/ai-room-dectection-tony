# YOLOv8 Room Detection Training Guide

## 🎓 Learning Path for Beginners

Welcome! This guide will walk you through training your first machine learning model step-by-step. Don't worry if this is new - we'll explain everything.

---

## 📚 Understanding the Basics

### What is YOLOv8?

**YOLO** stands for "You Only Look Once" - it's a fast object detection model. **YOLOv8-Seg** is the segmentation version, which means it can:
- Find objects in images (rooms in floor plans)
- Draw precise boundaries around them (polygons, not just boxes)
- Do this very quickly

**Think of it like this:**
- Regular detection: "There's a room somewhere in this box"
- Segmentation: "Here's the exact shape of the room"

### Why Segmentation for Floor Plans?

Floor plans have irregular room shapes. We need **polygons** (shapes with many points) not **rectangles** (bounding boxes). Segmentation gives us pixel-perfect boundaries.

---

## 📋 Prerequisites Checklist

Before starting, make sure you have:

- [ ] Python 3.8+ installed
- [ ] CubiCasa5K dataset downloaded
- [ ] At least 8GB RAM (16GB recommended)
- [ ] GPU recommended (but CPU works, just slower)

---

## 🚀 Step-by-Step Training Process

### Step 1: Install Required Packages

Open your terminal and run:

```bash
# Navigate to your project directory
cd "/Users/dohoonkim/GauntletAI/Room Detection"

# Activate your virtual environment (if you have one)
# If not, create one:
python3 -m venv venv
source venv/bin/activate  # On Mac/Linux
# OR
venv\Scripts\activate  # On Windows

# Install required packages
pip install ultralytics opencv-python numpy tqdm pillow
```

**What each package does:**
- `ultralytics`: The YOLOv8 library (contains the model)
- `opencv-python`: Image processing (reading/writing images)
- `numpy`: Math operations on arrays
- `tqdm`: Progress bars (shows how long things take)
- `pillow`: Image manipulation

---

### Step 2: Convert Your Dataset

**First, tell me where your CubiCasa5K dataset is located!**

Once you provide the path, run the conversion script:

```bash
python ml/scripts/convert_cubicasa_to_yolo.py \
  --input /path/to/your/cubicasa5k \
  --output ml/datasets/yolo_format
```

**What this does:**
1. Reads your CubiCasa5K dataset
2. Converts room masks to YOLOv8 format
3. Creates proper folder structure
4. Generates `data.yaml` configuration file

**Expected output structure:**
```
ml/datasets/yolo_format/
├── images/
│   ├── train/     (training images)
│   ├── val/       (validation images)
│   └── test/      (test images)
├── labels/
│   ├── train/     (training labels - polygons)
│   ├── val/       (validation labels)
│   └── test/      (test labels)
└── data.yaml      (configuration file)
```

**Understanding the splits:**
- **Train (80%)**: Images the model learns from
- **Val (10%)**: Images used to check progress during training
- **Test (10%)**: Images saved for final evaluation

---

### Step 3: Verify Your Data

Before training, let's make sure everything is correct:

```bash
# Check how many images you have
ls ml/datasets/yolo_format/images/train | wc -l
ls ml/datasets/yolo_format/images/val | wc -l

# Check a label file (should see polygon coordinates)
head -n 1 ml/datasets/yolo_format/labels/train/*.txt | head -n 5
```

**What to look for:**
- Each image should have a corresponding `.txt` label file
- Label files should contain lines like: `0 0.123 0.456 0.789 0.012 ...`
- Numbers should be between 0.0 and 1.0 (normalized coordinates)

---

### Step 4: Start Training

**For your first training run, use a small model and fewer epochs:**

```bash
# Basic training command
yolo segment train \
  model=yolov8n-seg.pt \
  data=ml/datasets/yolo_format/data.yaml \
  epochs=50 \
  imgsz=1024 \
  batch=8
```

**Breaking down the command:**
- `yolo segment train`: Train a segmentation model
- `model=yolov8n-seg.pt`: Use the "nano" (smallest) model
  - Options: `n` (nano), `s` (small), `m` (medium), `l` (large), `x` (xlarge)
  - Start with `n` for faster training, move to `s` or `m` for better accuracy
- `data=datasets/yolo_format/data.yaml`: Point to your dataset config
- `epochs=50`: Train for 50 complete passes through the data
  - More epochs = better accuracy (up to a point), but takes longer
- `imgsz=1024`: Resize images to 1024x1024 pixels
  - Larger = more detail but slower training
- `batch=8`: Process 8 images at once
  - Increase if you have more GPU memory, decrease if you get "out of memory" errors

**Training time estimates:**
- Nano model, 50 epochs, CPU: ~2-4 hours
- Nano model, 50 epochs, GPU: ~30-60 minutes
- Small model, 100 epochs, GPU: ~2-3 hours

---

### Step 5: Monitor Training

While training, you'll see output like:

```
Epoch    GPU_mem   box_loss   seg_loss   obj_loss   cls_loss   Instances       Size
1/50     2.1G      0.1234     0.5678     0.0123     0.0000     1234           1024
```

**What to watch:**
- **Loss values**: Should decrease over time (lower is better)
- **GPU_mem**: Memory usage (if it's too high, reduce batch size)
- **Instances**: Number of rooms detected

**Training automatically saves:**
- Best model: `ml/runs/segment/train/weights/best.pt`
- Last checkpoint: `ml/runs/segment/train/weights/last.pt`
```

---

### Step 6: Evaluate Your Model

After training completes:

```bash
# Test on validation set
yolo segment val \
  model=ml/runs/segment/train/weights/best.pt \
  data=ml/datasets/yolo_format/data.yaml \
  imgsz=1024
```

**Metrics to understand:**
- **mAP50**: Mean Average Precision at 50% IoU (Intersection over Union)
  - Range: 0.0 to 1.0
  - Higher is better
  - 0.5+ is decent, 0.7+ is good, 0.9+ is excellent
- **mAP50-95**: Average precision across multiple IoU thresholds
  - More strict metric
  - Usually lower than mAP50

---

### Step 7: Test on Your Own Images

```bash
# Predict on a single image
yolo segment predict \
  model=ml/runs/segment/train/weights/best.pt \
  source=path/to/your/floorplan.png \
  save=True
```

This will:
1. Load your trained model
2. Process the image
3. Draw detected room polygons
4. Save result to `ml/runs/segment/predict/`

---

## 🎯 Training Tips for Better Results

### 1. Start Small, Scale Up
- Begin with `yolov8n-seg.pt` (nano) and 50 epochs
- If results look good, try `yolov8s-seg.pt` (small) with 100 epochs
- Only use larger models if you need better accuracy

### 2. Adjust Image Size
- `imgsz=512`: Faster, less detail
- `imgsz=1024`: Balanced (recommended)
- `imgsz=1536`: Slower, more detail

### 3. Handle Memory Issues
If you get "out of memory" errors:
```bash
# Reduce batch size
batch=4  # or even batch=2

# Or reduce image size
imgsz=512
```

### 4. Improve Accuracy
- Train for more epochs: `epochs=100` or `epochs=200`
- Use data augmentation (YOLOv8 does this automatically)
- Use a larger model: `yolov8s-seg.pt` or `yolov8m-seg.pt`

### 5. Early Stopping
YOLOv8 automatically stops if validation loss doesn't improve. This prevents overfitting (memorizing training data instead of learning patterns).

---

## 🔍 Understanding Training Output

### Loss Functions

**box_loss**: How well bounding boxes fit around rooms
- Should decrease from ~0.5 to ~0.1

**seg_loss**: How well polygon boundaries match room shapes
- Should decrease from ~1.0 to ~0.2

**obj_loss**: How well the model detects that rooms exist
- Should decrease from ~0.1 to ~0.01

**cls_loss**: Classification loss (not used since we have 1 class)
- Should stay near 0.0

### Metrics

**Precision**: Of all rooms detected, how many were correct?
- High precision = few false positives

**Recall**: Of all actual rooms, how many did we find?
- High recall = few false negatives

**mAP**: Mean Average Precision (combines precision and recall)
- Best single metric to track

---

## 🐛 Common Issues and Solutions

### Issue: "CUDA out of memory"
**Solution**: Reduce batch size or image size
```bash
batch=4 imgsz=512
```

### Issue: Training is very slow
**Solutions**:
- Use smaller model: `yolov8n-seg.pt`
- Reduce image size: `imgsz=512`
- Use GPU if available
- Reduce number of epochs for testing

### Issue: Model doesn't detect rooms well
**Solutions**:
- Train for more epochs
- Use larger model
- Check that your dataset conversion worked correctly
- Verify label files have correct format

### Issue: "No labels found"
**Solution**: Check that label files exist and have correct format
```bash
# Check a label file
cat ml/datasets/yolo_format/labels/train/0001.txt
# Should see: 0 0.123 0.456 0.789 ...
```

---

## 📊 Next Steps After Training

Once you have a trained model:

1. **Extract Polygons**: Convert model predictions to polygon coordinates
2. **Add OCR**: Use text recognition to label rooms (Kitchen, Bedroom, etc.)
3. **Create API**: Build FastAPI endpoint to use the model
4. **Deploy**: Integrate into your application

See `POLYGON_EXTRACTION.md` and `OCR_LABELING.md` for these steps.

---

## 📚 Additional Resources

- **YOLOv8 Documentation**: https://docs.ultralytics.com/
- **CubiCasa5K Dataset**: https://github.com/CubiCasa/CubiCasa5k
- **Computer Vision Basics**: https://www.coursera.org/learn/computer-vision-basics

---

## ❓ Questions?

If you encounter issues:
1. Check the error message carefully
2. Review this guide's "Common Issues" section
3. Check YOLOv8 documentation
4. Ask for help with specific error messages

**Remember**: Training your first model takes time. Be patient, start small, and gradually improve!

