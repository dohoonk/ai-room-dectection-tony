# Deployment Guide

Complete guide for deploying Room Detection AI to production.

---

## 🎯 Deployment Options

### Option 1: AWS (Recommended - You're Already Using AWS)
- **Frontend**: S3 + CloudFront
- **Backend**: ECS Fargate or EC2
- **ML Model**: S3 + ECS/EC2
- **Best for**: Production, scalability, AWS integration

### Option 2: Docker + Cloud Provider
- **Frontend**: Docker container
- **Backend**: Docker container
- **ML Model**: Included in backend container
- **Best for**: Portability, any cloud provider

### Option 3: Serverless (AWS Lambda)
- **Frontend**: S3 + CloudFront
- **Backend**: Lambda + API Gateway
- **ML Model**: Lambda (with size limits)
- **Best for**: Cost-effective, low traffic

---

## 🚀 Option 1: AWS Deployment (Recommended)

### Architecture

```
┌─────────────┐
│   React     │  → S3 + CloudFront (CDN)
│  Frontend   │
└──────┬──────┘
       │
       ▼
┌─────────────────┐
│  API Gateway    │  → ECS Fargate (Backend)
│  or ALB         │
└──────┬──────────┘
       │
       ├──► S3 (File Storage)
       ├──► Textract/Rekognition (AWS Services)
       └──► ML Model (S3 or ECS)
```

### Step 1: Build Frontend for Production

```bash
cd frontend
npm run build
```

This creates a `build/` directory with optimized production files.

### Step 2: Deploy Frontend to S3 + CloudFront

#### 2.1 Create S3 Bucket for Frontend

```bash
# Create bucket
aws s3 mb s3://room-detection-frontend --region us-east-1

# Enable static website hosting
aws s3 website s3://room-detection-frontend \
  --index-document index.html \
  --error-document index.html
```

#### 2.2 Upload Frontend Build

```bash
cd frontend
aws s3 sync build/ s3://room-detection-frontend --delete
```

#### 2.3 Create CloudFront Distribution (Optional but Recommended)

1. Go to AWS Console → CloudFront
2. Create distribution
3. Origin: Your S3 bucket
4. Default root object: `index.html`
5. Enable HTTPS
6. Note the CloudFront URL

#### 2.4 Update Frontend API URL

Before building, update `frontend/src/services/api.ts`:

```typescript
const API_BASE_URL = process.env.REACT_APP_API_URL || 'https://your-api-domain.com';
```

Then rebuild:
```bash
npm run build
```

---

### Step 3: Deploy Backend to ECS Fargate

#### 3.1 Create Dockerfile

Create `backend/Dockerfile`:

```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/
COPY main.py .

# Copy ML model (if including in image)
# COPY ml/models/sagemaker/train/weights/best.pt ./ml/models/sagemaker/train/weights/

# Expose port
EXPOSE 8000

# Run application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### 3.2 Build and Push Docker Image to ECR

```bash
# Create ECR repository
aws ecr create-repository --repository-name room-detection-backend

# Get login token
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com

# Build image
cd backend
docker build -t room-detection-backend .

# Tag image
docker tag room-detection-backend:latest <account-id>.dkr.ecr.us-east-1.amazonaws.com/room-detection-backend:latest

# Push image
docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/room-detection-backend:latest
```

#### 3.3 Create ECS Task Definition

Create `ecs-task-definition.json`:

```json
{
  "family": "room-detection-backend",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "1024",
  "memory": "2048",
  "containerDefinitions": [
    {
      "name": "backend",
      "image": "<account-id>.dkr.ecr.us-east-1.amazonaws.com/room-detection-backend:latest",
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "AWS_REGION",
          "value": "us-east-1"
        },
        {
          "name": "AWS_S3_BUCKET_NAME",
          "value": "room-detection-blueprints-tony-gauntlet"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/room-detection-backend",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
```

#### 3.4 Register Task Definition

```bash
aws ecs register-task-definition --cli-input-json file://ecs-task-definition.json
```

#### 3.5 Create ECS Service

```bash
aws ecs create-service \
  --cluster room-detection-cluster \
  --service-name room-detection-backend \
  --task-definition room-detection-backend \
  --desired-count 1 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-xxx],securityGroups=[sg-xxx],assignPublicIp=ENABLED}"
```

#### 3.6 Create Application Load Balancer (ALB)

1. Create ALB in AWS Console
2. Configure target group pointing to ECS service
3. Set health check path: `/health`
4. Note the ALB DNS name

---

### Step 4: Deploy ML Model

#### Option A: Include in Docker Image (Small Models)

If model is < 500MB, include in Docker image:

```dockerfile
# In Dockerfile
COPY ml/models/sagemaker/train/weights/best.pt ./ml/models/sagemaker/train/weights/
```

#### Option B: Store in S3 (Recommended for Large Models)

1. Upload model to S3:
```bash
aws s3 cp ml/models/sagemaker/train/weights/best.pt \
  s3://room-detection-models/best.pt
```

2. Download at runtime in your application:
```python
# In backend/src/ml_room_detector.py
import boto3

def download_model_from_s3():
    s3 = boto3.client('s3')
    s3.download_file('room-detection-models', 'best.pt', '/tmp/model.pt')
    return '/tmp/model.pt'
```

---

### Step 5: Environment Variables

Set environment variables in ECS task definition or use AWS Systems Manager Parameter Store:

```bash
# Store secrets in Parameter Store
aws ssm put-parameter \
  --name "/room-detection/aws-access-key-id" \
  --value "your-key" \
  --type "SecureString"

aws ssm put-parameter \
  --name "/room-detection/aws-secret-access-key" \
  --value "your-secret" \
  --type "SecureString"
```

---

## 🐳 Option 2: Docker Deployment

### Step 1: Create Docker Compose

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - AWS_REGION=us-east-1
      - AWS_S3_BUCKET_NAME=room-detection-blueprints-tony-gauntlet
    volumes:
      - ./ml/models:/app/ml/models
    env_file:
      - .env

  frontend:
    build: ./frontend
    ports:
      - "3000:80"
    depends_on:
      - backend
    environment:
      - REACT_APP_API_URL=http://localhost:8000
```

### Step 2: Create Frontend Dockerfile

Create `frontend/Dockerfile`:

```dockerfile
FROM node:18-alpine as build

WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/build /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

### Step 3: Deploy

```bash
# Build and run
docker-compose up -d

# Or deploy to cloud provider (AWS ECS, Google Cloud Run, Azure Container Instances)
```

---

## ⚡ Option 3: Serverless (AWS Lambda)

### Limitations
- Lambda has 10GB max container size
- ML model might be too large
- 15-minute max execution time

### Step 1: Create Lambda Function

```python
# lambda_handler.py
import json
from src.ml_room_detector import MLRoomDetector

def lambda_handler(event, context):
    # Download model from S3 if needed
    # Process request
    # Return response
    pass
```

### Step 2: Package for Lambda

```bash
# Create deployment package
cd backend
pip install -r requirements.txt -t .
zip -r lambda-deployment.zip .
```

### Step 3: Deploy

```bash
aws lambda create-function \
  --function-name room-detection-api \
  --runtime python3.12 \
  --role arn:aws:iam::<account>:role/lambda-execution-role \
  --handler lambda_handler.lambda_handler \
  --zip-file fileb://lambda-deployment.zip \
  --timeout 900 \
  --memory-size 3008
```

---

## 🔧 Configuration

### Environment Variables

Create `.env.production`:

```bash
# AWS
AWS_REGION=us-east-1
AWS_S3_BUCKET_NAME=room-detection-blueprints-tony-gauntlet
AWS_ACCESS_KEY_ID=your-key
AWS_SECRET_ACCESS_KEY=your-secret

# API
API_URL=https://your-api-domain.com
FRONTEND_URL=https://your-frontend-domain.com

# ML Model
ML_MODEL_PATH=s3://room-detection-models/best.pt
# OR
ML_MODEL_PATH=/app/ml/models/sagemaker/train/weights/best.pt
```

---

## 📋 Deployment Checklist

### Pre-Deployment
- [ ] Build frontend: `cd frontend && npm run build`
- [ ] Test backend locally
- [ ] Update API URLs in frontend
- [ ] Set up AWS credentials
- [ ] Create S3 buckets
- [ ] Upload ML model to S3 (if using S3 storage)

### Backend Deployment
- [ ] Create Docker image
- [ ] Push to ECR (or Docker Hub)
- [ ] Create ECS task definition
- [ ] Create ECS service
- [ ] Set up ALB or API Gateway
- [ ] Configure environment variables
- [ ] Set up CloudWatch logging

### Frontend Deployment
- [ ] Build production bundle
- [ ] Upload to S3
- [ ] Configure CloudFront (optional)
- [ ] Set up custom domain (optional)
- [ ] Test CORS settings

### Post-Deployment
- [ ] Test API endpoints
- [ ] Test ML model loading
- [ ] Monitor CloudWatch logs
- [ ] Set up alerts
- [ ] Test file uploads
- [ ] Verify AWS service integration

---

## 🚨 Important Considerations

### ML Model Size
- **Current model**: ~6.5 MB (fits in Lambda)
- **If using larger models**: Use ECS/EC2 or S3 download

### CORS Configuration
Update `backend/main.py`:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://your-frontend-domain.com",
        "https://*.cloudfront.net"  # If using CloudFront
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Security
- Use IAM roles (not access keys) when possible
- Enable HTTPS everywhere
- Use AWS Secrets Manager for sensitive data
- Set up WAF for API Gateway

### Cost Optimization
- Use ECS Fargate Spot instances
- Use S3 Intelligent-Tiering
- Enable CloudFront caching
- Use Lambda for low-traffic scenarios

---

## 📚 Next Steps

1. **Choose deployment option** based on your needs
2. **Set up infrastructure** (S3, ECS, etc.)
3. **Deploy backend** first
4. **Deploy frontend** second
5. **Test thoroughly** before going live
6. **Monitor** with CloudWatch

---

## 🆘 Troubleshooting

### Backend won't start
- Check CloudWatch logs
- Verify environment variables
- Check IAM permissions
- Verify model path

### Frontend can't connect to backend
- Check CORS configuration
- Verify API URL in frontend
- Check security groups (if using VPC)
- Test backend health endpoint

### ML model not loading
- Verify model file exists
- Check file permissions
- Verify S3 bucket access (if using S3)
- Check model path in code

---

**Need help?** Check AWS documentation or review the Phase 2 transition plan in `PHASE2_TRANSITION_PLAN.md`.

