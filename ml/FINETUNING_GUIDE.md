# Fine-Tuning Your Existing Model - Complete Guide

## 🎯 Overview

You have a trained model at `ml/models/sagemaker/train/weights/best.pt`. Here are all your options to improve it through fine-tuning.

---

## ✅ Option 1: Continue Training (Fine-Tuning) - Recommended

**What it does:** Starts from your current model and trains for more epochs.

**Best for:** Quick improvement without starting from scratch.

### On SageMaker (Recommended)

**Step 1: Upload your current model to S3**

```bash
# Get bucket name
BUCKET_NAME=$(cat ml/sagemaker_bucket_name.txt)

# Upload current model
aws s3 cp ml/models/sagemaker/train/weights/best.pt \
  s3://$BUCKET_NAME/models/best.pt
```

**Step 2: Launch fine-tuning job**

```bash
python ml/sagemaker_scripts/launch_training.py \
  --bucket $BUCKET_NAME \
  --spot \
  --epochs 50 \
  --model s3://$BUCKET_NAME/models/best.pt \
  --download
```

**What happens:**
- Loads your trained model (not pre-trained)
- Continues training for 50 more epochs
- Learns from where it left off
- Faster convergence

**Cost:** ~$0.50 (Spot)  
**Time:** ~2-3 hours  
**Expected improvement:** 15-25% better accuracy

---

### On Local Machine (Free, Slower)

```bash
source backend/venv/bin/activate

yolo segment train \
  model=ml/models/sagemaker/train/weights/best.pt \
  data=ml/datasets/yolo_format/data.yaml \
  epochs=50 \
  imgsz=1024 \
  batch=8 \
  device=mps \
  project=ml/runs \
  name=finetuned_model
```

**What happens:**
- Uses your current model as starting point
- Trains for 50 more epochs
- Saves to `ml/runs/finetuned_model/weights/best.pt`

**Cost:** $0  
**Time:** ~10-11 hours (on your M4 Pro)  
**Expected improvement:** 15-25% better accuracy

---

## ✅ Option 2: Train for More Epochs (Same Model)

**What it does:** Trains your current model for longer.

**Best for:** When model is still learning (loss decreasing).

### On SageMaker

```bash
python ml/sagemaker_scripts/launch_training.py \
  --bucket $BUCKET_NAME \
  --spot \
  --epochs 100 \
  --model ml/models/sagemaker/train/weights/best.pt \
  --download
```

**Or start from pre-trained and train longer:**

```bash
python ml/sagemaker_scripts/launch_training.py \
  --bucket $BUCKET_NAME \
  --spot \
  --epochs 100 \
  --model yolov8n-seg.pt \
  --download
```

**Cost:** ~$1.00 (Spot)  
**Time:** ~4-6 hours  
**Expected improvement:** 10-20% better accuracy

---

## ✅ Option 3: Adjust Hyperparameters

**What it does:** Fine-tunes learning rate, batch size, etc. for better learning.

### Modify Training Script

Edit `ml/sagemaker_scripts/train.py` to add hyperparameters:

```python
# In train_model function, add:
cmd = [
    "yolo", "segment", "train",
    f"model={model}",
    f"data={updated_yaml}",
    f"epochs={epochs}",
    f"imgsz={imgsz}",
    f"batch={batch}",
    "lr0=0.001",           # Lower learning rate for fine-tuning
    "lrf=0.01",            # Final learning rate
    "momentum=0.937",
    "weight_decay=0.0005",
    "warmup_epochs=3.0",
    "box=7.5",
    "cls=0.5",
    "dfl=1.5",
    "project=/opt/ml/model",
    "name=train"
]
```

**Or use YOLOv8's built-in fine-tuning:**

```bash
yolo segment train \
  model=ml/models/sagemaker/train/weights/best.pt \
  data=ml/datasets/yolo_format/data.yaml \
  epochs=50 \
  imgsz=1024 \
  batch=8 \
  lr0=0.001 \        # Lower LR for fine-tuning
  device=mps
```

**Expected improvement:** 5-15% better accuracy

---

## ✅ Option 4: Use Larger Model Architecture

**What it does:** Start with larger pre-trained model, then fine-tune.

**Best for:** When you need better accuracy and have budget.

### On SageMaker

```bash
# Use yolov8s-seg.pt (small) instead of yolov8n-seg.pt (nano)
python ml/sagemaker_scripts/launch_training.py \
  --bucket $BUCKET_NAME \
  --spot \
  --epochs 100 \
  --model yolov8s-seg.pt \
  --download
```

**Model sizes:**
- `yolov8n-seg.pt`: 6.5 MB (current)
- `yolov8s-seg.pt`: ~22 MB (better accuracy)
- `yolov8m-seg.pt`: ~52 MB (even better)

**Cost:** ~$1.50 (Spot)  
**Time:** ~5-7 hours  
**Expected improvement:** 20-30% better accuracy

---

## ✅ Option 5: Progressive Fine-Tuning

**What it does:** Fine-tune in stages with different settings.

**Stage 1: Fine-tune with lower learning rate**
```bash
yolo segment train \
  model=ml/models/sagemaker/train/weights/best.pt \
  data=ml/datasets/yolo_format/data.yaml \
  epochs=25 \
  lr0=0.001 \
  device=mps
```

**Stage 2: Fine-tune with even lower learning rate**
```bash
yolo segment train \
  model=ml/runs/segment/train/weights/best.pt \
  data=ml/datasets/yolo_format/data.yaml \
  epochs=25 \
  lr0=0.0005 \
  device=mps
```

**Expected improvement:** 20-30% better accuracy

---

## ✅ Option 6: Fine-Tune on Specific Data

**What it does:** Fine-tune on harder examples or specific room types.

### Create Subset Dataset

```bash
# Create directory for fine-tuning data
mkdir -p ml/datasets/finetune/images/train
mkdir -p ml/datasets/finetune/labels/train

# Copy specific images (e.g., complex floor plans)
# Then train on this subset
```

**Useful for:**
- Improving on specific room types
- Fixing common errors
- Handling edge cases

---

## 📊 Comparison Table

| Option | Cost | Time | Improvement | Difficulty |
|--------|------|------|-------------|------------|
| **Continue Training (SageMaker)** | $0.50 | 2-3h | 15-25% | Easy |
| **Continue Training (Local)** | $0 | 10-11h | 15-25% | Easy |
| **More Epochs** | $1.00 | 4-6h | 10-20% | Easy |
| **Adjust Hyperparameters** | $0.50 | 2-3h | 5-15% | Medium |
| **Larger Model** | $1.50 | 5-7h | 20-30% | Easy |
| **Progressive Fine-Tuning** | $0 | 20-22h | 20-30% | Medium |

---

## 🎯 Recommended Approach

### Quick Improvement (Best Value)

**Option 1: Continue Training on SageMaker**

```bash
# 1. Upload current model
BUCKET_NAME=$(cat ml/sagemaker_bucket_name.txt)
aws s3 cp ml/models/sagemaker/train/weights/best.pt \
  s3://$BUCKET_NAME/models/best.pt

# 2. Fine-tune
python ml/sagemaker_scripts/launch_training.py \
  --bucket $BUCKET_NAME \
  --spot \
  --epochs 50 \
  --model s3://$BUCKET_NAME/models/best.pt \
  --download
```

**Why:**
- Fast (2-3 hours)
- Cheap ($0.50)
- Good improvement (15-25%)
- Easy to do

---

### Best Results (More Investment)

**Option 4: Larger Model + Fine-Tune**

```bash
# Use larger model, train longer
python ml/sagemaker_scripts/launch_training.py \
  --bucket $BUCKET_NAME \
  --spot \
  --epochs 100 \
  --model yolov8s-seg.pt \
  --download
```

**Why:**
- Best accuracy (20-30% improvement)
- Still affordable ($1.50)
- One command

---

## 🔧 Step-by-Step: Fine-Tune on SageMaker

### Step 1: Upload Current Model

```bash
BUCKET_NAME=$(cat ml/sagemaker_bucket_name.txt)

# Upload your current best model
aws s3 cp ml/models/sagemaker/train/weights/best.pt \
  s3://$BUCKET_NAME/models/best.pt

echo "✅ Model uploaded to S3"
```

### Step 2: Update Training Script (Optional)

If you want to adjust hyperparameters, edit `ml/sagemaker_scripts/train.py`:

```python
# Add to train_model function:
"lr0=0.001",  # Lower learning rate for fine-tuning
```

### Step 3: Launch Fine-Tuning Job

```bash
python ml/sagemaker_scripts/launch_training.py \
  --bucket $BUCKET_NAME \
  --spot \
  --epochs 50 \
  --model s3://$BUCKET_NAME/models/best.pt \
  --download
```

### Step 4: Compare Results

```bash
# Test old model
python ml/scripts/extract_polygons.py \
  --model ml/models/sagemaker/train/weights/best.pt \
  --image test.png \
  --output old_results.json \
  --confidence 0.05

# Test new model
python ml/scripts/extract_polygons.py \
  --model ml/models/sagemaker/train/weights/best.pt \
  --image test.png \
  --output new_results.json \
  --confidence 0.05

# Compare
echo "Old model rooms: $(cat old_results.json | grep -o '\"room_id\"' | wc -l)"
echo "New model rooms: $(cat new_results.json | grep -o '\"room_id\"' | wc -l)"
```

---

## 💡 Tips for Better Fine-Tuning

### 1. Use Lower Learning Rate

Fine-tuning should use lower learning rate than initial training:
- Initial training: `lr0=0.01`
- Fine-tuning: `lr0=0.001` or `lr0=0.0005`

### 2. Monitor Validation Loss

Stop if validation loss stops improving (early stopping).

### 3. Use Data Augmentation

YOLOv8 does this automatically, but you can adjust:
- More augmentation = better generalization
- Less augmentation = faster convergence

### 4. Train on Hard Examples

If you have images where model fails, add more of those to training set.

---

## 🎯 Quick Decision Guide

**If you want:**
- **Fast improvement:** Continue training on SageMaker (Option 1)
- **Best accuracy:** Larger model + more epochs (Option 4)
- **Free option:** Continue training locally (Option 1 local)
- **Maximum improvement:** Progressive fine-tuning (Option 5)

---

## 📝 Summary

**Best option for most people:** Continue training on SageMaker
- Upload current model to S3
- Train for 50 more epochs
- Cost: ~$0.50
- Time: ~2-3 hours
- Improvement: 15-25%

**Ready to start?** Follow the "Step-by-Step" section above! 🚀


