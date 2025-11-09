# PDF API Manual Testing Guide

This guide provides instructions for manually testing the new `/detect-rooms-from-pdf` endpoint.

## Prerequisites

1. ✅ AWS S3 bucket configured (`room-detection-blueprints-tony-gauntlet`)
2. ✅ AWS credentials in `.env` file
3. ✅ Backend server running
4. ✅ A PDF blueprint file to test with

---

## Step 1: Start the Backend Server

```bash
cd backend
python -m uvicorn main:app --reload --port 8000
```

You should see:
```
INFO:     Uvicorn running on http://127.0.0.1:8000
```

---

## Step 2: Test the Endpoint

### Option A: Using curl

```bash
curl -X POST "http://localhost:8000/detect-rooms-from-pdf?use_textract=false&use_rekognition=false" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@/path/to/your/blueprint.pdf"
```

**Replace `/path/to/your/blueprint.pdf` with your actual PDF file path.**

### Option B: Using Python requests

Create a test script `test_pdf_api.py`:

```python
import requests

url = "http://localhost:8000/detect-rooms-from-pdf"
files = {'file': open('path/to/your/blueprint.pdf', 'rb')}
params = {
    'use_textract': False,  # Set to True to enable Textract OCR
    'use_rekognition': False  # Set to True to enable Rekognition object detection
}

response = requests.post(url, files=files, params=params)
print(f"Status: {response.status_code}")
print(f"Response: {response.json()}")
```

Run it:
```bash
python test_pdf_api.py
```

### Option C: Using Postman or Insomnia

1. **Method**: POST
2. **URL**: `http://localhost:8000/detect-rooms-from-pdf`
3. **Query Parameters**:
   - `use_textract`: `false` (or `true` to enable)
   - `use_rekognition`: `false` (or `true` to enable)
4. **Body**: 
   - Type: `form-data`
   - Key: `file` (type: File)
   - Value: Select your PDF file
5. **Send**

---

## Step 3: Expected Response

### Success Response (200 OK)

```json
[
  {
    "id": "room_001",
    "bounding_box": [50, 50, 200, 300],
    "name_hint": "Room 1"
  },
  {
    "id": "room_002",
    "bounding_box": [250, 50, 700, 500],
    "name_hint": "Room 2"
  }
]
```

### Error Responses

**400 Bad Request** - Invalid file or processing error:
```json
{
  "detail": "No lines found in PDF. Ensure PDF contains vector graphics."
}
```

**500 Internal Server Error** - Server/configuration error:
```json
{
  "detail": "AWS_S3_BUCKET_NAME not configured"
}
```

---

## Step 4: Check Backend Logs

The backend will print progress messages:

```
📤 Uploading blueprint.pdf to S3...
✅ Uploaded to S3: pdfs/blueprint_20241109_123456.pdf
📄 Extracting lines from PDF...
✅ Extracted 45 lines from PDF
🔄 Transforming coordinates...
✅ Normalized 45 lines
🔍 Filtering wall lines...
✅ Filtered to 32 wall lines
🏗️  Converting to wall segments...
✅ Validating segments...
🔍 Detecting rooms...
✅ Detected 3 rooms
```

---

## Step 5: Verify S3 Upload

Check your S3 bucket to confirm the file was uploaded:

1. Go to AWS Console → S3
2. Navigate to your bucket: `room-detection-blueprints-tony-gauntlet`
3. Check the `pdfs/` folder
4. You should see your uploaded PDF file

---

## Step 6: Test with AWS Services (Optional)

### Enable Textract (OCR):

```bash
curl -X POST "http://localhost:8000/detect-rooms-from-pdf?use_textract=true&use_rekognition=false" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@blueprint.pdf"
```

**Note**: This requires Textract permissions. You'll see additional logs:
```
🔍 Running AWS services: ['textract']
✅ Textract completed: 12 lines detected
```

### Enable Rekognition (Object Detection):

```bash
curl -X POST "http://localhost:8000/detect-rooms-from-pdf?use_textract=false&use_rekognition=true" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@blueprint.pdf"
```

**Note**: This requires Rekognition permissions. You'll see:
```
🔍 Running AWS services: ['rekognition']
✅ Rekognition completed: 8 labels detected
```

### Enable Both:

```bash
curl -X POST "http://localhost:8000/detect-rooms-from-pdf?use_textract=true&use_rekognition=true" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@blueprint.pdf"
```

---

## Troubleshooting

### Error: "AWS_S3_BUCKET_NAME not configured"
- **Solution**: Make sure `.env` file has `AWS_S3_BUCKET_NAME=room-detection-blueprints-tony-gauntlet`

### Error: "No lines found in PDF"
- **Cause**: PDF might be a scanned image (raster) instead of vector graphics
- **Solution**: 
  - Use a PDF with vector graphics (CAD exports, not scanned images)
  - Or wait for Phase 2B (Raster image processing)

### Error: "No wall lines found after filtering"
- **Cause**: Filter parameters too strict
- **Solution**: Adjust `min_thickness`, `max_thickness`, `min_length` in the code

### Error: S3 upload fails
- **Check**: 
  - AWS credentials are correct
  - IAM user has S3 upload permissions
  - Bucket name is correct

### Error: Textract/Rekognition fails
- **Check**:
  - IAM roles are created (Step 5 in AWS setup)
  - Bucket policy allows service access (Step 6 in AWS setup)
  - File is actually in S3 (check bucket)

---

## Testing Checklist

- [ ] Backend server starts without errors
- [ ] Health check works: `curl http://localhost:8000/health`
- [ ] PDF upload succeeds
- [ ] File appears in S3 bucket
- [ ] Rooms are detected and returned
- [ ] Response format matches PRD (array of rooms)
- [ ] (Optional) Textract works when enabled
- [ ] (Optional) Rekognition works when enabled

---

## Next Steps

After successful manual testing:
1. ✅ API endpoint is working
2. Create frontend PDF upload component (Subtask 20.7)
3. Integrate with existing UI (Subtask 20.8)
4. Write comprehensive tests (Subtask 20.9)

---

## Quick Test Commands

```bash
# Health check
curl http://localhost:8000/health

# Test with a PDF (replace path)
curl -X POST "http://localhost:8000/detect-rooms-from-pdf" \
  -F "file=@tests/sample_data/simple/simple_floorplan.pdf" 2>/dev/null || \
  echo "Note: PDF file needed. Use a real blueprint PDF."

# Check S3 connection
cd backend && python test_s3_connection.py
```

