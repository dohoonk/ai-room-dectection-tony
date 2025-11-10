# SageMaker Training - Complete Guide

## 📚 Documentation Overview

I've created a complete set of guides and scripts for training on SageMaker:

### 📖 Guides

1. **`SAGEMAKER_QUICK_START.md`** - Fastest way to get started (5 steps)
2. **`SAGEMAKER_STEP_BY_STEP.md`** - Detailed walkthrough with explanations
3. **`SAGEMAKER_COST_ANALYSIS.md`** - Cost breakdown and comparison
4. **`SAGEMAKER_TRAINING_GUIDE.md`** - Original guide (reference)

### 🔧 Scripts

1. **`sagemaker_scripts/setup_and_upload.sh`** - Uploads dataset to S3
2. **`sagemaker_scripts/train.py`** - Training script (runs on SageMaker)
3. **`sagemaker_scripts/launch_training.py`** - Launches training job

---

## 🚀 Quick Start

**Fastest path to training:**

```bash
# 1. Setup AWS
aws configure

# 2. Upload dataset
bash ml/sagemaker_scripts/setup_and_upload.sh

# 3. Create IAM role (via AWS Console)
# See SAGEMAKER_STEP_BY_STEP.md Step 4

# 4. Install SDK
pip install sagemaker boto3

# 5. Launch training
BUCKET_NAME=$(cat ml/sagemaker_bucket_name.txt)
python ml/sagemaker_scripts/launch_training.py \
  --bucket $BUCKET_NAME \
  --spot \
  --epochs 50 \
  --download
```

**That's it!** Training will complete in ~2-3 hours and cost ~$0.50.

---

## 📋 What Each Script Does

### `setup_and_upload.sh`
- Checks AWS CLI installation
- Verifies AWS credentials
- Creates S3 bucket
- Uploads dataset (5-10 minutes)
- Saves bucket name for later

### `train.py`
- Runs on SageMaker training instance
- Installs YOLOv8 dependencies
- Downloads dataset from S3
- Trains the model
- Saves model to S3

### `launch_training.py`
- Runs on your local machine
- Creates SageMaker training job
- Monitors progress
- Downloads model when complete

---

## 💰 Cost Summary

| Option | Cost | Time | Speedup |
|--------|------|------|---------|
| **Local (M4 Pro)** | $0 | 10-11 hours | 1x |
| **SageMaker GPU Spot** | $0.50 | 2-3 hours | 3-5x |
| **SageMaker GPU** | $2.00 | 2-3 hours | 3-5x |

**Recommendation:** Use Spot instances for best value.

---

## 🎯 Next Steps

1. **Read:** `SAGEMAKER_QUICK_START.md` for fastest path
2. **Or read:** `SAGEMAKER_STEP_BY_STEP.md` for detailed explanations
3. **Check costs:** `SAGEMAKER_COST_ANALYSIS.md` for pricing details

---

## ✅ Checklist

Before training:
- [ ] AWS account created
- [ ] AWS CLI installed and configured
- [ ] IAM role created (SageMakerTrainingRole)
- [ ] Dataset uploaded to S3
- [ ] SageMaker SDK installed

After training:
- [ ] Model downloaded from S3
- [ ] Model tested locally
- [ ] S3 bucket cleaned up (optional, to save costs)

---

## 🆘 Need Help?

- **Detailed steps:** See `SAGEMAKER_STEP_BY_STEP.md`
- **Quick reference:** See `SAGEMAKER_QUICK_START.md`
- **Cost questions:** See `SAGEMAKER_COST_ANALYSIS.md`
- **Troubleshooting:** See Step 8 in `SAGEMAKER_STEP_BY_STEP.md`

---

**Ready to start? Begin with `SAGEMAKER_QUICK_START.md`!** 🚀


