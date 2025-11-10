# Quick Start: Training Your First Room Detection Model

## 🎯 Goal
Train a YOLOv8 model to detect rooms in floor plans and output polygons with room types.

---

## 📍 Step 1: Tell Me Where Your Dataset Is

**I need the full path to your CubiCasa5K dataset.**

For example:
```
/Users/dohoonkim/Downloads/cubicasa5k/
```

Or wherever you downloaded it. Once you provide this, we'll proceed!

---

## 📦 Step 2: Install Dependencies

```bash
# Navigate to project directory
cd "/Users/dohoonkim/GauntletAI/Room Detection"

# Activate virtual environment (if you have one)
source backend/venv/bin/activate  # or create new one

# Install ML packages
pip install ultralytics opencv-python numpy tqdm pillow pytesseract
```

**Note**: For Tesseract OCR, you also need the system package:
- **Mac**: `brew install tesseract`
- **Linux**: `sudo apt-get install tesseract-ocr`
- **Windows**: Download from https://github.com/UB-Mannheim/tesseract/wiki

---

## 🔄 Step 3: Convert Dataset to YOLOv8 Format

Once you provide your dataset path, run:

```bash
python ml/scripts/convert_cubicasa_to_yolo.py \
  --input /path/to/your/cubicasa5k \
  --output ml/datasets/yolo_format
```

**What this does:**
- Reads your CubiCasa5K dataset
- Converts room masks to YOLOv8 polygon format
- Creates proper folder structure
- Generates `data.yaml` configuration

**Expected time:** 5-15 minutes depending on dataset size

---

## 🚀 Step 4: Train Your Model

**Start with a small test run:**

```bash
yolo segment train \
  model=yolov8n-seg.pt \
  data=ml/datasets/yolo_format/data.yaml \
  epochs=50 \
  imgsz=1024 \
  batch=8
```

**What each parameter means:**
- `yolov8n-seg.pt`: Nano model (smallest, fastest)
- `epochs=50`: Train for 50 complete passes
- `imgsz=1024`: Resize images to 1024x1024
- `batch=8`: Process 8 images at once

**Training time:**
- CPU: 2-4 hours
- GPU: 30-60 minutes

**Watch for:**
- Loss values decreasing (good!)
- Model saved to `runs/segment/train/weights/best.pt`

---

## 🧪 Step 5: Test Your Model

```bash
# Test on validation set
yolo segment val \
  model=ml/runs/segment/train/weights/best.pt \
  data=ml/datasets/yolo_format/data.yaml \
  imgsz=1024

# Test on your own image
yolo segment predict \
  model=ml/runs/segment/train/weights/best.pt \
  source=path/to/your/floorplan.png \
  save=True
```

---

## 📐 Step 6: Extract Polygons

```bash
python ml/scripts/extract_polygons.py \
  --model ml/runs/segment/train/weights/best.pt \
  --image path/to/floorplan.png \
  --output ml/results/results.json \
  --visualize ml/results/output.png
```

This creates `results.json` with room polygons.

---

## 🏷️ Step 7: Add Room Labels with OCR

```bash
python ml/scripts/add_ocr_labels.py \
  --input ml/results/results.json \
  --image path/to/floorplan.png \
  --output ml/results/labeled_results.json \
  --method tesseract
```

This adds room type labels (Kitchen, Bedroom, etc.) to each room.

---

## 📊 Expected Results

After training, you should have:

1. **Trained model**: `runs/segment/train/weights/best.pt`
2. **Room polygons**: JSON file with coordinates
3. **Room labels**: Each room tagged with type

**Example output:**
```json
{
  "rooms": [
    {
      "room_id": 0,
      "polygon": [[100, 200], [300, 200], [300, 400], [100, 400]],
      "confidence": 0.95,
      "room_type": "kitchen"
    }
  ]
}
```

---

## 🆘 Troubleshooting

### "CUDA out of memory"
```bash
# Reduce batch size
batch=4
```

### Training is too slow
```bash
# Use smaller model or image size
model=yolov8n-seg.pt imgsz=512
```

### "No labels found"
Check that conversion script ran successfully and label files exist.

---

## 📚 Next Steps

1. **Improve accuracy**: Train longer (`epochs=100`) or use larger model (`yolov8s-seg.pt`)
2. **Create API**: Build FastAPI endpoint (see next section)
3. **Deploy**: Integrate into your application

---

## 🎓 Learning Resources

- **YOLOv8 Docs**: https://docs.ultralytics.com/
- **Full Training Guide**: See `TRAINING_GUIDE.md`
- **Script Documentation**: Each script has detailed comments

---

## ❓ Need Help?

1. Check `TRAINING_GUIDE.md` for detailed explanations
2. Review script comments (they explain everything)
3. Ask specific questions about errors you encounter

**Remember**: Start small, test often, and gradually improve!

