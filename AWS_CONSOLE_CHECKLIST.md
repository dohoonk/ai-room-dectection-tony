# AWS Console Setup Checklist

**Follow this checklist as we implement the code. Complete each step in AWS Console.**

## ✅ Step 1: Create S3 Bucket

**Location**: AWS Console → Services → S3

- [ ] Click "Create bucket"
- [ ] Bucket name: `room-detection-blueprints-{your-unique-id}`
  - ⚠️ Must be globally unique (add your account ID or random suffix)
- [ ] Region: `us-east-1` (or your preferred region)
- [ ] Object Ownership: "ACLs disabled (recommended)"
- [ ] Block Public Access: ✅ Keep all checked
- [ ] Bucket Versioning: Disable
- [ ] Default Encryption: ✅ Enable (SSE-S3)
- [ ] Click "Create bucket"

**Note**: Write down your bucket name - you'll need it for environment variables!

---

## ✅ Step 2: Create IAM User

**Location**: AWS Console → Services → IAM → Users

- [ ] Click "Create user"
- [ ] User name: `room-detection-service`
- [ ] AWS credential type: ✅ "Access key - Programmatic access"
- [ ] Click "Next"
- [ ] Click "Next" (we'll attach policy in next step)
- [ ] Click "Create user"
- [ ] ⚠️ **COPY AND SAVE**:
  - Access Key ID: `_________________`
  - Secret Access Key: `_________________`
  - Download CSV file (recommended)

**⚠️ CRITICAL**: Save these credentials securely. You won't see the secret key again!

---

## ✅ Step 3: Create IAM Policy

**Location**: AWS Console → IAM → Policies

- [ ] Click "Create policy"
- [ ] Click "JSON" tab
- [ ] Paste the policy (replace `YOUR-BUCKET-NAME` with your actual bucket name from Step 1):

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

- [ ] Click "Next"
- [ ] Policy name: `RoomDetectionS3Access`
- [ ] Description: "Allows S3 access for room detection service"
- [ ] Click "Create policy"

---

## ✅ Step 4: Attach Policy to User

**Location**: AWS Console → IAM → Users → room-detection-service

- [ ] Click on `room-detection-service` user
- [ ] Click "Add permissions" → "Attach policies directly"
- [ ] Search for: `RoomDetectionS3Access`
- [ ] ✅ Check the box
- [ ] Click "Next" → "Add permissions"

---

## ✅ Step 5: Create IAM Roles for AWS Services (Optional - for later)

**Location**: AWS Console → IAM → Roles

### For Textract:
- [ ] Click "Create role"
- [ ] Trusted entity: "AWS service"
- [ ] Use case: "Text" → "Textract"
- [ ] Click "Next"
- [ ] Search: `AmazonS3ReadOnlyAccess`
- [ ] ✅ Check the box
- [ ] Click "Next"
- [ ] Role name: `RoomDetectionTextractRole`
- [ ] Click "Create role"

### For Rekognition:
- [ ] Click "Create role"
- [ ] Trusted entity: "AWS service"
- [ ] Use case: "Machine learning" → "Rekognition"
- [ ] Click "Next"
- [ ] Search: `AmazonS3ReadOnlyAccess`
- [ ] ✅ Check the box
- [ ] Click "Next"
- [ ] Role name: `RoomDetectionRekognitionRole`
- [ ] Click "Create role"

---

## ✅ Step 6: Add Bucket Policy (Optional - for Service Access)

**Location**: AWS Console → S3 → Your Bucket → Permissions → Bucket policy

- [ ] Click "Edit"
- [ ] Add policy (replace `YOUR-BUCKET-NAME`):

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

- [ ] Click "Save changes"

---

## ✅ Step 7: Configure Environment Variables

**After completing Steps 1-4, configure your project:**

### Update `.env` file:
```bash
AWS_ACCESS_KEY_ID=your-access-key-from-step-2
AWS_SECRET_ACCESS_KEY=your-secret-key-from-step-2
AWS_REGION=us-east-1
AWS_S3_BUCKET_NAME=your-bucket-name-from-step-1
```

### Update `.cursor/mcp.json`:
Add to the `env` section:
```json
"AWS_ACCESS_KEY_ID": "your-access-key-from-step-2",
"AWS_SECRET_ACCESS_KEY": "your-secret-key-from-step-2",
"AWS_REGION": "us-east-1",
"AWS_S3_BUCKET_NAME": "your-bucket-name-from-step-1"
```

---

## ✅ Step 8: Test Connection

After configuring environment variables, test:

```bash
cd backend
python test_s3_connection.py
```

Expected output:
```
✅ Successfully connected to S3 bucket: your-bucket-name
✅ S3 setup complete! Ready to use.
```

---

## Quick Reference

**Your AWS Configuration:**
- Bucket Name: `_________________`
- Region: `_________________`
- Access Key ID: `_________________`
- Secret Access Key: `_________________` (stored securely)
- IAM User: `room-detection-service`
- IAM Policy: `RoomDetectionS3Access`

---

## Troubleshooting

**If connection test fails:**

1. **"Bucket not found"**:
   - Verify bucket name matches exactly
   - Check region is correct

2. **"Access denied"**:
   - Verify IAM policy is attached to user
   - Check policy JSON has correct bucket name
   - Ensure access keys are correct

3. **"Invalid credentials"**:
   - Verify access key ID and secret key are correct
   - Check environment variables are set
   - Restart terminal/IDE after setting env vars

---

## Next Steps

Once S3 is set up, we'll:
1. ✅ Test S3 upload/download (code ready)
2. Integrate with PDF processing
3. Set up Textract integration
4. Set up Rekognition integration
5. Create API endpoint

