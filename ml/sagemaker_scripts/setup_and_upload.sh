#!/bin/bash
# Setup and Upload Dataset to S3 for SageMaker Training

set -e  # Exit on error

echo "="*60
echo "🚀 SageMaker Dataset Setup and Upload"
echo "="*60
echo

# Step 1: Check AWS CLI
echo "📋 Step 1: Checking AWS CLI..."
if ! command -v aws &> /dev/null; then
    echo "❌ AWS CLI not found. Install with: brew install awscli"
    exit 1
fi
echo "✅ AWS CLI found: $(aws --version)"
echo

# Step 2: Check AWS credentials
echo "📋 Step 2: Checking AWS credentials..."
if ! aws sts get-caller-identity &> /dev/null; then
    echo "❌ AWS credentials not configured."
    echo "   Run: aws configure"
    exit 1
fi
echo "✅ AWS credentials configured"
AWS_ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
echo "   Account: $AWS_ACCOUNT"
echo

# Step 3: Set region
REGION=${AWS_REGION:-us-east-1}
echo "📋 Step 3: Using region: $REGION"
echo

# Step 4: Create S3 bucket
echo "📋 Step 4: Creating S3 bucket..."
TIMESTAMP=$(date +%s)
BUCKET_NAME="room-detection-training-${TIMESTAMP}"
echo "   Bucket name: $BUCKET_NAME"

if aws s3 mb "s3://${BUCKET_NAME}" --region "$REGION" 2>/dev/null; then
    echo "✅ Bucket created: $BUCKET_NAME"
else
    echo "⚠️  Bucket might already exist or name taken. Trying alternative..."
    BUCKET_NAME="room-detection-training-${AWS_ACCOUNT}-${TIMESTAMP}"
    aws s3 mb "s3://${BUCKET_NAME}" --region "$REGION"
    echo "✅ Bucket created: $BUCKET_NAME"
fi

# Save bucket name
echo "$BUCKET_NAME" > ml/sagemaker_bucket_name.txt
echo "   Saved to: ml/sagemaker_bucket_name.txt"
echo

# Step 5: Upload dataset
echo "📋 Step 5: Uploading dataset to S3..."
echo "   This may take 5-10 minutes for 3.1 GB..."
echo

DATASET_PATH="ml/datasets/yolo_format"
if [ ! -d "$DATASET_PATH" ]; then
    echo "❌ Dataset not found at: $DATASET_PATH"
    echo "   Please run the conversion script first!"
    exit 1
fi

# Upload with progress
aws s3 sync "$DATASET_PATH" "s3://${BUCKET_NAME}/yolo_format/" \
    --exclude "*.gitkeep" \
    --exclude ".DS_Store" \
    --region "$REGION"

echo
echo "✅ Dataset uploaded!"
echo

# Step 6: Verify upload
echo "📋 Step 6: Verifying upload..."
TRAIN_IMAGES=$(aws s3 ls "s3://${BUCKET_NAME}/yolo_format/images/train/" --recursive | wc -l)
VAL_IMAGES=$(aws s3 ls "s3://${BUCKET_NAME}/yolo_format/images/val/" --recursive | wc -l)
TEST_IMAGES=$(aws s3 ls "s3://${BUCKET_NAME}/yolo_format/images/test/" --recursive | wc -l)

echo "   Training images: $TRAIN_IMAGES"
echo "   Validation images: $VAL_IMAGES"
echo "   Test images: $TEST_IMAGES"
echo

# Step 7: Summary
echo "="*60
echo "✅ Setup Complete!"
echo "="*60
echo "   Bucket: $BUCKET_NAME"
echo "   Dataset: s3://${BUCKET_NAME}/yolo_format/"
echo
echo "📋 Next steps:"
echo "   1. Set up IAM role (see SAGEMAKER_TRAINING_GUIDE.md)"
echo "   2. Run: python ml/sagemaker_scripts/launch_training.py \\"
echo "            --bucket $BUCKET_NAME \\"
echo "            --spot \\"
echo "            --epochs 50"
echo "="*60

