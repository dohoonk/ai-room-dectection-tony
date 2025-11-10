# ML Model Integration Guide

## ✅ Integration Complete!

Your YOLOv8 model has been integrated into the FastAPI backend.

---

## 🎯 New Endpoint

### `/detect-rooms-ml` (POST)

**Description:** Detect rooms from images using the trained YOLOv8 model.

**Request:**
- `file`: Image file (PNG, JPG, etc.) - **Required**
- `confidence`: Confidence threshold (default: 0.05) - **Optional**
- `model_path`: Custom model path (default: uses SageMaker model) - **Optional**

**Response:**
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

## 📝 Usage Examples

### cURL

```bash
curl -X POST "http://localhost:8000/detect-rooms-ml" \
  -F "file=@path/to/floorplan.png" \
  -F "confidence=0.05"
```

### Python

```python
import requests

with open('floorplan.png', 'rb') as f:
    response = requests.post(
        'http://localhost:8000/detect-rooms-ml',
        files={'file': f},
        data={'confidence': 0.05}
    )

rooms = response.json()
print(f"Detected {len(rooms)} rooms")
```

### JavaScript/Fetch

```javascript
const formData = new FormData();
formData.append('file', fileInput.files[0]);
formData.append('confidence', '0.05');

const response = await fetch('http://localhost:8000/detect-rooms-ml', {
  method: 'POST',
  body: formData
});

const rooms = await response.json();
```

---

## 🔄 Model Location

**Default model:** `ml/models/sagemaker/train/weights/best.pt`

**To use a different model:**
- Pass `model_path` parameter in the request
- Or update the default path in `backend/src/ml_room_detector.py`

**After fine-tuning completes:**
- The new model will be at the same location
- Just restart the FastAPI server to use it
- Or pass the new model path in the request

---

## 🚀 Testing the Integration

### 1. Start the FastAPI Server

```bash
cd backend
source venv/bin/activate
uvicorn main:app --reload
```

### 2. Test with cURL

```bash
curl -X POST "http://localhost:8000/detect-rooms-ml" \
  -F "file=@ml/datasets/yolo_format/images/val/1034.png" \
  -F "confidence=0.05"
```

### 3. Check Response

You should see:
```json
[
  {
    "id": "room_001",
    "bounding_box": [100, 200, 300, 400],
    "name_hint": "Room 1"
  },
  ...
]
```

---

## 📊 Comparison: ML vs Graph-Based

### ML Endpoint (`/detect-rooms-ml`)
- ✅ Direct room detection from images
- ✅ No need to extract wall lines first
- ✅ Faster processing
- ✅ Works on any floor plan image
- ⚠️ Requires trained model

### Graph-Based Endpoint (`/detect-rooms-from-image`)
- ✅ Works without ML model
- ✅ More control over processing
- ⚠️ Requires wall line extraction first
- ⚠️ More processing steps

**Recommendation:** Use ML endpoint for production, graph-based as fallback.

---

## 🔧 Configuration

### Model Path

Edit `backend/src/ml_room_detector.py`:

```python
# Change default model path
if model_path is None:
    model_path = project_root / "ml" / "models" / "your_model" / "best.pt"
```

### Confidence Threshold

Default: `0.05` (works well for your current model)

**Adjust if needed:**
- Lower (0.01-0.03): More detections, more false positives
- Higher (0.1-0.25): Fewer detections, higher precision

---

## 🔄 Switching Models

### After Fine-Tuning Completes

1. **Download new model** (if from SageMaker):
   ```bash
   # Model will be in ml/models/sagemaker/train/weights/best.pt
   ```

2. **Restart FastAPI server:**
   ```bash
   # Stop current server (Ctrl+C)
   # Start again
   uvicorn main:app --reload
   ```

3. **Or use custom model path:**
   ```bash
   curl -X POST "http://localhost:8000/detect-rooms-ml" \
     -F "file=@floorplan.png" \
     -F "model_path=/path/to/new/model.pt"
   ```

---

## 📝 API Documentation

Once server is running, visit:
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

You'll see the new `/detect-rooms-ml` endpoint with full documentation.

---

## ✅ Next Steps

1. **Test the endpoint** with a sample image
2. **Integrate into your frontend** (if you have one)
3. **Monitor performance** and adjust confidence if needed
4. **Switch to fine-tuned model** when training completes

---

## 🐛 Troubleshooting

### "Model not found"
- Check model path: `ml/models/sagemaker/train/weights/best.pt`
- Ensure model file exists
- Check file permissions

### "No rooms detected"
- Lower confidence threshold (try 0.01)
- Check image quality
- Verify model is loaded correctly

### "Import error"
- Ensure `ultralytics` is installed: `pip install ultralytics`
- Check Python environment is activated

---

**Your ML model is now integrated and ready to use!** 🚀


