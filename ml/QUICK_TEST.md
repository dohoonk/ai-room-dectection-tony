# Quick Test Script - Full Path

## 📝 Complete Test Script

**File Location:** `/Users/dohoonkim/GauntletAI/Room Detection/ml/test_model_complete.py`

---

## 🚀 Quick Start

### Basic Usage (with default paths)

```bash
cd "/Users/dohoonkim/GauntletAI/Room Detection"
source backend/venv/bin/activate
python ml/test_model_complete.py
```

### With Custom Image

```bash
python ml/test_model_complete.py \
  --image "ml/datasets/yolo_format/images/test/20023.png" \
  --confidence 0.01
```

### With Your Own Image

```bash
python ml/test_model_complete.py \
  --image "/path/to/your/floorplan.png" \
  --confidence 0.05
```

### With Custom Model

```bash
python ml/test_model_complete.py \
  --image "ml/datasets/yolo_format/images/test/20023.png" \
  --model "ml/models/sagemaker/train/weights/best.pt" \
  --confidence 0.01
```

---

## 📋 Full Command Examples

### Example 1: Test with default settings
```bash
cd "/Users/dohoonkim/GauntletAI/Room Detection"
source backend/venv/bin/activate
python ml/test_model_complete.py
```

### Example 2: Test with specific image and confidence
```bash
cd "/Users/dohoonkim/GauntletAI/Room Detection"
source backend/venv/bin/activate
python ml/test_model_complete.py \
  --image "ml/datasets/yolo_format/images/test/20023.png" \
  --confidence 0.01
```

### Example 3: Test without saving results
```bash
cd "/Users/dohoonkim/GauntletAI/Room Detection"
source backend/venv/bin/activate
python ml/test_model_complete.py \
  --image "ml/datasets/yolo_format/images/test/20023.png" \
  --confidence 0.05 \
  --no-save
```

### Example 4: Test with absolute paths
```bash
cd "/Users/dohoonkim/GauntletAI/Room Detection"
source backend/venv/bin/activate
python ml/test_model_complete.py \
  --image "/Users/dohoonkim/GauntletAI/Room Detection/ml/datasets/yolo_format/images/test/20023.png" \
  --model "/Users/dohoonkim/GauntletAI/Room Detection/ml/models/sagemaker/train/weights/best.pt" \
  --confidence 0.01
```

---

## 📊 Default Paths

The script uses these default paths:

- **Model:** `ml/models/sagemaker/train/weights/best.pt`
- **Test Image:** `ml/datasets/yolo_format/images/test/20023.png`
- **Output Directory:** `ml/results/`
- **Confidence:** `0.05`

---

## 🎯 What the Script Does

1. ✅ Loads the YOLOv8 model
2. ✅ Loads the test image
3. ✅ Runs room detection
4. ✅ Displays results (top 10 rooms by confidence)
5. ✅ Converts to API format (normalized bounding boxes)
6. ✅ Saves results to JSON file (unless `--no-save`)

---

## 📤 Output

Results are saved to:
```
ml/results/test_results_<image_name>.json
```

The JSON includes:
- Image path and size
- Confidence threshold used
- Total rooms detected
- Full room data (both raw polygons and normalized bounding boxes)

---

## 💡 Tips

- **Confidence 0.01-0.03**: More detections (may include false positives)
- **Confidence 0.05**: Balanced (recommended)
- **Confidence 0.10+**: Fewer detections (higher precision)

---

## 🔧 Troubleshooting

**Model not found:**
- Check: `ml/models/sagemaker/train/weights/best.pt` exists
- Or use `--model` to specify custom path

**Image not found:**
- Use absolute path or relative path from project root
- Check file exists: `ls -la <image_path>`

**No rooms detected:**
- Try lower confidence: `--confidence 0.01`
- Verify image is a valid floor plan
- Check model is working: `python ml/test_model_complete.py --help`

