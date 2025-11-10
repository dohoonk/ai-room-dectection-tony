# YOLOv8 Room Detection Training - Complete Setup

## 📋 What We've Created

I've set up everything you need to train a YOLOv8 segmentation model for room detection. Here's what's ready:

### 📁 Scripts Created

1. **`ml/scripts/convert_cubicasa_to_yolo.py`**
   - Converts CubiCasa5K dataset to YOLOv8 format
   - Extracts room polygons from masks
   - Creates proper directory structure
   - Generates `data.yaml` configuration

2. **`ml/scripts/extract_polygons.py`**
   - Runs inference with trained model
   - Extracts room polygons from predictions
   - Outputs JSON with polygon coordinates
   - Can create visualization images

3. **`ml/scripts/add_ocr_labels.py`**
   - Adds room type labels using OCR
   - Extracts text from each room region
   - Matches text to room types (Kitchen, Bedroom, etc.)
   - Supports Tesseract and AWS Textract

### 📚 Documentation Created

1. **`TRAINING_GUIDE.md`**
   - Complete beginner-friendly training guide
   - Explains all concepts step-by-step
   - Troubleshooting section
   - Training tips and best practices

2. **`QUICK_START.md`**
   - Fast reference for getting started
   - Step-by-step commands
   - Quick troubleshooting

3. **`YOLOV8_TRAINING_SUMMARY.md`** (this file)
   - Overview of everything created
   - Next steps

---

## 🎯 Your Next Steps

### Step 1: Provide Dataset Path

**I need to know where your CubiCasa5K dataset is located.**

Please provide the full path, for example:
```
/Users/dohoonkim/Downloads/cubicasa5k/
```

Once you provide this, we can run the conversion script.

### Step 2: Install Dependencies

```bash
cd "/Users/dohoonkim/GauntletAI/Room Detection"
source backend/venv/bin/activate  # or create new venv
pip install -r backend/requirements.txt
```

**Also install Tesseract OCR** (for room labeling):
- Mac: `brew install tesseract`
- Linux: `sudo apt-get install tesseract-ocr`
- Windows: https://github.com/UB-Mannheim/tesseract/wiki

### Step 3: Convert Dataset

```bash
python ml/scripts/convert_cubicasa_to_yolo.py \
  --input /path/to/your/cubicasa5k \
  --output ml/datasets/yolo_format
```

### Step 4: Train Model

```bash
# Start with small test run
yolo segment train \
  model=yolov8n-seg.pt \
  data=ml/datasets/yolo_format/data.yaml \
  epochs=50 \
  imgsz=1024 \
  batch=8
```

### Step 5: Test and Use

```bash
# Extract polygons
python ml/scripts/extract_polygons.py \
  --model ml/runs/segment/train/weights/best.pt \
  --image path/to/floorplan.png \
  --output ml/results/results.json

# Add labels
python ml/scripts/add_ocr_labels.py \
  --input ml/results/results.json \
  --image path/to/floorplan.png \
  --output ml/results/labeled_results.json
```

---

## 📊 Expected Dataset Structure

After conversion, you'll have:

```
ml/datasets/yolo_format/
├── images/
│   ├── train/        (training images)
│   ├── val/          (validation images)
│   └── test/         (test images)
├── labels/
│   ├── train/        (training labels - .txt files)
│   ├── val/          (validation labels)
│   └── test/         (test labels)
└── data.yaml         (YOLOv8 configuration)
```

**Label file format** (each .txt file):
```
0 0.123 0.456 0.789 0.012 0.345 0.678 ...
0 0.234 0.567 0.890 0.123 0.456 0.789 ...
```
- First number: class ID (0 = room)
- Rest: Normalized polygon coordinates (x1, y1, x2, y2, ...)

---

## 🎓 Learning Path

Since you're new to ML training, here's the recommended learning path:

1. **Read `QUICK_START.md`** - Get started quickly
2. **Run conversion script** - See how data is prepared
3. **Train small model** - Start with `yolov8n-seg.pt` and 50 epochs
4. **Review `TRAINING_GUIDE.md`** - Understand what's happening
5. **Experiment** - Try different models, epochs, image sizes
6. **Improve** - Use larger models, more epochs for better accuracy

---

## 🔍 Understanding the Pipeline

```
Floor Plan Image
    ↓
YOLOv8-Seg Model (trained)
    ↓
Room Masks/Polygons
    ↓
OCR (Tesseract/AWS Textract)
    ↓
Polygons + Room Labels
    ↓
Your Application
```

**What each step does:**

1. **YOLOv8 Training**: Learns to detect room boundaries
2. **Inference**: Applies trained model to new images
3. **Polygon Extraction**: Converts predictions to coordinates
4. **OCR Labeling**: Identifies room types from text in image
5. **Output**: JSON with polygons and labels

---

## 📦 Dependencies Explained

- **ultralytics**: YOLOv8 library (the model framework)
- **opencv-python**: Image processing (reading/writing images)
- **numpy**: Math operations on arrays
- **tqdm**: Progress bars
- **pillow**: Image manipulation
- **pytesseract**: OCR for room labeling

---

## 🎯 Training Tips

### Start Small
- Use `yolov8n-seg.pt` (nano model) first
- Train for 50 epochs
- Use `imgsz=1024`

### Scale Up
- If results look good, try `yolov8s-seg.pt` (small)
- Increase epochs to 100-200
- Keep `imgsz=1024` or try `imgsz=1536` for more detail

### Memory Issues
- Reduce `batch` size (8 → 4 → 2)
- Reduce `imgsz` (1024 → 512)
- Use smaller model

### Better Accuracy
- More epochs (50 → 100 → 200)
- Larger model (n → s → m)
- More training data
- Data augmentation (YOLOv8 does this automatically)

---

## 🐛 Common Issues

### "CUDA out of memory"
**Solution**: Reduce batch size or image size
```bash
batch=4 imgsz=512
```

### "No labels found"
**Solution**: Check that conversion script completed successfully
```bash
ls ml/datasets/yolo_format/labels/train/*.txt | head -5
```

### Training very slow
**Solutions**:
- Use GPU if available
- Use smaller model (`yolov8n-seg.pt`)
- Reduce image size (`imgsz=512`)

### Model doesn't detect rooms
**Solutions**:
- Train for more epochs
- Use larger model
- Check dataset conversion worked correctly
- Verify label files have correct format

---

## 📝 File Locations

- **Conversion script**: `ml/scripts/convert_cubicasa_to_yolo.py`
- **Polygon extraction**: `ml/scripts/extract_polygons.py`
- **OCR labeling**: `ml/scripts/add_ocr_labels.py`
- **Training guide**: `TRAINING_GUIDE.md` (project root)
- **Quick start**: `QUICK_START.md` (project root)
- **This summary**: `YOLOV8_TRAINING_SUMMARY.md` (project root)
- **ML README**: `ml/README.md`

---

## 🚀 Ready to Start?

1. **Provide your dataset path** (where is CubiCasa5K located?)
2. **Install dependencies** (see Step 2 above)
3. **Run conversion** (see Step 3 above)
4. **Start training** (see Step 4 above)

**I'm here to help at each step!** Just ask if you encounter any issues or have questions.

---

## 📚 Additional Resources

- **YOLOv8 Documentation**: https://docs.ultralytics.com/
- **CubiCasa5K Dataset**: https://github.com/CubiCasa/CubiCasa5k
- **Tesseract OCR**: https://github.com/tesseract-ocr/tesseract

---

**Remember**: Training your first model is a learning process. Start small, test often, and don't be afraid to experiment!

