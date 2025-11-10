# Quick Deployment Guide

## 🚀 Automated Deployment

I've created an automated deployment script that handles most of the deployment process.

### Run Deployment

```bash
cd "/Users/dohoonkim/GauntletAI/Room Detection"
./deploy.sh
```

**What it does:**
1. ✅ Builds frontend production bundle
2. ✅ Creates/verifies S3 buckets
3. ✅ Uploads frontend to S3
4. ✅ Uploads ML model to S3
5. ✅ Builds and pushes Docker image to ECR
6. ✅ Creates deployment summary

---

## 📋 What You'll Need to Do Manually

After running the script, you'll need to:

### 1. Set Up ECS (Backend)

The script creates the Docker image, but you need to:
- Create ECS cluster
- Create ECS task definition
- Create ECS service
- Set up Application Load Balancer

**Quick ECS Setup:**

```bash
# Create ECS cluster
aws ecs create-cluster --cluster-name room-detection-cluster

# Register task definition (update image URI from deployment-info.txt)
aws ecs register-task-definition --cli-input-json file://ecs-task-definition.json

# Create service
aws ecs create-service \
  --cluster room-detection-cluster \
  --service-name room-detection-backend \
  --task-definition room-detection-backend \
  --desired-count 1 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-xxx],securityGroups=[sg-xxx],assignPublicIp=ENABLED}"
```

### 2. Set Up CloudFront (Optional but Recommended)

1. Go to AWS Console → CloudFront
2. Create distribution
3. Origin: Your frontend S3 bucket
4. Enable HTTPS
5. Note the CloudFront URL

### 3. Configure Environment Variables

Update ECS task definition with:
- `AWS_REGION`
- `AWS_S3_BUCKET_NAME`
- `ML_MODEL_PATH` (S3 path to model)

---

## 🎯 Quick Deploy Commands

### Full Automated Deploy
```bash
./deploy.sh
```

### Just Build Frontend
```bash
cd frontend
npm run build
```

### Just Upload Frontend
```bash
cd frontend
aws s3 sync build/ s3://room-detection-frontend-<account-id>/ --delete
```

### Just Build Docker
```bash
cd backend
docker build -t room-detection-backend .
```

---

## 📊 After Deployment

Check `deployment-info.txt` for:
- S3 bucket names
- ECR image URI
- Frontend URL
- Next steps

---

## 🆘 Troubleshooting

**"Bucket already exists"**
- The script will use existing buckets or create new ones

**"Docker not found"**
- Install Docker Desktop
- Or skip Docker step and deploy manually

**"ECR login failed"**
- Check AWS credentials: `aws sts get-caller-identity`
- Verify IAM permissions for ECR

---

**Ready to deploy?** Run `./deploy.sh` and follow the prompts!

