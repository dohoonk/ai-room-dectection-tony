# SageMaker Training - Complete Step-by-Step Guide

## 🎯 Overview

This guide walks you through training your YOLOv8 model on AWS SageMaker from start to finish. Each step is explained in detail.

**Estimated time:** 30-60 minutes setup, 2-3 hours training  
**Estimated cost:** $0.50 - $2.00

---

## 📋 Prerequisites

Before starting, you need:
1. AWS account (create at https://aws.amazon.com)
2. Your YOLOv8 dataset ready (`ml/datasets/yolo_format/`)
3. Terminal access

---

## Step 1: Install AWS CLI

### 1.1 Check if AWS CLI is installed

```bash
aws --version
```

If you see a version number, skip to Step 2.

### 1.2 Install AWS CLI (Mac)

```bash
brew install awscli
```

**Or download installer:**
- Visit: https://aws.amazon.com/cli/
- Download macOS installer
- Run the installer

### 1.3 Verify Installation

```bash
aws --version
# Should show: aws-cli/2.x.x Python/3.x.x ...
```

---

## Step 2: Configure AWS Credentials

### 2.1 Get AWS Access Keys

1. **Go to AWS Console:** https://console.aws.amazon.com
2. **Click your name** (top right corner)
3. **Click "Security credentials"**
4. **Scroll to "Access keys"**
5. **Click "Create access key"**
6. **Select "Command Line Interface (CLI)"**
7. **Click "Next"**
8. **Click "Create access key"**
9. **IMPORTANT:** Download the CSV file or copy:
   - Access Key ID
   - Secret Access Key

⚠️ **Security Note:** Never share these keys! They give full access to your AWS account.

### 2.2 Configure AWS CLI

```bash
aws configure
```

**Enter the following when prompted:**

1. **AWS Access Key ID:** [Paste your Access Key ID]
2. **AWS Secret Access Key:** [Paste your Secret Access Key]
3. **Default region name:** `us-east-1` (or your preferred region)
4. **Default output format:** `json`

**Example:**
```
AWS Access Key ID [None]: AKIAIOSFODNN7EXAMPLE
AWS Secret Access Key [None]: wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
Default region name [None]: us-east-1
Default output format [None]: json
```

### 2.3 Verify Configuration

```bash
aws sts get-caller-identity
```

You should see your AWS account ID and user info. If you see an error, check your credentials.

---

## Step 3: Upload Dataset to S3

### 3.1 Run Setup Script

I've created an automated script that does everything:

```bash
cd "/Users/dohoonkim/GauntletAI/Room Detection"
bash ml/sagemaker_scripts/setup_and_upload.sh
```

**What this script does:**
1. Checks AWS CLI is installed
2. Verifies AWS credentials
3. Creates S3 bucket (with unique name)
4. Uploads your dataset (takes 5-10 minutes)
5. Verifies upload
6. Saves bucket name for later use

**Or do it manually:**

#### 3.1a Create S3 Bucket

```bash
# Create unique bucket name
BUCKET_NAME="room-detection-training-$(date +%s)"

# Create bucket
aws s3 mb s3://$BUCKET_NAME --region us-east-1

# Save bucket name
echo $BUCKET_NAME > ml/sagemaker_bucket_name.txt
```

#### 3.1b Upload Dataset

```bash
# Get bucket name
BUCKET_NAME=$(cat ml/sagemaker_bucket_name.txt)

# Upload dataset
aws s3 sync ml/datasets/yolo_format/ \
  s3://$BUCKET_NAME/yolo_format/ \
  --exclude "*.gitkeep" \
  --exclude ".DS_Store"
```

**This takes 5-10 minutes for 3.1 GB**

#### 3.1c Verify Upload

```bash
# Check training images
aws s3 ls s3://$BUCKET_NAME/yolo_format/images/train/ | wc -l
# Should show ~4195

# Check validation images
aws s3 ls s3://$BUCKET_NAME/yolo_format/images/val/ | wc -l
# Should show ~400
```

---

## Step 4: Create IAM Role for SageMaker

### 4.1 Create Role via AWS Console

1. **Go to IAM:** https://console.aws.amazon.com/iam
2. **Click "Roles"** (left sidebar)
3. **Click "Create role"**
4. **Select "AWS service"**
5. **Select "SageMaker"** → Click "Next"
6. **Attach policies:**
   - Search and select: `AmazonSageMakerFullAccess`
   - Search and select: `AmazonS3FullAccess` (or create custom policy for your bucket only)
   - Click "Next"
7. **Role name:** `SageMakerTrainingRole`
8. **Description:** `Role for YOLOv8 training jobs`
9. **Click "Create role"**

### 4.2 Get Role ARN

1. **Click on the role** you just created (`SageMakerTrainingRole`)
2. **Copy the "ARN"** (looks like: `arn:aws:iam::123456789012:role/SageMakerTrainingRole`)
3. **Save it:**

```bash
# Replace with your actual ARN
echo "arn:aws:iam::YOUR_ACCOUNT_ID:role/SageMakerTrainingRole" > ml/sagemaker_role_arn.txt
```

**Or get it automatically:**
```bash
# Get your account ID
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

# Save role ARN
echo "arn:aws:iam::${ACCOUNT_ID}:role/SageMakerTrainingRole" > ml/sagemaker_role_arn.txt
```

---

## Step 5: Install SageMaker SDK

```bash
cd "/Users/dohoonkim/GauntletAI/Room Detection"
source backend/venv/bin/activate
pip install sagemaker boto3
```

---

## Step 6: Launch Training Job

### 6.1 Quick Start (Recommended)

```bash
# Get bucket name
BUCKET_NAME=$(cat ml/sagemaker_bucket_name.txt)

# Launch training with Spot instances (cheapest)
python ml/sagemaker_scripts/launch_training.py \
  --bucket $BUCKET_NAME \
  --spot \
  --epochs 50 \
  --instance-type ml.g4dn.xlarge
```

**What this does:**
- Uploads training script to S3
- Creates SageMaker training job
- Uses Spot instances (70-90% cheaper)
- Trains for 50 epochs
- Monitors progress

### 6.2 Options Explained

```bash
python ml/sagemaker_scripts/launch_training.py \
  --bucket YOUR_BUCKET_NAME \          # S3 bucket with dataset
  --spot \                             # Use Spot (cheaper) or omit for on-demand
  --epochs 50 \                        # Number of epochs
  --instance-type ml.g4dn.xlarge \     # Instance type
  --imgsz 1024 \                       # Image size
  --batch 8 \                          # Batch size
  --model yolov8n-seg.pt \             # Model size
  --download                           # Download model when done
```

**Instance types:**
- `ml.g4dn.xlarge` - Cheapest GPU (~$0.20/hour spot)
- `ml.g4dn.2xlarge` - More memory (~$0.30/hour spot)
- `ml.p3.2xlarge` - Faster GPU (~$0.60/hour spot)

### 6.3 Monitor Training

**Option 1: Watch in terminal**
- The script will show progress if you don't use `--no-wait`

**Option 2: AWS Console**
- Go to: https://console.aws.amazon.com/sagemaker
- Click "Training jobs"
- Click your job name
- View logs, metrics, and status

**Option 3: AWS CLI**
```bash
# Get job name from script output, then:
aws sagemaker describe-training-job --training-job-name YOUR_JOB_NAME

# View logs
aws logs tail /aws/sagemaker/TrainingJobs/YOUR_JOB_NAME --follow
```

---

## Step 7: Download Trained Model

### 7.1 After Training Completes

**If you used `--download` flag:**
- Model automatically downloads to `ml/models/sagemaker/`

**Manual download:**

```bash
# Get job name (from training output or console)
JOB_NAME="your-training-job-name"

# Get model location
MODEL_URI=$(aws sagemaker describe-training-job \
  --training-job-name $JOB_NAME \
  --query 'ModelArtifacts.S3ModelArtifacts' \
  --output text)

# Download model
aws s3 cp $MODEL_URI ml/models/sagemaker_model.tar.gz

# Extract
cd ml/models
tar -xzf sagemaker_model.tar.gz
```

### 7.2 Use the Model

The model will be in `ml/models/` directory. You can use it with:

```bash
python ml/scripts/extract_polygons.py \
  --model ml/models/best.pt \
  --image path/to/floorplan.png \
  --output ml/results/results.json
```

---

## Step 8: Clean Up (Optional)

### 8.1 Delete S3 Data (Save Storage Costs)

```bash
# Get bucket name
BUCKET_NAME=$(cat ml/sagemaker_bucket_name.txt)

# Delete dataset (optional - only if you don't need it)
aws s3 rm s3://$BUCKET_NAME/yolo_format/ --recursive

# Delete training outputs (optional)
aws s3 rm s3://$BUCKET_NAME/training-output/ --recursive

# Delete bucket (optional - only if empty)
aws s3 rb s3://$BUCKET_NAME
```

**Storage costs:**
- ~$0.023/GB/month
- 3.1 GB = ~$0.07/month
- Delete if you don't need it anymore

---

## 🎯 Complete Example Workflow

Here's the complete workflow from start to finish:

```bash
# 1. Setup AWS (one-time)
aws configure

# 2. Upload dataset
bash ml/sagemaker_scripts/setup_and_upload.sh

# 3. Get bucket name
BUCKET_NAME=$(cat ml/sagemaker_bucket_name.txt)

# 4. Launch training
python ml/sagemaker_scripts/launch_training.py \
  --bucket $BUCKET_NAME \
  --spot \
  --epochs 50 \
  --download

# 5. Wait for completion (2-3 hours)

# 6. Model is in ml/models/sagemaker/
```

---

## 📊 Monitoring Training

### View Training Metrics

**In AWS Console:**
1. Go to SageMaker → Training jobs
2. Click your job
3. View "Metrics" tab
4. See loss curves, mAP, etc.

**Via CLI:**
```bash
# Get job status
aws sagemaker describe-training-job \
  --training-job-name YOUR_JOB_NAME \
  --query 'TrainingJobStatus'

# Get latest metrics
aws sagemaker describe-training-job \
  --training-job-name YOUR_JOB_NAME \
  --query 'FinalMetricDataList'
```

---

## 💰 Cost Tracking

### Check Current Costs

```bash
# View training job costs (approximate)
aws sagemaker describe-training-job \
  --training-job-name YOUR_JOB_NAME \
  --query '[TrainingStartTime, TrainingEndTime, ResourceConfig.InstanceType]'
```

**Or in AWS Console:**
- Go to Cost Explorer
- Filter by SageMaker service
- See actual costs

---

## 🐛 Troubleshooting

### Issue: "Access Denied"
**Solution:** Check IAM role has correct permissions

### Issue: "Bucket not found"
**Solution:** Verify bucket name: `cat ml/sagemaker_bucket_name.txt`

### Issue: "Training job failed"
**Solution:** Check CloudWatch logs for error details

### Issue: "Spot instance interrupted"
**Solution:** Normal for Spot - job will resume automatically

---

## ✅ Success Checklist

After training completes, you should have:
- [ ] Trained model in `ml/models/sagemaker/`
- [ ] Training metrics/logs in CloudWatch
- [ ] Model artifacts in S3
- [ ] Cost: ~$0.50-$2.00

---

## 📚 Next Steps

1. **Test the model:**
   ```bash
   python ml/scripts/extract_polygons.py \
     --model ml/models/sagemaker/best.pt \
     --image path/to/test.png \
     --output ml/results/test.json
   ```

2. **Compare with local training:**
   - Check accuracy metrics
   - Compare training time
   - Evaluate cost vs. time saved

3. **Integrate into your app:**
   - Use model in FastAPI backend
   - Create inference endpoint
   - Deploy to production

---

**Ready to start? Begin with Step 1!** 🚀

