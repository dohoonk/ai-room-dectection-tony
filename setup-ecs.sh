#!/bin/bash
# Setup ECS for Room Detection Backend
# Run this after deploy.sh to set up the backend service

set -e

echo "="*70
echo "🚀 Setting up ECS for Room Detection Backend"
echo "="*70
echo

REGION=${AWS_REGION:-us-east-1}
CLUSTER_NAME="room-detection-cluster"
SERVICE_NAME="room-detection-backend"
TASK_DEFINITION="room-detection-backend"

# Step 1: Create CloudWatch log group
echo "📋 Step 1: Creating CloudWatch log group..."
aws logs create-log-group --log-group-name "/ecs/room-detection-backend" --region "$REGION" 2>/dev/null || echo "   Log group already exists"
echo "✅ CloudWatch log group ready"
echo

# Step 2: Create ECS cluster
echo "📋 Step 2: Creating ECS cluster..."
if aws ecs describe-clusters --clusters "$CLUSTER_NAME" --region "$REGION" --query 'clusters[0].status' --output text 2>/dev/null | grep -q "ACTIVE"; then
    echo "✅ Cluster already exists: $CLUSTER_NAME"
else
    aws ecs create-cluster --cluster-name "$CLUSTER_NAME" --region "$REGION"
    echo "✅ Cluster created: $CLUSTER_NAME"
fi
echo

# Step 3: Get default VPC and subnets
echo "📋 Step 3: Getting VPC and subnet information..."
VPC_ID=$(aws ec2 describe-vpcs --filters "Name=isDefault,Values=true" --query 'Vpcs[0].VpcId' --output text --region "$REGION")
SUBNET_IDS=$(aws ec2 describe-subnets --filters "Name=vpc-id,Values=$VPC_ID" --query 'Subnets[*].SubnetId' --output text --region "$REGION" | tr '\t' ',')

# Get first subnet for single subnet (Fargate needs at least 2 subnets in different AZs)
SUBNET_LIST=($(echo $SUBNET_IDS | tr ',' ' '))
if [ ${#SUBNET_LIST[@]} -lt 2 ]; then
    echo "⚠️  Warning: Need at least 2 subnets in different AZs for Fargate"
    echo "   Using available subnets: $SUBNET_IDS"
else
    # Use first 2 subnets
    SUBNET_IDS="${SUBNET_LIST[0]},${SUBNET_LIST[1]}"
fi

# Get default security group
SG_ID=$(aws ec2 describe-security-groups --filters "Name=vpc-id,Values=$VPC_ID" "Name=group-name,Values=default" --query 'SecurityGroups[0].GroupId' --output text --region "$REGION")

echo "   VPC: $VPC_ID"
echo "   Subnets: $SUBNET_IDS"
echo "   Security Group: $SG_ID"
echo

# Step 4: Register task definition
echo "📋 Step 4: Registering ECS task definition..."
if [ -f "ecs-task-definition.json" ]; then
    aws ecs register-task-definition --cli-input-json file://ecs-task-definition.json --region "$REGION"
    echo "✅ Task definition registered"
else
    echo "❌ ecs-task-definition.json not found"
    echo "   Please create it first (see DEPLOYMENT_GUIDE.md)"
    exit 1
fi
echo

# Step 5: Create ECS service
echo "📋 Step 5: Creating ECS service..."
if aws ecs describe-services --cluster "$CLUSTER_NAME" --services "$SERVICE_NAME" --region "$REGION" --query 'services[0].status' --output text 2>/dev/null | grep -q "ACTIVE"; then
    echo "✅ Service already exists: $SERVICE_NAME"
    echo "   Updating service..."
    aws ecs update-service \
        --cluster "$CLUSTER_NAME" \
        --service "$SERVICE_NAME" \
        --task-definition "$TASK_DEFINITION" \
        --region "$REGION" > /dev/null
    echo "✅ Service updated"
else
    aws ecs create-service \
        --cluster "$CLUSTER_NAME" \
        --service-name "$SERVICE_NAME" \
        --task-definition "$TASK_DEFINITION" \
        --desired-count 1 \
        --launch-type FARGATE \
        --network-configuration "awsvpcConfiguration={subnets=[$SUBNET_IDS],securityGroups=[$SG_ID],assignPublicIp=ENABLED}" \
        --region "$REGION"
    echo "✅ Service created: $SERVICE_NAME"
fi
echo

# Step 6: Wait for service to stabilize
echo "📋 Step 6: Waiting for service to start..."
echo "   This may take 2-3 minutes..."
aws ecs wait services-stable --cluster "$CLUSTER_NAME" --services "$SERVICE_NAME" --region "$REGION"
echo "✅ Service is running"
echo

# Get task IP
echo "📋 Step 7: Getting service information..."
TASK_ARN=$(aws ecs list-tasks --cluster "$CLUSTER_NAME" --service-name "$SERVICE_NAME" --region "$REGION" --query 'taskArns[0]' --output text)
if [ "$TASK_ARN" != "None" ] && [ -n "$TASK_ARN" ]; then
    TASK_IP=$(aws ecs describe-tasks --cluster "$CLUSTER_NAME" --tasks "$TASK_ARN" --region "$REGION" --query 'tasks[0].attachments[0].details[?name==`networkInterfaceId`].value' --output text | xargs -I {} aws ec2 describe-network-interfaces --network-interface-ids {} --region "$REGION" --query 'NetworkInterfaces[0].Association.PublicIp' --output text)
    
    echo "✅ Backend is running"
    echo "   Task ARN: $TASK_ARN"
    if [ -n "$TASK_IP" ] && [ "$TASK_IP" != "None" ]; then
        echo "   Public IP: $TASK_IP"
        echo "   API URL: http://$TASK_IP:8000"
        echo "   Health check: http://$TASK_IP:8000/health"
    else
        echo "   ⚠️  Public IP not available (may be in private subnet)"
    fi
else
    echo "   ⚠️  No tasks running yet"
fi
echo

echo "="*70
echo "✅ ECS Setup Complete!"
echo "="*70
echo
echo "📝 Next steps:"
echo "   1. Set up Application Load Balancer (recommended)"
echo "   2. Update frontend API URL to point to backend"
echo "   3. Configure CloudFront for frontend"
echo
echo "💡 To check service status:"
echo "   aws ecs describe-services --cluster $CLUSTER_NAME --services $SERVICE_NAME --region $REGION"
echo

