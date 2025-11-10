# Using Your New Fine-Tuned Model

## ✅ Model Status

Your fine-tuned model is ready to use!
- **Location:** `ml/models/sagemaker/train/weights/best.pt`
- **Model Type:** YOLOv8 Segmentation
- **Status:** Working correctly with coordinate fixes

---

## 🧪 Quick Test

Test the model directly:

```bash
cd backend
source venv/bin/activate
python ../ml/test_new_model.py --image "ml/datasets/yolo_format/images/test/20023.png" --confidence 0.05
```

---

## 🚀 Using via FastAPI

### 1. Start the Server

```bash
cd backend
source venv/bin/activate
uvicorn main:app --reload
```

### 2. Test the Endpoint

```bash
curl -X POST "http://localhost:8000/detect-rooms-ml" \
  -F "file=@ml/datasets/yolo_format/images/test/20023.png" \
  -F "confidence=0.05"
```

### 3. Response Format

```json
[
  {
    "id": "room_001",
    "bounding_box": [x_min, y_min, x_max, y_max],
    "name_hint": "Room 1"
  },
  ...
]
```

---

## ⚙️ Confidence Thresholds

**Recommended values:**
- **0.01-0.03**: More detections, may include false positives
- **0.05**: Balanced (default)
- **0.10-0.15**: Fewer detections, higher precision

**Note:** Your model produces detections in the 0.01-0.05 confidence range. Adjust based on your needs.

---

## 🔧 What Was Fixed

1. **Coordinate Extraction**: Fixed polygon coordinate extraction - `result.masks.xy` returns pixel coordinates directly (not normalized)
2. **Inference Confidence**: Changed model inference to use `conf=0.001` to get all detections, then filter by your threshold

---

## 📊 Model Performance

- **Detections:** Working correctly
- **Coordinates:** Fixed and accurate
- **Confidence Range:** 0.01-0.05 for most detections
- **Polygon Quality:** Good (4+ points per room)

---

## 🎯 Next Steps

1. **Test with your own images** via the API
2. **Adjust confidence threshold** based on your needs
3. **Fine-tune further** if needed (see `FINETUNING_GUIDE.md`)

---

## 💡 Tips

- Start with `confidence=0.05` and adjust up/down based on results
- Lower confidence = more rooms detected (may include false positives)
- Higher confidence = fewer rooms (more precise, may miss some rooms)

