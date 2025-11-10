# SageMaker Training Guide - Step-by-Step

## 🎯 Complete Walkthrough for Training on AWS SageMaker

This guide will walk you through training your YOLOv8 model on SageMaker from start to finish.

---

## 📋 Prerequisites Checklist

Before starting, make sure you have:
- [ ] AWS account (free tier works)
- [ ] AWS CLI installed (`aws --version`)
- [ ] AWS credentials configured
- [ ] Your YOLOv8 dataset ready (`ml/datasets/yolo_format/`)

---

## Step 1: Install and Configure AWS CLI

### 1.1 Install AWS CLI

**On Mac:**
```bash
brew install awscli
```

**Or download from:**
https://aws.amazon.com/cli/

### 1.2 Configure AWS Credentials

```bash
aws configure
```

**You'll be asked for:**
1. **AWS Access Key ID:** Get from AWS Console → IAM → Security Credentials
2. **AWS Secret Access Key:** Get from same place
3. **Default region:** `us-east-1` (or your preferred region)
4. **Default output format:** `json`

**How to get credentials:**
1. Go to AWS Console: https://console.aws.amazon.com
2. Click your name (top right) → Security Credentials
3. Create Access Key → Download CSV (save securely!)

---

## Step 2: Create S3 Bucket for Your Dataset

### 2.1 Create Bucket

```bash
# Set your bucket name (must be globally unique)
BUCKET_NAME="room-detection-training-$(date +%s)"

# Create bucket
aws s3 mb s3://$BUCKET_NAME --region us-east-1

# Save bucket name for later
echo $BUCKET_NAME > ml/sagemaker_bucket_name.txt
```

**Or via AWS Console:**
1. Go to S3: https://s3.console.aws.amazon.com
2. Click "Create bucket"
3. Name: `room-detection-training-[your-unique-id]`
4. Region: `us-east-1` (or your region)
5. Click "Create bucket"

### 2.2 Upload Your Dataset

```bash
# Upload your YOLOv8 dataset to S3
aws s3 sync ml/datasets/yolo_format/ s3://$BUCKET_NAME/yolo_format/ \
  --exclude "*.gitkeep"

# Verify upload
aws s3 ls s3://$BUCKET_NAME/yolo_format/images/train/ | head -5
```

**What this does:**
- Uploads all images and labels
- Maintains directory structure
- Takes ~5-10 minutes for 3.1 GB

**Expected structure in S3:**
```
s3://your-bucket/yolo_format/
├── images/
│   ├── train/
│   ├── val/
│   └── test/
├── labels/
│   ├── train/
│   ├── val/
│   └── test/
└── data.yaml
```

---

## Step 3: Create SageMaker Training Script

### 3.1 Create Training Script

We'll create a script that SageMaker will run:

```bash
# Create directory for SageMaker scripts
mkdir -p ml/sagemaker_scripts
```

**File: `ml/sagemaker_scripts/train.py`**

This script will be uploaded to SageMaker and run on the training instance.

---

## Step 4: Set Up IAM Role for SageMaker

### 4.1 Create IAM Role (via Console)

1. Go to IAM: https://console.aws.amazon.com/iam
2. Click "Roles" → "Create role"
3. Select "SageMaker" → "Next"
4. Attach policies:
   - `AmazonSageMakerFullAccess`
   - `AmazonS3FullAccess` (or create custom policy for your bucket only)
5. Name: `SageMakerTrainingRole`
6. Click "Create role"

### 4.2 Get Role ARN

Copy the Role ARN (looks like: `arn:aws:iam::123456789012:role/SageMakerTrainingRole`)

Save it:
```bash
echo "arn:aws:iam::YOUR_ACCOUNT_ID:role/SageMakerTrainingRole" > ml/sagemaker_role_arn.txt
```

---

## Step 5: Create Training Job Script

I'll create a Python script that uses the SageMaker SDK to launch training.

---

## Step 6: Run Training Job

### 6.1 Install SageMaker SDK

```bash
source backend/venv/bin/activate
pip install sagemaker boto3
```

### 6.2 Run Training

The script will:
1. Upload training code to S3
2. Create SageMaker training job
3. Monitor progress
4. Download results when complete

---

## Step 7: Monitor Training

### 7.1 Check Status

```bash
# View training job status
aws sagemaker describe-training-job --training-job-name YOUR_JOB_NAME
```

### 7.2 View Logs

Training logs appear in CloudWatch:
- Go to CloudWatch: https://console.aws.amazon.com/cloudwatch
- Logs → Log groups → `/aws/sagemaker/TrainingJobs`

---

## Step 8: Download Results

### 8.1 Download Trained Model

```bash
# Download model artifacts
aws s3 cp s3://your-bucket/training-output/model.tar.gz ml/models/sagemaker_model.tar.gz

# Extract
cd ml/models
tar -xzf sagemaker_model.tar.gz
```

---

## 🚀 Quick Start Script

I'll create an all-in-one script that does everything for you.

---

## ⚠️ Important Notes

1. **Costs:** Training will cost ~$0.50-$2.00 (use Spot for cheapest)
2. **Time:** ~2-3 hours on GPU (vs 10-11 hours local)
3. **Data:** Your dataset stays in S3 (secure, but costs ~$0.07/month storage)
4. **Cleanup:** Delete S3 data after training to save costs

---

## 📚 Next Steps

After training completes:
1. Download model from S3
2. Test locally with `extract_polygons.py`
3. Integrate into your FastAPI backend
4. Clean up S3 bucket (optional, to save costs)


