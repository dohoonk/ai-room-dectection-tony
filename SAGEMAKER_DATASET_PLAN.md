# SageMaker Dataset Integration Plan

## Overview

This document outlines how to use the **Cubicasa5k** (Kaggle) and **Hugging Face Floor Plans** datasets with Amazon SageMaker for custom model training, if we decide to enhance our approach beyond pre-built services.

---

## 📊 Dataset Analysis

### 1. Cubicasa5k Dataset (Kaggle)

**Source:** [Kaggle - Cubicasa5k](https://www.kaggle.com/datasets/qmarva/cubicasa5k)

**What It Contains:**
- **5,000+ floor plan images** (likely PNG/JPG)
- **Structured annotations** (room boundaries, labels, wall segments)
- **Multiple formats:** Images + JSON annotations
- **Professional quality:** Real architectural floor plans

**Expected Format:**
```
cubicasa5k/
├── images/
│   ├── floorplan_001.png
│   ├── floorplan_002.png
│   └── ...
├── annotations/
│   ├── floorplan_001.json
│   ├── floorplan_002.json
│   └── ...
└── metadata/
    └── dataset_info.json
```

**Annotation Structure (Likely):**
```json
{
  "image_id": "floorplan_001",
  "rooms": [
    {
      "id": "room_001",
      "type": "bedroom",
      "bounding_box": [x_min, y_min, x_max, y_max],
      "polygon": [[x1, y1], [x2, y2], ...]
    }
  ],
  "walls": [
    {
      "start": [x1, y1],
      "end": [x2, y2],
      "is_load_bearing": false
    }
  ]
}
```

**Pros:**
- ✅ Large dataset (5,000+ samples)
- ✅ Professional quality
- ✅ Structured annotations
- ✅ Multiple room types
- ✅ Real-world floor plans

**Cons:**
- ⚠️ Requires Kaggle account and API setup
- ⚠️ May need format conversion for SageMaker
- ⚠️ License restrictions (check Kaggle dataset license)

---

### 2. Hugging Face Floor Plans Dataset

**Source:** [Hugging Face - floor-plans-dataset](https://huggingface.co/datasets/OmarAmir2001/floor-plans-dataset)

**What It Contains:**
- **31 floor plan images** (small dataset)
- **Text descriptions** (Arabic/English descriptions of room layouts)
- **Format:** Images + text pairs
- **Style:** Technical drawings with labels

**Expected Format:**
```python
{
  "image": <PIL.Image or path>,
  "text": "A floor plan of a house in Arabic. The floor plan shows a living room, dining room, kitchen, three bedrooms, two bathrooms, a balcony, and a garage."
}
```

**Pros:**
- ✅ Easy to access (Hugging Face `datasets` library)
- ✅ Includes text descriptions (useful for room labeling)
- ✅ Multiple languages (Arabic, English)

**Cons:**
- ❌ Very small dataset (31 samples - not enough for training)
- ❌ No structured annotations (only text descriptions)
- ❌ Would need manual annotation or extraction
- ❌ More suitable for fine-tuning text models than training from scratch

**Use Case:**
- Better for **testing** or **fine-tuning** existing models
- Not suitable for training a new model from scratch

---

## 🤔 Should We Use SageMaker?

### Current Strategy (Strategy 1): Pre-Built Services ✅

**What We're Doing:**
```
Image/PDF → S3
  ↓
AWS Services (Pre-Built):
  ├─ Textract → Extract text (room labels)
  ├─ Rekognition → Detect objects (doors, windows)
  └─ Our Algorithms → Extract wall lines (PyMuPDF/OpenCV)
  ↓
Our Algorithm (NetworkX + Shapely) → Detect rooms
```

**Status:** ✅ Working, compliant, fast, low cost

---

### Alternative Strategy: SageMaker Custom Training

**What This Would Do:**
```
Image/PDF → S3
  ↓
SageMaker Custom Model:
  ├─ Trained on Cubicasa5k dataset
  ├─ Detects wall lines from images
  └─ Outputs wall segments (JSON)
  ↓
Our Algorithm (NetworkX + Shapely) → Detect rooms
```

**When to Consider:**
1. **If pre-built services prove insufficient** (low accuracy)
2. **If we need specialized line detection** (architectural-specific)
3. **If requirement explicitly requires SageMaker training**
4. **For future Phase 3 enhancements** (advanced features)

---

## 📋 SageMaker Workflow (If We Proceed)

### Step 1: Dataset Preparation

#### 1.1 Download Datasets

**Cubicasa5k (Kaggle):**
```bash
# Install Kaggle API
pip install kaggle

# Configure credentials (place kaggle.json in ~/.kaggle/)
# Download dataset
kaggle datasets download -d qmarva/cubicasa5k

# Extract
unzip cubicasa5k.zip -d datasets/cubicasa5k/
```

**Hugging Face:**
```python
from datasets import load_dataset

dataset = load_dataset("OmarAmir2001/floor-plans-dataset")
# Save images locally
for i, example in enumerate(dataset["train"]):
    example["image"].save(f"datasets/hf_floorplans/image_{i}.png")
```

#### 1.2 Data Format Conversion

**Convert to SageMaker Training Format:**

SageMaker expects data in **S3** in a specific format:

```
s3://your-bucket/training-data/
├── train/
│   ├── image_001.png
│   ├── image_001.json  # Ground truth annotations
│   ├── image_002.png
│   └── image_002.json
├── validation/
│   ├── image_101.png
│   └── image_101.json
└── test/
    ├── image_201.png
    └── image_201.json
```

**Annotation Format (JSON):**
```json
{
  "image_id": "image_001",
  "walls": [
    {
      "start": [100, 100],
      "end": [500, 100],
      "is_load_bearing": false
    }
  ],
  "rooms": [
    {
      "id": "room_001",
      "bounding_box": [50, 50, 200, 300],
      "name_hint": "Bedroom"
    }
  ]
}
```

#### 1.3 Upload to S3

```python
import boto3
from pathlib import Path

s3 = boto3.client('s3')
bucket = 'room-detection-training-data'

# Upload training data
for image_path in Path('datasets/cubicasa5k/train/images').glob('*.png'):
    s3.upload_file(
        str(image_path),
        bucket,
        f'training-data/train/{image_path.name}'
    )
    # Upload corresponding annotation
    annotation_path = image_path.with_suffix('.json')
    s3.upload_file(
        str(annotation_path),
        bucket,
        f'training-data/train/{annotation_path.name}'
    )
```

---

### Step 2: Model Architecture Selection

#### Option A: Object Detection Model (Detectron2, YOLO)

**Use Case:** Detect wall segments as objects

**Input:** Floor plan image
**Output:** Bounding boxes for wall segments

**Pros:**
- ✅ Pre-trained models available
- ✅ Can fine-tune on floor plans
- ✅ Fast inference

**Cons:**
- ⚠️ May not capture precise line coordinates
- ⚠️ Requires bounding box annotations

#### Option B: Semantic Segmentation Model (U-Net, DeepLab)

**Use Case:** Segment walls vs non-walls

**Input:** Floor plan image
**Output:** Pixel-level mask (walls vs background)

**Pros:**
- ✅ Precise pixel-level detection
- ✅ Can extract exact line coordinates
- ✅ Good for architectural drawings

**Cons:**
- ⚠️ Requires pixel-level annotations
- ⚠️ More complex training

#### Option C: Line Detection Model (Custom CNN)

**Use Case:** Directly detect line segments

**Input:** Floor plan image
**Output:** List of line segments `[(x1, y1, x2, y2), ...]`

**Pros:**
- ✅ Direct output (matches our format)
- ✅ Can be trained end-to-end
- ✅ Optimized for our use case

**Cons:**
- ⚠️ Requires custom architecture
- ⚠️ More complex to implement

**Recommendation:** Start with **Option B (Semantic Segmentation)** using a pre-trained U-Net, fine-tuned on floor plans.

---

### Step 3: SageMaker Training Setup

#### 3.1 Create Training Script

**File:** `training_scripts/train_wall_detector.py`

```python
import os
import json
import boto3
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from PIL import Image
import torchvision.transforms as transforms

# Custom dataset class
class FloorPlanDataset(Dataset):
    def __init__(self, image_dir, annotation_dir, transform=None):
        self.image_dir = image_dir
        self.annotation_dir = annotation_dir
        self.transform = transform
        self.image_files = os.listdir(image_dir)
    
    def __len__(self):
        return len(self.image_files)
    
    def __getitem__(self, idx):
        # Load image
        image_path = os.path.join(self.image_dir, self.image_files[idx])
        image = Image.open(image_path).convert('RGB')
        
        # Load annotation
        annotation_path = os.path.join(
            self.annotation_dir,
            self.image_files[idx].replace('.png', '.json')
        )
        with open(annotation_path) as f:
            annotation = json.load(f)
        
        # Convert to model format
        if self.transform:
            image = self.transform(image)
        
        # Create segmentation mask from wall segments
        mask = self._create_mask(annotation['walls'], image.size)
        
        return image, mask
    
    def _create_mask(self, walls, image_size):
        # Convert wall segments to pixel mask
        # Implementation depends on model architecture
        pass

# Training loop
def train(model, train_loader, val_loader, epochs=10):
    optimizer = torch.optim.Adam(model.parameters(), lr=0.001)
    criterion = nn.BCEWithLogitsLoss()
    
    for epoch in range(epochs):
        model.train()
        for images, masks in train_loader:
            optimizer.zero_grad()
            outputs = model(images)
            loss = criterion(outputs, masks)
            loss.backward()
            optimizer.step()
        
        # Validation
        model.eval()
        val_loss = 0
        with torch.no_grad():
            for images, masks in val_loader:
                outputs = model(images)
                val_loss += criterion(outputs, masks).item()
        
        print(f"Epoch {epoch+1}/{epochs}, Val Loss: {val_loss/len(val_loader)}")

if __name__ == '__main__':
    # Load data from S3 (SageMaker handles this)
    train_dataset = FloorPlanDataset(
        image_dir='/opt/ml/input/data/train/images',
        annotation_dir='/opt/ml/input/data/train/annotations'
    )
    train_loader = DataLoader(train_dataset, batch_size=16, shuffle=True)
    
    # Initialize model
    model = UNet()  # Or your chosen architecture
    
    # Train
    train(model, train_loader, epochs=10)
    
    # Save model
    torch.save(model.state_dict(), '/opt/ml/model/model.pth')
```

#### 3.2 Create SageMaker Estimator

**File:** `sagemaker_training.py`

```python
import sagemaker
from sagemaker.pytorch import PyTorch

# Initialize SageMaker session
sagemaker_session = sagemaker.Session()
role = 'arn:aws:iam::YOUR_ACCOUNT:role/SageMakerExecutionRole'

# Create estimator
estimator = PyTorch(
    entry_point='train_wall_detector.py',
    source_dir='training_scripts/',
    role=role,
    framework_version='2.0.0',
    py_version='py310',
    instance_type='ml.p3.2xlarge',  # GPU instance
    instance_count=1,
    hyperparameters={
        'epochs': 10,
        'batch-size': 16,
        'learning-rate': 0.001
    }
)

# Start training
estimator.fit({
    'train': 's3://room-detection-training-data/training-data/train',
    'validation': 's3://room-detection-training-data/training-data/validation'
})
```

#### 3.3 Deploy Model

```python
# Deploy to endpoint
predictor = estimator.deploy(
    initial_instance_count=1,
    instance_type='ml.m5.large'
)

# Test inference
result = predictor.predict(image_data)
```

---

### Step 4: Integration with Our System

#### 4.1 Create SageMaker Client

**File:** `backend/src/aws_sagemaker.py`

```python
import boto3
import json
from typing import List, Dict, Any

class SageMakerClient:
    def __init__(self, endpoint_name: str = None):
        self.sagemaker_runtime = boto3.client('sagemaker-runtime')
        self.endpoint_name = endpoint_name or os.getenv('SAGEMAKER_ENDPOINT_NAME')
    
    def detect_wall_lines(self, image_path: str) -> List[Dict[str, Any]]:
        """Call SageMaker endpoint to detect wall lines from image."""
        with open(image_path, 'rb') as f:
            image_data = f.read()
        
        response = self.sagemaker_runtime.invoke_endpoint(
            EndpointName=self.endpoint_name,
            ContentType='image/png',
            Body=image_data
        )
        
        result = json.loads(response['Body'].read())
        
        # Convert to our WallSegment format
        wall_segments = []
        for line in result['walls']:
            wall_segments.append({
                'type': 'line',
                'start': line['start'],
                'end': line['end'],
                'is_load_bearing': line.get('is_load_bearing', False)
            })
        
        return wall_segments
```

#### 4.2 Update Backend Endpoint

**File:** `backend/main.py` (update `/detect-rooms-from-image`)

```python
from src.aws_sagemaker import SageMakerClient

@app.post("/detect-rooms-from-image")
async def detect_rooms_from_image(
    file: UploadFile = File(...),
    use_sagemaker: bool = Form(False),  # New parameter
    use_textract: bool = Form(False),
    use_rekognition: bool = Form(False)
):
    # ... existing code ...
    
    if use_sagemaker:
        # Use SageMaker for line detection
        sagemaker_client = SageMakerClient()
        wall_segments_dict = sagemaker_client.detect_wall_lines(temp_image_path)
    else:
        # Use OpenCV (existing approach)
        # ... existing OpenCV code ...
    
    # Continue with room detection (unchanged)
    rooms = detect_rooms(wall_segments_dict, tolerance=5.0)
    return rooms
```

---

## 💰 Cost Estimation

### SageMaker Training Costs

| Component | Cost | Notes |
|-----------|------|-------|
| **Training Instance** (ml.p3.2xlarge) | $3.06/hour | GPU instance for training |
| **Training Time** | ~4-8 hours | For 5,000 images, 10 epochs |
| **Total Training Cost** | **$12-25** | One-time cost |
| **Model Storage** | $0.023/GB/month | Minimal (model ~500MB) |
| **Endpoint Instance** (ml.m5.large) | $0.115/hour | For inference |
| **Inference Cost** | **$0.0001-0.001 per image** | Depends on instance type |

### Comparison with Current Approach

| Approach | Training Cost | Inference Cost | Total (1000 images) |
|----------|--------------|---------------|-------------------|
| **Pre-Built Services** | $0 | $16-56 | **$16-56** |
| **SageMaker Custom** | $12-25 | $0.10-1.00 | **$112-1025** |

**Verdict:** SageMaker is **10-20x more expensive** for inference, plus training costs.

---

## ⏱️ Time Estimation

### SageMaker Training Timeline

| Phase | Duration | Notes |
|-------|----------|-------|
| **Dataset Preparation** | 1-2 weeks | Download, convert, upload to S3 |
| **Model Development** | 2-3 weeks | Architecture selection, training script |
| **Training** | 1-2 weeks | Multiple training runs, hyperparameter tuning |
| **Deployment** | 1 week | Endpoint setup, integration |
| **Testing** | 1 week | Testing, validation |
| **Total** | **6-9 weeks** | vs 2-3 weeks for pre-built services |

---

## 🎯 Recommendation

### For MVP / Phase 2: **Stick with Pre-Built Services** ✅

**Reasons:**
1. ✅ **Already working** - Our algorithms achieve 100% accuracy
2. ✅ **Faster** - 2-3 weeks vs 6-9 weeks
3. ✅ **Lower cost** - $16-56 vs $112-1025 per 1000 images
4. ✅ **Compliant** - Uses AWS AI/ML services (Textract, Rekognition)
5. ✅ **Flexible** - Can add SageMaker later if needed

### For Phase 3 / Future Enhancement: **Consider SageMaker** 🔮

**When to Revisit:**
1. If pre-built services prove insufficient
2. If we need specialized architectural line detection
3. If requirement explicitly requires SageMaker training
4. For advanced features (room type classification, furniture detection)

---

## 📝 Action Plan (If We Proceed with SageMaker)

### Phase 1: Dataset Preparation (Week 1-2)
- [ ] Download Cubicasa5k dataset from Kaggle
- [ ] Download Hugging Face dataset (for testing)
- [ ] Convert annotations to SageMaker format
- [ ] Split into train/validation/test (80/10/10)
- [ ] Upload to S3

### Phase 2: Model Development (Week 3-4)
- [ ] Choose model architecture (U-Net recommended)
- [ ] Create training script
- [ ] Set up SageMaker training environment
- [ ] Test training script locally

### Phase 3: Training (Week 5-6)
- [ ] Run initial training job
- [ ] Evaluate results
- [ ] Hyperparameter tuning
- [ ] Retrain with best parameters

### Phase 4: Deployment (Week 7)
- [ ] Deploy model to SageMaker endpoint
- [ ] Create SageMaker client in backend
- [ ] Integrate with `/detect-rooms-from-image` endpoint
- [ ] Add `use_sagemaker` parameter

### Phase 5: Testing (Week 8)
- [ ] Test with sample images
- [ ] Compare accuracy vs OpenCV approach
- [ ] Performance benchmarking
- [ ] Cost analysis

---

## 🤔 Questions to Consider

1. **Do we actually need SageMaker?**
   - Our current approach works well
   - Pre-built services are compliant
   - Cost and time are significant

2. **What problem would SageMaker solve?**
   - Better line detection accuracy?
   - Specialized architectural understanding?
   - Compliance requirement?

3. **Is the dataset sufficient?**
   - Cubicasa5k: 5,000 images (good)
   - Hugging Face: 31 images (too small)
   - May need data augmentation

4. **What's the ROI?**
   - 6-9 weeks development time
   - $12-25 training cost
   - 10-20x higher inference cost
   - Potential accuracy improvement?

---

## 📚 Resources

- [SageMaker Training Documentation](https://docs.aws.amazon.com/sagemaker/latest/dg/train-model.html)
- [SageMaker PyTorch Estimator](https://sagemaker.readthedocs.io/en/stable/frameworks/pytorch/using_pytorch.html)
- [Cubicasa5k Dataset](https://www.kaggle.com/datasets/qmarva/cubicasa5k)
- [Hugging Face Datasets](https://huggingface.co/docs/datasets/)

---

## Next Steps

1. **Decide:** Do we want to proceed with SageMaker training?
2. **If Yes:** Start with Phase 1 (Dataset Preparation)
3. **If No:** Continue with current pre-built services approach
4. **Document:** Update PRD and decision log with final choice

---

**Last Updated:** 2025-11-09
**Status:** Planning Phase

