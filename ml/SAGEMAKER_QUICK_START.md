# SageMaker Quick Start Guide

## 🚀 Fastest Way to Train on SageMaker

This is the quickest path to get training on SageMaker. For detailed explanations, see `SAGEMAKER_STEP_BY_STEP.md`.

---

## ⚡ Quick Start (5 Steps)

### Step 1: Install & Configure AWS CLI

```bash
# Install
brew install awscli

# Configure (you'll need AWS access keys)
aws configure
```

**Get AWS keys:**
1. AWS Console → Your name → Security credentials
2. Create access key → Download CSV

---

### Step 2: Upload Dataset

```bash
cd "/Users/dohoonkim/GauntletAI/Room Detection"
bash ml/sagemaker_scripts/setup_and_upload.sh
```

**This creates S3 bucket and uploads your dataset (~5-10 min)**

---

### Step 3: Create IAM Role

1. Go to: https://console.aws.amazon.com/iam
2. Roles → Create role
3. Select "SageMaker"
4. Attach: `AmazonSageMakerFullAccess` + `AmazonS3FullAccess`
5. Name: `SageMakerTrainingRole`
6. Create role

---

### Step 4: Install SageMaker SDK

```bash
source backend/venv/bin/activate
pip install sagemaker boto3
```

---

### Step 5: Launch Training

```bash
# Get bucket name
BUCKET_NAME=$(cat ml/sagemaker_bucket_name.txt)

# Launch training (Spot = cheapest)
python ml/sagemaker_scripts/launch_training.py \
  --bucket $BUCKET_NAME \
  --spot \
  --epochs 50 \
  --download
```

**That's it!** Training will:
- Start in ~2-3 minutes
- Run for ~2-3 hours
- Cost ~$0.50 (Spot) or ~$2.00 (On-Demand)
- Download model automatically when done

---

## 📊 Monitor Training

**AWS Console:**
https://console.aws.amazon.com/sagemaker → Training jobs

**CLI:**
```bash
# Get job name from output, then:
aws sagemaker describe-training-job --training-job-name YOUR_JOB_NAME
```

---

## 💰 Cost Summary

- **Spot GPU:** ~$0.50 (recommended)
- **On-Demand GPU:** ~$2.00
- **CPU:** ~$2.50 (not recommended - same speed as local)

---

## ✅ After Training

Model will be in: `ml/models/sagemaker/best.pt`

Test it:
```bash
python ml/scripts/extract_polygons.py \
  --model ml/models/sagemaker/best.pt \
  --image path/to/floorplan.png \
  --output ml/results/results.json
```

---

## 🆘 Troubleshooting

**"Access Denied"** → Check IAM role permissions  
**"Bucket not found"** → Run setup script again  
**"Training failed"** → Check CloudWatch logs  

---

**For detailed explanations, see `SAGEMAKER_STEP_BY_STEP.md`**


