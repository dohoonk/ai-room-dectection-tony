#!/bin/bash
# Automated Deployment Script for Room Detection AI
# This script automates the deployment process to AWS

set -e  # Exit on error

echo "="*70
echo "🚀 Room Detection AI - Automated Deployment"
echo "="*70
echo

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REGION=${AWS_REGION:-us-east-1}
AWS_ACCOUNT=$(aws sts get-caller-identity --query Account --output text)

# Get existing bucket name if available
if [ -f "$PROJECT_ROOT/ml/sagemaker_bucket_name.txt" ]; then
    TRAINING_BUCKET=$(cat "$PROJECT_ROOT/ml/sagemaker_bucket_name.txt")
else
    TRAINING_BUCKET=""
fi

# Check prerequisites
echo "📋 Checking prerequisites..."
if ! command -v aws &> /dev/null; then
    echo -e "${RED}❌ AWS CLI not found${NC}"
    exit 1
fi

if ! aws sts get-caller-identity &> /dev/null; then
    echo -e "${RED}❌ AWS credentials not configured${NC}"
    exit 1
fi

echo -e "${GREEN}✅ AWS CLI configured${NC}"
echo "   Account: $AWS_ACCOUNT"
echo "   Region: $REGION"
echo

# Step 1: Build Frontend
echo "📦 Step 1: Building frontend..."
cd "$PROJECT_ROOT/frontend"

if [ ! -d "node_modules" ]; then
    echo "   Installing dependencies..."
    npm install
fi

echo "   Building production bundle..."
npm run build

if [ ! -d "build" ]; then
    echo -e "${RED}❌ Build failed - build/ directory not found${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Frontend built successfully${NC}"
echo

# Step 2: Create/Check S3 Buckets
echo "📦 Step 2: Setting up S3 buckets..."

# Frontend bucket
FRONTEND_BUCKET="room-detection-frontend-${AWS_ACCOUNT}"
echo "   Checking frontend bucket: $FRONTEND_BUCKET"

if aws s3 ls "s3://${FRONTEND_BUCKET}" 2>/dev/null; then
    echo -e "${GREEN}✅ Frontend bucket exists${NC}"
else
    echo "   Creating frontend bucket..."
    aws s3 mb "s3://${FRONTEND_BUCKET}" --region "$REGION"
    
    # Enable static website hosting
    aws s3 website "s3://${FRONTEND_BUCKET}" \
        --index-document index.html \
        --error-document index.html
    
    echo -e "${GREEN}✅ Frontend bucket created${NC}"
fi

# Backend bucket (for file storage)
BACKEND_BUCKET="room-detection-blueprints-${AWS_ACCOUNT}"
echo "   Checking backend bucket: $BACKEND_BUCKET"

if aws s3 ls "s3://${BACKEND_BUCKET}" 2>/dev/null; then
    echo -e "${GREEN}✅ Backend bucket exists${NC}"
else
    echo "   Creating backend bucket..."
    aws s3 mb "s3://${BACKEND_BUCKET}" --region "$REGION"
    echo -e "${GREEN}✅ Backend bucket created${NC}"
fi

# Models bucket
MODELS_BUCKET="room-detection-models-${AWS_ACCOUNT}"
echo "   Checking models bucket: $MODELS_BUCKET"

if aws s3 ls "s3://${MODELS_BUCKET}" 2>/dev/null; then
    echo -e "${GREEN}✅ Models bucket exists${NC}"
else
    echo "   Creating models bucket..."
    aws s3 mb "s3://${MODELS_BUCKET}" --region "$REGION"
    echo -e "${GREEN}✅ Models bucket created${NC}"
fi

echo

# Step 3: Upload Frontend to S3
echo "📤 Step 3: Uploading frontend to S3..."
cd "$PROJECT_ROOT/frontend"

aws s3 sync build/ "s3://${FRONTEND_BUCKET}/" --delete

echo -e "${GREEN}✅ Frontend uploaded to S3${NC}"
echo "   URL: http://${FRONTEND_BUCKET}.s3-website-${REGION}.amazonaws.com"
echo

# Step 4: Upload ML Model to S3
echo "📤 Step 4: Uploading ML model to S3..."

MODEL_PATH="$PROJECT_ROOT/ml/models/sagemaker/train/weights/best.pt"
if [ -f "$MODEL_PATH" ]; then
    echo "   Uploading model: $MODEL_PATH"
    aws s3 cp "$MODEL_PATH" "s3://${MODELS_BUCKET}/best.pt"
    echo -e "${GREEN}✅ Model uploaded${NC}"
else
    echo -e "${YELLOW}⚠️  Model not found at $MODEL_PATH${NC}"
    echo "   Skipping model upload"
fi
echo

# Step 5: Build Docker Image
echo "🐳 Step 5: Building Docker image for backend..."

cd "$PROJECT_ROOT/backend"

# Check if Docker is available
if ! command -v docker &> /dev/null; then
    echo -e "${YELLOW}⚠️  Docker not found - skipping Docker build${NC}"
    echo "   You can build manually later with: docker build -t room-detection-backend ."
else
    ECR_REPO="room-detection-backend"
    ECR_URI="${AWS_ACCOUNT}.dkr.ecr.${REGION}.amazonaws.com/${ECR_REPO}"
    
    echo "   Building image..."
    docker build -t room-detection-backend .
    
    echo "   Checking ECR repository..."
    if aws ecr describe-repositories --repository-names "$ECR_REPO" &>/dev/null; then
        echo -e "${GREEN}✅ ECR repository exists${NC}"
    else
        echo "   Creating ECR repository..."
        aws ecr create-repository --repository-name "$ECR_REPO" --region "$REGION"
        echo -e "${GREEN}✅ ECR repository created${NC}"
    fi
    
    echo "   Logging in to ECR..."
    aws ecr get-login-password --region "$REGION" | \
        docker login --username AWS --password-stdin "$ECR_URI"
    
    echo "   Tagging image..."
    docker tag room-detection-backend:latest "${ECR_URI}:latest"
    
    echo "   Pushing image to ECR..."
    docker push "${ECR_URI}:latest"
    
    echo -e "${GREEN}✅ Docker image pushed to ECR${NC}"
    echo "   Image URI: ${ECR_URI}:latest"
fi
echo

# Step 6: Create deployment summary
echo "📋 Step 6: Creating deployment summary..."

DEPLOYMENT_INFO="$PROJECT_ROOT/deployment-info.txt"
cat > "$DEPLOYMENT_INFO" << EOF
Room Detection AI - Deployment Information
Generated: $(date)

AWS Account: ${AWS_ACCOUNT}
Region: ${REGION}

S3 Buckets:
- Frontend: ${FRONTEND_BUCKET}
  URL: http://${FRONTEND_BUCKET}.s3-website-${REGION}.amazonaws.com
  
- Backend Storage: ${BACKEND_BUCKET}
  
- Models: ${MODELS_BUCKET}
  Model: s3://${MODELS_BUCKET}/best.pt

Docker:
- ECR Repository: ${ECR_REPO:-room-detection-backend}
- Image URI: ${ECR_URI:-${AWS_ACCOUNT}.dkr.ecr.${REGION}.amazonaws.com/room-detection-backend}:latest

Next Steps:
1. Set up CloudFront distribution for frontend (optional but recommended)
2. Create ECS cluster and service for backend
3. Set up Application Load Balancer
4. Configure environment variables in ECS task definition
5. Set up custom domain (optional)

See DEPLOYMENT_GUIDE.md for detailed instructions.
EOF

echo -e "${GREEN}✅ Deployment summary saved to: deployment-info.txt${NC}"
echo

# Final summary
echo "="*70
echo -e "${GREEN}✅ Deployment Complete!${NC}"
echo "="*70
echo
echo "📊 Summary:"
echo "   ✅ Frontend built and uploaded to S3"
echo "   ✅ S3 buckets created/verified"
echo "   ✅ ML model uploaded (if available)"
echo "   ✅ Docker image built and pushed (if Docker available)"
echo
echo "🌐 Access your frontend:"
echo "   http://${FRONTEND_BUCKET}.s3-website-${REGION}.amazonaws.com"
echo
echo "📝 Next steps:"
echo "   1. Review deployment-info.txt"
echo "   2. Set up ECS service (see DEPLOYMENT_GUIDE.md)"
echo "   3. Configure CloudFront for better performance"
echo "   4. Set up custom domain (optional)"
echo

