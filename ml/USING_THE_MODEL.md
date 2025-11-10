# Using Your Trained Model - Complete Guide

## 🎯 What You Have Now

You have a trained YOLOv8 segmentation model that can detect rooms in floor plan images!

---

## 📥 Step 1: Download Model (If Not Already Done)

### Option A: Model Already Downloaded

If the `--download` flag worked, your model should be in:
```
ml/models/sagemaker/best.pt
```

### Option B: Download from S3

If you need to download manually:

```bash
# Get model location from training job
MODEL_URI=$(aws sagemaker describe-training-job \
  --training-job-name pytorch-training-2025-11-09-07-42-31-036 \
  --query 'ModelArtifacts.S3ModelArtifacts' \
  --output text)

# Download model
mkdir -p ml/models/sagemaker
aws s3 cp $MODEL_URI ml/models/sagemaker_model.tar.gz

# Extract
cd ml/models/sagemaker
tar -xzf ../sagemaker_model.tar.gz
# Model will be in: train/weights/best.pt
```

---

## 🧪 Step 2: Test the Model

### Quick Test

```bash
# Test on a sample image
python ml/scripts/extract_polygons.py \
  --model ml/models/sagemaker/train/weights/best.pt \
  --image path/to/your/floorplan.png \
  --output ml/results/test_results.json
```

### What This Does

1. Loads your trained model
2. Runs inference on the image
3. Extracts room polygons
4. Saves results to JSON

### Expected Output

```json
[
  {
    "room_id": 0,
    "polygon": [[100, 200], [300, 200], [300, 400], [100, 400]],
    "confidence": 0.95
  },
  {
    "room_id": 1,
    "polygon": [[350, 200], [600, 200], [600, 400], [350, 400]],
    "confidence": 0.92
  }
]
```

---

## 🎨 Step 3: Visualize Results (Optional)

Create a script to visualize detected rooms:

```python
import cv2
import json
import numpy as np

# Load image
img = cv2.imread('path/to/floorplan.png')

# Load results
with open('ml/results/test_results.json', 'r') as f:
    results = json.load(f)

# Draw polygons
for room in results:
    polygon = np.array(room['polygon'], np.int32)
    cv2.polylines(img, [polygon], True, (0, 255, 0), 2)
    cv2.putText(img, f"Room {room['room_id']}", 
                tuple(polygon[0]), cv2.FONT_HERSHEY_SIMPLEX, 
                0.5, (0, 255, 0), 2)

# Save
cv2.imwrite('ml/results/visualized.png', img)
```

---

## 🔌 Step 4: Integrate into Your FastAPI Backend

### Update Your Backend

Add model inference to your FastAPI app:

```python
# backend/src/room_detector.py
from ultralytics import YOLO
from pathlib import Path
import cv2
import numpy as np

class RoomDetector:
    def __init__(self, model_path: str):
        self.model = YOLO(model_path)
    
    def detect_rooms(self, image_path: str):
        """Detect rooms in floor plan image."""
        results = self.model(image_path)
        
        # Extract polygons
        rooms = []
        for result in results:
            for mask in result.masks:
                # Convert mask to polygon
                polygon = self._mask_to_polygon(mask.data[0].cpu().numpy())
                rooms.append({
                    "polygon": polygon,
                    "confidence": float(mask.conf)
                })
        
        return rooms
    
    def _mask_to_polygon(self, mask):
        """Convert segmentation mask to polygon coordinates."""
        contours, _ = cv2.findContours(
            (mask * 255).astype(np.uint8),
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE
        )
        
        if contours:
            # Get largest contour
            largest = max(contours, key=cv2.contourArea)
            polygon = largest.reshape(-1, 2).tolist()
            return polygon
        return []

# Initialize detector
detector = RoomDetector("ml/models/sagemaker/train/weights/best.pt")
```

### Add API Endpoint

```python
# backend/src/api.py
from fastapi import FastAPI, UploadFile, File
from room_detector import detector

app = FastAPI()

@app.post("/detect-rooms")
async def detect_rooms(file: UploadFile = File(...)):
    """Detect rooms in uploaded floor plan."""
    # Save uploaded file
    image_path = f"/tmp/{file.filename}"
    with open(image_path, "wb") as f:
        f.write(await file.read())
    
    # Detect rooms
    rooms = detector.detect_rooms(image_path)
    
    return {"rooms": rooms}
```

---

## 📊 Step 5: Evaluate Model Performance

### Check Training Metrics

Your training job saved metrics. Check them:

```bash
# View training metrics in CloudWatch
aws logs get-log-events \
  --log-group-name /aws/sagemaker/TrainingJobs \
  --log-stream-name pytorch-training-2025-11-09-07-42-31-036 \
  --query 'events[*].message' \
  --output text | grep -i "mAP\|loss" | tail -20
```

### Test on Multiple Images

```bash
# Test on validation set
for img in ml/datasets/yolo_format/images/val/*.png; do
    python ml/scripts/extract_polygons.py \
      --model ml/models/sagemaker/train/weights/best.pt \
      --image "$img" \
      --output "ml/results/$(basename $img .png).json"
done
```

---

## 🎯 Step 6: Add Room Type Labels (OCR)

Your model detects rooms but doesn't label them. Add OCR:

```bash
python ml/scripts/add_ocr_labels.py \
  --input ml/results/test_results.json \
  --image path/to/floorplan.png \
  --output ml/results/labeled_results.json \
  --method tesseract
```

This will add room types like "Kitchen", "Bedroom", etc.

---

## 🚀 Step 7: Deploy to Production

### Option A: Keep Model Local

- Model stays on your server
- Fast inference
- No additional costs

### Option B: Deploy to SageMaker Endpoint

```python
from sagemaker.pytorch import PyTorchModel

# Create model
model = PyTorchModel(
    model_data='s3://your-bucket/training-output/model.tar.gz',
    role='arn:aws:iam::...:role/SageMakerTrainingRole',
    framework_version='2.0.1',
    py_version='py310',
    entry_point='inference.py'
)

# Deploy
predictor = model.deploy(instance_type='ml.m5.large', initial_instance_count=1)
```

---

## 📝 Next Steps Summary

1. ✅ **Download model** (if not done)
2. ✅ **Test on sample image**
3. ✅ **Integrate into FastAPI**
4. ✅ **Add OCR for room labels**
5. ✅ **Deploy to production**

---

## 🎉 Congratulations!

You've successfully:
- Trained a YOLOv8 model on SageMaker
- Detected rooms in floor plans
- Ready to integrate into your application!

**Your model is ready to use!** 🚀


