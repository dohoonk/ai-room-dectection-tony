# AWS S3 Setup Guide

This guide walks you through setting up AWS S3 for PDF and image file storage, which is required for AWS services (Textract, Rekognition) to access files.

## Prerequisites

- AWS Account
- AWS CLI installed and configured (optional, but helpful)
- Access to AWS Console

---

## Step 1: Create S3 Bucket

### In AWS Console:

1. **Navigate to S3**:
   - Go to [AWS Console](https://console.aws.amazon.com/)
   - Search for "S3" or navigate to **Services → Storage → S3**

2. **Create Bucket**:
   - Click **"Create bucket"**
   #room-detection-blueprints-tony-gauntlet
   - **Bucket name**: `room-detection-blueprints` (or your preferred name)
     - ⚠️ Bucket names must be globally unique across all AWS accounts
     - Use lowercase letters, numbers, hyphens only
     - Example: `room-detection-blueprints-{your-account-id}`
   
3. **Choose AWS Region**:
   - Select the same region where you'll deploy your services
   - Recommended: `us-east-1` (N. Virginia) or your preferred region
   - **Note**: Keep this consistent across all AWS services

4. **Object Ownership**:
   - Select **"ACLs disabled (recommended)"**
   - This is the modern default

5. **Block Public Access**:
   - ✅ **Keep all settings checked** (block all public access)
   - Files should only be accessible via IAM roles

6. **Bucket Versioning**:
   - **Disable** for now (can enable later if needed)

7. **Default Encryption**:
   - ✅ **Enable**
   - Choose **"Amazon S3 managed keys (SSE-S3)"** (simplest option)

8. **Advanced Settings**:
   - Leave defaults for now

9. **Create Bucket**:
   - Click **"Create bucket"**
   - ✅ Bucket created!

---

## Step 2: Create IAM User for Application

### In AWS Console:

1. **Navigate to IAM**:
   - Go to **Services → Security, Identity & Compliance → IAM**

2. **Create User**:
   - Click **"Users"** in left sidebar
   - Click **"Create user"**

3. **User Details**:
#room-detection-service-tony
   - **User name**: `room-detection-service`
   - **AWS credential type**: Select **"Access key - Programmatic access"**
   - Click **"Next"**

4. **Set Permissions**:
   - Select **"Attach policies directly"**
   - We'll create a custom policy in the next step
   - Click **"Next"** for now

5. **Review and Create**:
   - Click **"Create user"**
   - ⚠️ **IMPORTANT**: Copy the **Access Key ID** and **Secret Access Key**
   - Store these securely - you'll need them for the application
   - You can download the CSV file

---

## Step 3: Create IAM Policy for S3 Access

### In AWS Console:

1. **Navigate to Policies**:
   - In IAM, click **"Policies"** in left sidebar
   - Click **"Create policy"**

2. **Use JSON Editor**:
   - Click **"JSON"** tab
   - Paste the following policy (replace `YOUR-BUCKET-NAME` with your actual bucket name):

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "AllowS3Upload",
            "Effect": "Allow",
            "Action": [
                "s3:PutObject",
                "s3:PutObjectAcl"
            ],
            "Resource": "arn:aws:s3:::YOUR-BUCKET-NAME/*"
        },
        {
            "Sid": "AllowS3Read",
            "Effect": "Allow",
            "Action": [
                "s3:GetObject"
            ],
            "Resource": "arn:aws:s3:::YOUR-BUCKET-NAME/*"
        },
        {
            "Sid": "AllowS3List",
            "Effect": "Allow",
            "Action": [
                "s3:ListBucket"
            ],
            "Resource": "arn:aws:s3:::YOUR-BUCKET-NAME"
        },
        {
            "Sid": "AllowS3Delete",
            "Effect": "Allow",
            "Action": [
                "s3:DeleteObject"
            ],
            "Resource": "arn:aws:s3:::YOUR-BUCKET-NAME/*"
        }
    ]
}
```

3. **Policy Details**:
   - **Policy name**: `RoomDetectionS3Access`
   - **Description**: "Allows S3 access for room detection service"
   - Click **"Create policy"**

4. **Attach Policy to User**:
   - Go back to **"Users"**
   - Click on `room-detection-service` user
   - Click **"Add permissions"** → **"Attach policies directly"**
   - Search for `RoomDetectionS3Access`
   - ✅ Check the box
   - Click **"Next"** → **"Add permissions"**

---

## Step 4: Create IAM Role for AWS Services (Textract, Rekognition)

AWS services (Textract, Rekognition) need permission to read from S3. We'll create a role for this.

### In AWS Console:

1. **Navigate to Roles**:
   - In IAM, click **"Roles"** in left sidebar
   - Click **"Create role"**

2. **Trusted Entity Type**:
   - Select **"AWS service"**

3. **Use Case**:
   - Select **"Text"** → **"Textract"**
   - Click **"Next"**

4. **Add Permissions**:
   - Search for `AmazonS3ReadOnlyAccess`
   - ✅ Check the box
   - Click **"Next"**

5. **Role Details**:
   - **Role name**: `RoomDetectionTextractRole`
   - **Description**: "Allows Textract to read from S3 bucket"
   - Click **"Create role"**

6. **Repeat for Rekognition**:
   - Create another role: `RoomDetectionRekognitionRole`
   - Same permissions: `AmazonS3ReadOnlyAccess`
   - Use case: **"Machine learning"** → **"Rekognition"**

---

## Step 5: Update S3 Bucket Policy (Optional - for Service Access)

If you want Textract/Rekognition to access files directly, you can add a bucket policy.

### In AWS Console:

1. **Navigate to S3 Bucket**:
   - Go to your bucket: `room-detection-blueprints`
   - Click on **"Permissions"** tab
   - Scroll to **"Bucket policy"**

2. **Add Bucket Policy** (Optional):
   - Click **"Edit"**
   - Add policy (replace `YOUR-BUCKET-NAME` and `YOUR-ACCOUNT-ID`):

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "AllowTextractAccess",
            "Effect": "Allow",
            "Principal": {
                "Service": "textract.amazonaws.com"
            },
            "Action": [
                "s3:GetObject"
            ],
            "Resource": "arn:aws:s3:::YOUR-BUCKET-NAME/*"
        },
        {
            "Sid": "AllowRekognitionAccess",
            "Effect": "Allow",
            "Principal": {
                "Service": "rekognition.amazonaws.com"
            },
            "Action": [
                "s3:GetObject"
            ],
            "Resource": "arn:aws:s3:::YOUR-BUCKET-NAME/*"
        }
    ]
}
```

3. **Save**:
   - Click **"Save changes"**

---

## Step 6: Configure Environment Variables

### In Your Project:

1. **Update `.env` file** (for local development):
   ```bash
   AWS_ACCESS_KEY_ID=your-access-key-id
   AWS_SECRET_ACCESS_KEY=your-secret-access-key
   AWS_REGION=us-east-1
   AWS_S3_BUCKET_NAME=room-detection-blueprints
   ```

2. **Update `.cursor/mcp.json`** (for MCP/Cursor):
   ```json
   {
     "env": {
       "AWS_ACCESS_KEY_ID": "your-access-key-id",
       "AWS_SECRET_ACCESS_KEY": "your-secret-access-key",
       "AWS_REGION": "us-east-1",
       "AWS_S3_BUCKET_NAME": "room-detection-blueprints"
     }
   }
   ```

---

## Step 7: Test S3 Connection

After implementing the code, test with:

```python
# Test script
import boto3
from botocore.exceptions import ClientError

s3 = boto3.client('s3',
    aws_access_key_id='your-key',
    aws_secret_access_key='your-secret',
    region_name='us-east-1'
)

try:
    response = s3.list_buckets()
    print("✅ S3 connection successful!")
    print(f"Buckets: {[b['Name'] for b in response['Buckets']]}")
except ClientError as e:
    print(f"❌ Error: {e}")
```

---

## Summary Checklist

- [ ] S3 bucket created: `room-detection-blueprints`
- [ ] IAM user created: `room-detection-service`
- [ ] IAM policy created: `RoomDetectionS3Access`
- [ ] Policy attached to user
- [ ] Access keys saved securely
- [ ] IAM roles created for Textract and Rekognition
- [ ] Bucket policy added (optional)
- [ ] Environment variables configured
- [ ] S3 connection tested

---

## Security Best Practices

1. **Never commit AWS credentials to Git**
   - Use `.env` file (already in `.gitignore`)
   - Use environment variables in production

2. **Use IAM roles in production**
   - For Lambda/ECS, use IAM roles instead of access keys
   - More secure than storing credentials

3. **Limit permissions**
   - Only grant minimum required permissions
   - Use bucket-specific policies

4. **Enable CloudTrail** (optional)
   - Monitor S3 access for security auditing

---

## Cost Considerations

- **S3 Storage**: ~$0.023 per GB/month (first 50 TB)
- **PUT requests**: $0.005 per 1,000 requests
- **GET requests**: $0.0004 per 1,000 requests
- **Data transfer**: Free within same region

For MVP/testing: Costs should be minimal (< $1/month for testing)

---

## Next Steps

After completing AWS console setup:
1. Install `boto3` Python library
2. Implement S3 upload/download functions
3. Test file upload
4. Integrate with PDF processing pipeline

