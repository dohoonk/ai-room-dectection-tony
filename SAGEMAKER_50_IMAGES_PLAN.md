# SageMaker Training Plan: 50 Images

## Overview

Training a custom SageMaker model with **50 floor plan images** to improve accuracy over the current OpenCV/PyMuPDF approach.

**Key Challenge:** 50 images is small for training from scratch, so we'll use **transfer learning** and **data augmentation**.

---

## 🎯 Goals

1. **Improve accuracy** for room detection from images
2. **Train with 50 images** (small dataset)
3. **Use transfer learning** to leverage pre-trained models
4. **Deploy to SageMaker endpoint** for production use

---

## 📊 Dataset Requirements

### What You Need

**50 floor plan images** with:
- ✅ **Images:** PNG/JPG format, clear floor plans
- ✅ **Annotations:** JSON files with wall segments and/or room boundaries
- ✅ **Format:** Consistent structure across all images

### Annotation Format

Each image needs a corresponding JSON file:

```json
{
  "image_id": "floorplan_001",
  "walls": [
    {
      "start": [100, 100],
      "end": [500, 100],
      "is_load_bearing": false
    },
    {
      "start": [500, 100],
      "end": [500, 400],
      "is_load_bearing": true
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

### Questions to Answer

1. **Do you have 50 images ready?**
   - Where are they located?
   - What format are they in?

2. **Do you have annotations?**
   - If yes: What format are they in?
   - If no: We'll need to create them (manual or semi-automated)

3. **What accuracy issues are you seeing?**
   - Missing rooms?
   - Incorrect boundaries?
   - False positives?
   - Specific image types that fail?

---

## 🏗️ Architecture: Transfer Learning Approach

### Why Transfer Learning?

With only 50 images, training from scratch won't work well. Instead:

1. **Start with pre-trained model** (ImageNet weights)
2. **Fine-tune on your 50 images** (last few layers)
3. **Use heavy data augmentation** (rotate, flip, scale, etc.)
4. **Use small learning rate** (avoid overfitting)

### Model Architecture Options

#### Option 1: U-Net for Semantic Segmentation (Recommended)

**What it does:** Classifies each pixel as "wall" or "not wall"

**Pros:**
- ✅ Pre-trained models available
- ✅ Good for line detection
- ✅ Can extract precise coordinates
- ✅ Works well with small datasets

**Model:** `segmentation_models` library with ResNet34 backbone

```python
import segmentation_models as sm

model = sm.Unet(
    'resnet34',
    encoder_weights='imagenet',
    classes=1,  # Binary: wall vs not-wall
    activation='sigmoid'
)
```

#### Option 2: YOLO for Object Detection

**What it does:** Detects wall segments as bounding boxes

**Pros:**
- ✅ Fast inference
- ✅ Pre-trained on COCO
- ✅ Good for object detection

**Cons:**
- ⚠️ Less precise than segmentation
- ⚠️ May need more data

**Model:** YOLOv8 (Ultralytics)

#### Option 3: Custom CNN for Line Detection

**What it does:** Directly outputs line segments

**Pros:**
- ✅ Matches our exact format
- ✅ Optimized for our use case

**Cons:**
- ⚠️ Requires custom architecture
- ⚠️ More complex

**Recommendation:** **Option 1 (U-Net)** - Best balance of accuracy and simplicity with small dataset.

---

## 📋 Step-by-Step Plan

### Phase 1: Data Preparation (Week 1)

#### Step 1.1: Collect and Organize Images

```bash
# Create directory structure
mkdir -p datasets/training/{images,annotations}
mkdir -p datasets/validation/{images,annotations}
mkdir -p datasets/test/{images,annotations}
```

**Split:**
- **Training:** 40 images (80%)
- **Validation:** 5 images (10%)
- **Test:** 5 images (10%)

#### Step 1.2: Create Annotations (If Needed)

**Option A: Manual Annotation Tool**

Create a simple web tool to:
1. Load image
2. Click to mark wall endpoints
3. Export as JSON

**Option B: Use Current System**

1. Run current algorithm on images
2. Manually correct errors
3. Export corrected annotations

**Option C: Semi-Automated**

1. Use current algorithm to generate initial annotations
2. Review and correct in UI
3. Export corrected version

#### Step 1.3: Convert to Training Format

**Create segmentation masks from wall segments:**

```python
import cv2
import numpy as np
import json

def create_mask_from_walls(image_path, annotation_path, output_path):
    """Convert wall segments to pixel mask."""
    # Load image
    image = cv2.imread(image_path)
    h, w = image.shape[:2]
    
    # Create blank mask
    mask = np.zeros((h, w), dtype=np.uint8)
    
    # Load annotations
    with open(annotation_path) as f:
        data = json.load(f)
    
    # Draw walls on mask
    for wall in data['walls']:
        start = tuple(map(int, wall['start']))
        end = tuple(map(int, wall['end']))
        cv2.line(mask, start, end, 255, thickness=3)
    
    # Save mask
    cv2.imwrite(output_path, mask)
```

#### Step 1.4: Data Augmentation

**Apply augmentations to increase dataset size:**

```python
import albumentations as A

transform = A.Compose([
    A.Rotate(limit=15, p=0.5),
    A.Flip(p=0.5),
    A.RandomBrightnessContrast(p=0.3),
    A.GaussNoise(p=0.2),
    A.ElasticTransform(p=0.2),
    A.ShiftScaleRotate(shift_limit=0.1, scale_limit=0.1, rotate_limit=15, p=0.5)
])
```

**Result:** 40 images → ~200-400 augmented images

#### Step 1.5: Upload to S3

```python
import boto3
from pathlib import Path

s3 = boto3.client('s3')
bucket = 'room-detection-training-data'

# Upload training data
for split in ['train', 'validation', 'test']:
    for image_path in Path(f'datasets/{split}/images').glob('*.png'):
        # Upload image
        s3.upload_file(
            str(image_path),
            bucket,
            f'training-data/{split}/images/{image_path.name}'
        )
        # Upload mask
        mask_path = Path(f'datasets/{split}/masks/{image_path.name}')
        s3.upload_file(
            str(mask_path),
            bucket,
            f'training-data/{split}/masks/{image_path.name}'
        )
```

---

### Phase 2: Training Script Development (Week 1-2)

#### Step 2.1: Create Training Script

**File:** `training_scripts/train_wall_segmentation.py`

```python
import os
import json
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
import torchvision.transforms as transforms
from PIL import Image
import cv2
import numpy as np
import segmentation_models_pytorch as smp
from albumentations import Compose, Rotate, Flip, RandomBrightnessContrast
from albumentations.pytorch import ToTensorV2

class FloorPlanDataset(Dataset):
    def __init__(self, image_dir, mask_dir, transform=None):
        self.image_dir = image_dir
        self.mask_dir = mask_dir
        self.transform = transform
        self.image_files = sorted([f for f in os.listdir(image_dir) if f.endswith(('.png', '.jpg'))])
    
    def __len__(self):
        return len(self.image_files)
    
    def __getitem__(self, idx):
        # Load image
        image_path = os.path.join(self.image_dir, self.image_files[idx])
        image = cv2.imread(image_path)
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        # Load mask
        mask_path = os.path.join(self.mask_dir, self.image_files[idx])
        mask = cv2.imread(mask_path, cv2.IMREAD_GRAYSCALE)
        mask = (mask > 127).astype(np.float32)  # Binary threshold
        
        # Apply augmentations
        if self.transform:
            augmented = self.transform(image=image, mask=mask)
            image = augmented['image']
            mask = augmented['mask']
        
        # Convert to tensor
        image = transforms.ToTensor()(image)
        mask = torch.from_numpy(mask).unsqueeze(0).float()
        
        return image, mask

def train():
    # SageMaker paths
    train_dir = '/opt/ml/input/data/train'
    val_dir = '/opt/ml/input/data/validation'
    model_dir = '/opt/ml/model'
    
    # Data augmentation
    train_transform = Compose([
        Rotate(limit=15, p=0.5),
        Flip(p=0.5),
        RandomBrightnessContrast(p=0.3),
        ToTensorV2()
    ])
    
    val_transform = Compose([ToTensorV2()])
    
    # Datasets
    train_dataset = FloorPlanDataset(
        os.path.join(train_dir, 'images'),
        os.path.join(train_dir, 'masks'),
        transform=train_transform
    )
    val_dataset = FloorPlanDataset(
        os.path.join(val_dir, 'images'),
        os.path.join(val_dir, 'masks'),
        transform=val_transform
    )
    
    train_loader = DataLoader(train_dataset, batch_size=4, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=4, shuffle=False)
    
    # Model (U-Net with ResNet34 backbone)
    model = smp.Unet(
        encoder_name='resnet34',
        encoder_weights='imagenet',
        in_channels=3,
        classes=1,
        activation=None
    )
    
    # Loss and optimizer
    criterion = nn.BCEWithLogitsLoss()
    optimizer = optim.Adam(model.parameters(), lr=0.0001)  # Small LR for fine-tuning
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode='min', factor=0.5, patience=5)
    
    # Training loop
    num_epochs = 50
    best_val_loss = float('inf')
    
    for epoch in range(num_epochs):
        # Training
        model.train()
        train_loss = 0
        for images, masks in train_loader:
            optimizer.zero_grad()
            outputs = model(images)
            loss = criterion(outputs, masks)
            loss.backward()
            optimizer.step()
            train_loss += loss.item()
        
        # Validation
        model.eval()
        val_loss = 0
        with torch.no_grad():
            for images, masks in val_loader:
                outputs = model(images)
                loss = criterion(outputs, masks)
                val_loss += loss.item()
        
        val_loss /= len(val_loader)
        train_loss /= len(train_loader)
        
        scheduler.step(val_loss)
        
        print(f"Epoch {epoch+1}/{num_epochs}, Train Loss: {train_loss:.4f}, Val Loss: {val_loss:.4f}")
        
        # Save best model
        if val_loss < best_val_loss:
            best_val_loss = val_loss
            torch.save(model.state_dict(), os.path.join(model_dir, 'model.pth'))
    
    print(f"Training complete. Best validation loss: {best_val_loss:.4f}")

if __name__ == '__main__':
    train()
```

#### Step 2.2: Create Requirements File

**File:** `training_scripts/requirements.txt`

```
torch>=2.0.0
torchvision>=0.15.0
segmentation-models-pytorch>=0.3.0
opencv-python>=4.8.0
albumentations>=1.3.0
pillow>=10.0.0
numpy>=1.24.0
```

---

### Phase 3: SageMaker Training Setup (Week 2)

#### Step 3.1: Create SageMaker Training Script

**File:** `sagemaker_train.py`

```python
import sagemaker
from sagemaker.pytorch import PyTorch
from sagemaker import get_execution_role

# Initialize
sagemaker_session = sagemaker.Session()
role = get_execution_role()  # Or specify: 'arn:aws:iam::ACCOUNT:role/SageMakerRole'

# Create estimator
estimator = PyTorch(
    entry_point='train_wall_segmentation.py',
    source_dir='training_scripts/',
    role=role,
    framework_version='2.0.1',
    py_version='py310',
    instance_type='ml.g4dn.xlarge',  # GPU instance (cheaper than p3)
    instance_count=1,
    hyperparameters={
        'epochs': 50,
        'batch-size': 4,
        'learning-rate': 0.0001
    },
    output_path='s3://room-detection-training-data/models/',
    use_spot_instances=True,  # Save 70% on training costs
    max_wait=3600,  # Max 1 hour for spot
    max_run=3600
)

# Start training
estimator.fit({
    'train': 's3://room-detection-training-data/training-data/train',
    'validation': 's3://room-detection-training-data/training-data/validation'
})

# Deploy model
predictor = estimator.deploy(
    initial_instance_count=1,
    instance_type='ml.t3.medium',  # Cheaper for inference
    endpoint_name='wall-segmentation-endpoint'
)
```

#### Step 3.2: Run Training

```bash
python sagemaker_train.py
```

**Expected Training Time:** 1-2 hours (with spot instances)

**Expected Cost:** ~$2-5 (much cheaper than p3 instances)

---

### Phase 4: Inference Script (Week 2)

#### Step 4.1: Convert Mask to Wall Segments

**File:** `training_scripts/inference.py`

```python
import torch
import cv2
import numpy as np
from PIL import Image
import segmentation_models_pytorch as smp
from scipy.ndimage import label
from skimage.morphology import skeletonize
from skimage.measure import find_contours

def mask_to_wall_segments(mask, min_length=10):
    """Convert segmentation mask to wall segments."""
    # Threshold mask
    binary = (mask > 0.5).astype(np.uint8)
    
    # Skeletonize (thin to lines)
    skeleton = skeletonize(binary)
    
    # Find contours
    contours = find_contours(skeleton, 0.5)
    
    # Extract line segments
    segments = []
    for contour in contours:
        if len(contour) < 2:
            continue
        
        # Convert to line segments
        for i in range(len(contour) - 1):
            start = contour[i]
            end = contour[i + 1]
            
            # Calculate length
            length = np.sqrt((end[0] - start[0])**2 + (end[1] - start[1])**2)
            
            if length >= min_length:
                segments.append({
                    'start': [int(start[1]), int(start[0])],  # x, y
                    'end': [int(end[1]), int(end[0])],
                    'is_load_bearing': False  # Default
                })
    
    return segments

def predict_walls(image_path, model_path):
    """Predict wall segments from image."""
    # Load model
    model = smp.Unet(
        encoder_name='resnet34',
        encoder_weights=None,
        in_channels=3,
        classes=1,
        activation=None
    )
    model.load_state_dict(torch.load(model_path))
    model.eval()
    
    # Load and preprocess image
    image = cv2.imread(image_path)
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    image_tensor = transforms.ToTensor()(image).unsqueeze(0)
    
    # Predict
    with torch.no_grad():
        output = model(image_tensor)
        mask = torch.sigmoid(output).squeeze().numpy()
    
    # Convert mask to wall segments
    segments = mask_to_wall_segments(mask)
    
    return segments
```

---

### Phase 5: Integration with Backend (Week 2-3)

#### Step 5.1: Create SageMaker Client

**File:** `backend/src/aws_sagemaker.py`

```python
import boto3
import json
import os
from typing import List, Dict, Any
import tempfile

class SageMakerClient:
    def __init__(self, endpoint_name: str = None):
        self.sagemaker_runtime = boto3.client('sagemaker-runtime')
        self.endpoint_name = endpoint_name or os.getenv('SAGEMAKER_ENDPOINT_NAME')
    
    def detect_wall_lines(self, image_path: str) -> List[Dict[str, Any]]:
        """Call SageMaker endpoint to detect wall lines from image."""
        with open(image_path, 'rb') as f:
            image_data = f.read()
        
        try:
            response = self.sagemaker_runtime.invoke_endpoint(
                EndpointName=self.endpoint_name,
                ContentType='image/png',
                Body=image_data
            )
            
            # Parse response (assuming JSON format)
            result = json.loads(response['Body'].read())
            
            # Convert to our WallSegment format
            wall_segments = []
            for line in result.get('walls', []):
                wall_segments.append({
                    'type': 'line',
                    'start': line['start'],
                    'end': line['end'],
                    'is_load_bearing': line.get('is_load_bearing', False)
                })
            
            return wall_segments
        
        except Exception as e:
            print(f"❌ SageMaker error: {e}")
            raise

def create_sagemaker_client():
    """Create SageMaker client instance."""
    return SageMakerClient()
```

#### Step 5.2: Update Backend Endpoint

**File:** `backend/main.py` (update `/detect-rooms-from-image`)

```python
from src.aws_sagemaker import SageMakerClient

@app.post("/detect-rooms-from-image")
async def detect_rooms_from_image(
    file: UploadFile = File(...),
    use_sagemaker: bool = Form(False),  # New parameter
    use_textract: bool = Form(False),
    use_rekognition: bool = Form(False),
    parameters: Optional[str] = Form(None)
):
    # ... existing S3 upload code ...
    
    try:
        if use_sagemaker:
            # Use SageMaker for line detection
            print("🤖 Using SageMaker for wall detection...")
            sagemaker_client = SageMakerClient()
            wall_segments_dict = sagemaker_client.detect_wall_lines(temp_image_path)
            
            # Convert to WallSegment objects
            wall_segments = [
                ParserWallSegment(
                    start=(seg['start'][0], seg['start'][1]),
                    end=(seg['end'][0], seg['end'][1]),
                    is_load_bearing=seg.get('is_load_bearing', False)
                )
                for seg in wall_segments_dict
            ]
        else:
            # Use OpenCV (existing approach)
            # ... existing OpenCV code ...
        
        # Continue with room detection (unchanged)
        # ... existing room detection code ...
        
    finally:
        # Cleanup
        if os.path.exists(temp_image_path):
            os.unlink(temp_image_path)
```

---

## 💰 Cost Estimation (50 Images)

| Component | Cost | Notes |
|-----------|------|-------|
| **Training Instance** (ml.g4dn.xlarge, spot) | $0.30/hour | GPU instance, 70% discount |
| **Training Time** | 1-2 hours | With 50 images, 50 epochs |
| **Total Training Cost** | **$0.30-0.60** | One-time cost |
| **Endpoint Instance** (ml.t3.medium) | $0.052/hour | For inference |
| **Inference Cost** | **$0.00005 per image** | Very cheap |

**Total for 1000 images:** ~$0.05 (vs $16-56 for pre-built services)

**But:** Training accuracy may be lower with only 50 images.

---

## ⚠️ Challenges with 50 Images

### 1. Overfitting Risk

**Problem:** Model may memorize training data, fail on new images

**Solutions:**
- ✅ Heavy data augmentation (40 → 200-400 images)
- ✅ Transfer learning (pre-trained weights)
- ✅ Early stopping (stop when validation loss stops improving)
- ✅ Dropout layers
- ✅ Small learning rate

### 2. Limited Generalization

**Problem:** May not work well on different floor plan styles

**Solutions:**
- ✅ Ensure 50 images cover diverse styles
- ✅ Test on held-out test set
- ✅ Monitor validation metrics closely

### 3. Annotation Quality

**Problem:** Need accurate annotations for all 50 images

**Solutions:**
- ✅ Use current algorithm + manual correction
- ✅ Create annotation tool
- ✅ Validate annotations before training

---

## 📝 Next Steps

### Immediate Actions

1. **Collect 50 Images**
   - Where are they located?
   - What format?

2. **Create Annotations**
   - Do you have them?
   - If not, we'll create annotation tool

3. **Identify Accuracy Issues**
   - What specific problems are you seeing?
   - Which image types fail?

### Questions to Answer

1. **Do you have 50 images ready?** (Location, format)
2. **Do you have annotations?** (Format, location)
3. **What accuracy issues are you seeing?** (Specific examples)
4. **What's your timeline?** (When do you need this?)

---

## 🚀 Quick Start (Once You Have Data)

```bash
# 1. Organize data
python scripts/organize_dataset.py --input-dir /path/to/images --output-dir datasets/

# 2. Create annotations (if needed)
python scripts/create_annotations.py --image-dir datasets/train/images

# 3. Create masks
python scripts/create_masks.py --annotation-dir datasets/train/annotations --output-dir datasets/train/masks

# 4. Upload to S3
python scripts/upload_to_s3.py --data-dir datasets/ --bucket room-detection-training-data

# 5. Train
python sagemaker_train.py
```

---

**Last Updated:** 2025-11-09
**Status:** Ready to Start (Pending Data)

