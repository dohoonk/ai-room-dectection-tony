# High-Level Architecture Changes: Option 1 (AWS AI/ML Services)

## Current Architecture (MVP)

```
User → React Frontend
  ↓ (uploads JSON)
FastAPI Backend
  ↓
Our Algorithms:
  - parse_line_segments() → WallSegment[]
  - build_wall_graph() → NetworkX Graph
  - find_faces_using_polygonize() → Faces
  - filter_cycles() → Valid Rooms
  - polygon_to_bounding_box() → Rooms
  ↓
Return JSON: Room[]
```

## Proposed Architecture (Option 1: AWS AI/ML Services)

```
User → React Frontend
  ↓ (uploads PDF/Image)
FastAPI Backend
  ↓
AWS Services Layer:
  ├─ Textract (PDF/Image → Text, Forms, Tables)
  ├─ Rekognition (Image → Lines, Shapes, Objects)
  └─ SageMaker (Custom ML Model for Room Detection)
  ↓
Post-Processing:
  - Convert AWS responses → WallSegment[]
  - Use our algorithm OR SageMaker model
  ↓
Return JSON: Room[]
```

## High-Level Code Changes Required

### 1. **Backend API Layer Changes**

#### Current (`backend/main.py`):
```python
@app.post("/detect-rooms")
async def detect_rooms_endpoint(request: RoomDetectionRequest):
    # Direct processing with our algorithm
    rooms = detect_rooms(temp_path, tolerance=1.0)
    return rooms
```

#### With AWS Services:
```python
@app.post("/detect-rooms-from-pdf")
async def detect_rooms_from_pdf(file: UploadFile):
    # 1. Upload to S3
    s3_key = upload_to_s3(file)
    
    # 2. Call AWS services (async)
    textract_job = start_textract_job(s3_key)
    rekognition_job = start_rekognition_job(s3_key)
    
    # 3. Poll for completion
    textract_result = await poll_textract_job(textract_job)
    rekognition_result = await poll_rekognition_job(rekognition_job)
    
    # 4. Process AWS responses → wall segments
    wall_segments = process_aws_responses(textract_result, rekognition_result)
    
    # 5. Use our algorithm OR SageMaker
    rooms = detect_rooms_from_segments(wall_segments)
    return rooms
```

**Changes:**
- ✅ Add AWS SDK (`boto3`) dependency
- ✅ Add file upload handling (multipart/form-data)
- ✅ Add S3 integration for file storage
- ✅ Add async job polling logic
- ✅ Add AWS response processing layer

---

### 2. **New AWS Service Integration Module**

#### New File: `backend/src/aws_services.py`

```python
import boto3
from typing import Dict, List, Any

class AWSServiceClient:
    """Wrapper for AWS AI/ML services."""
    
    def __init__(self):
        self.textract = boto3.client('textract')
        self.rekognition = boto3.client('rekognition')
        self.s3 = boto3.client('s3')
        self.sagemaker = boto3.client('sagemaker-runtime')
    
    def extract_from_pdf(self, s3_bucket: str, s3_key: str) -> Dict:
        """Use Textract to extract text and forms from PDF."""
        response = self.textract.start_document_analysis(
            DocumentLocation={'S3Object': {'Bucket': s3_bucket, 'Name': s3_key}},
            FeatureTypes=['FORMS', 'TABLES']
        )
        return response
    
    def detect_lines_in_image(self, s3_bucket: str, s3_key: str) -> Dict:
        """Use Rekognition to detect lines/shapes in image."""
        # Note: Rekognition doesn't directly detect architectural lines
        # We might need custom SageMaker model
        response = self.rekognition.detect_labels(
            Image={'S3Object': {'Bucket': s3_bucket, 'Name': s3_key}}
        )
        return response
    
    def predict_rooms_sagemaker(self, wall_segments: List) -> List:
        """Use SageMaker endpoint to predict rooms."""
        # Custom trained model for room detection
        response = self.sagemaker.invoke_endpoint(
            EndpointName='room-detection-model',
            Body=json.dumps(wall_segments)
        )
        return json.loads(response['Body'].read())
```

**Changes:**
- ✅ New module for AWS service integration
- ✅ AWS credentials configuration
- ✅ Error handling for AWS service failures
- ✅ Retry logic for transient failures

---

### 3. **Response Processing Layer**

#### New File: `backend/src/aws_response_processor.py`

```python
def process_textract_response(textract_result: Dict) -> List[WallSegment]:
    """
    Convert Textract response to wall segments.
    
    Textract extracts:
    - Text blocks (room labels)
    - Forms (key-value pairs)
    - Tables (structured data)
    
    Challenge: Textract doesn't extract line coordinates directly.
    We'd need to parse form fields or tables that contain coordinates.
    """
    wall_segments = []
    
    # Parse Textract blocks for coordinate data
    for block in textract_result.get('Blocks', []):
        if block['BlockType'] == 'LINE':
            # Extract line coordinates if available
            # This is a challenge - Textract focuses on text, not geometry
            pass
    
    return wall_segments

def process_rekognition_response(rekognition_result: Dict) -> List[WallSegment]:
    """
    Convert Rekognition response to wall segments.
    
    Rekognition detects:
    - Objects (furniture, doors, windows)
    - Labels (general categories)
    - Text (OCR)
    
    Challenge: Rekognition doesn't detect architectural lines directly.
    We'd need a custom model or use DetectCustomLabels.
    """
    wall_segments = []
    
    # Rekognition doesn't provide line detection out-of-the-box
    # Would need custom model training
    
    return wall_segments
```

**Changes:**
- ✅ New module to convert AWS responses to our format
- ✅ Complex parsing logic (AWS responses are different from our format)
- ✅ Handling missing/incomplete data from AWS services

---

### 4. **Algorithm Changes**

#### Current: `backend/src/room_detector.py`
- Uses our proven algorithm (NetworkX + Shapely)
- Direct processing of wall segments

#### With AWS Services - Two Options:

**Option A: Hybrid (Recommended)**
```python
def detect_rooms_with_aws(aws_responses: Dict) -> List[Dict]:
    # 1. Process AWS responses → wall segments
    wall_segments = process_aws_responses(aws_responses)
    
    # 2. Use our existing algorithm
    rooms = detect_rooms_from_segments(wall_segments)
    
    return rooms
```

**Option B: Full AWS (SageMaker)**
```python
def detect_rooms_with_sagemaker(wall_segments: List) -> List[Dict]:
    # Train custom SageMaker model
    # Deploy endpoint
    # Call endpoint for predictions
    
    response = sagemaker_client.invoke_endpoint(
        EndpointName='room-detection-model',
        Body=json.dumps(wall_segments)
    )
    
    return json.loads(response['Body'].read())
```

**Changes:**
- ✅ Option A: Minimal changes (just add AWS response processing)
- ✅ Option B: Requires SageMaker model training, deployment, maintenance

---

### 5. **Frontend Changes**

#### Current: `frontend/src/components/FileUpload.tsx`
- Accepts JSON files only

#### With AWS Services:
```typescript
// Accept PDF and image files
const acceptedTypes = ['application/pdf', 'image/png', 'image/jpeg', 'image/jpg'];

// Handle async processing
const handleFileUpload = async (file: File) => {
  setLoading(true);
  
  // Upload to backend
  const formData = new FormData();
  formData.append('file', file);
  
  // Backend starts async job
  const response = await fetch('/detect-rooms-from-pdf', {
    method: 'POST',
    body: formData
  });
  
  // Poll for results (AWS services are async)
  const jobId = response.json().job_id;
  const rooms = await pollForResults(jobId);
  
  setRooms(rooms);
  setLoading(false);
};
```

**Changes:**
- ✅ Accept PDF/image files (not just JSON)
- ✅ Add async job polling UI
- ✅ Show processing status (AWS jobs take time)
- ✅ Handle longer processing times (30+ seconds)

---

### 6. **Infrastructure Changes**

#### Current:
- Local FastAPI server
- No cloud dependencies

#### With AWS Services:
```yaml
# New dependencies
- boto3 (AWS SDK)
- AWS credentials (IAM roles, access keys)
- S3 bucket for file storage
- Textract service access
- Rekognition service access
- SageMaker (if using custom model)

# New environment variables
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
AWS_REGION=us-east-1
S3_BUCKET_NAME=room-detection-input
TEXTRACT_ROLE_ARN=...
SAGEMAKER_ENDPOINT_NAME=...
```

**Changes:**
- ✅ AWS account setup
- ✅ IAM roles and policies
- ✅ S3 bucket configuration
- ✅ Service quotas and limits
- ✅ Cost monitoring

---

## Key Challenges with Option 1

### 1. **AWS Services Limitations**

**Textract:**
- ✅ Good for: Text extraction, form fields, tables
- ❌ **Cannot extract line coordinates directly**
- ❌ Focuses on text, not geometry

**Rekognition:**
- ✅ Good for: Object detection, labels, faces
- ❌ **No built-in line/edge detection for architectural drawings**
- ❌ Would need custom model training

**SageMaker:**
- ✅ Good for: Custom ML models
- ❌ Requires training data and model development
- ❌ Ongoing maintenance and costs

### 2. **Data Format Mismatch**

**Our Algorithm Needs:**
```json
[
  {"type": "line", "start": [100, 100], "end": [500, 100]}
]
```

**AWS Services Return:**
- Textract: Text blocks, form fields, tables (no coordinates)
- Rekognition: Labels, bounding boxes (not line segments)
- SageMaker: Whatever we train it to return

**Gap:** We'd need significant post-processing to convert AWS responses to our format.

### 3. **Async Processing Complexity**

**Current:** Synchronous, fast (< 1 second)

**With AWS:**
- Textract jobs: 5-30 seconds
- Rekognition: 1-5 seconds
- SageMaker: Variable
- **Total:** 10-60 seconds (vs our < 1 second)

**Impact:**
- Need job queue system
- Need polling mechanism
- Need status tracking
- User experience degradation

### 4. **Cost Implications**

**Current:** Free (local processing)

**With AWS (per 1000 requests):**
- Textract: ~$15-50 (depends on pages)
- Rekognition: ~$1-5 (depends on resolution)
- SageMaker: ~$0.10-1.00 per inference
- S3 storage: ~$0.023 per GB
- **Total:** ~$16-56 per 1000 requests

**At scale:** Could be expensive

---

## Recommended Approach: Hybrid (Best of Both)

### Use AWS Services Where They Excel:
1. **Textract** → Extract room labels/text (Phase 2C: OCR)
2. **S3** → File storage
3. **Our Algorithm** → Core room detection (proven, fast, accurate)

### Keep Our Algorithm For:
1. **PDF Vector Extraction** → PyMuPDF (more control, faster)
2. **Raster Image Processing** → OpenCV (more control, faster)
3. **Room Detection** → NetworkX + Shapely (proven, accurate)

### Architecture:
```
User → React Frontend
  ↓ (uploads PDF/Image)
FastAPI Backend
  ↓
Our Algorithms (PyMuPDF/OpenCV):
  - Extract wall segments
  ↓
Our Algorithm (NetworkX + Shapely):
  - Detect rooms
  ↓
AWS Textract (Optional):
  - Extract room labels for name_hint
  ↓
Return JSON: Room[]
```

**Benefits:**
- ✅ Faster processing (< 1 second vs 10-60 seconds)
- ✅ Lower costs (no AWS service fees for core processing)
- ✅ More control over algorithm
- ✅ Better accuracy (our algorithm is proven)
- ✅ Use AWS where it adds value (Textract for OCR)

---

## Summary: What Would Change with Option 1

### Code Changes:
1. ✅ Add `boto3` SDK integration
2. ✅ Add AWS service client wrapper
3. ✅ Add AWS response processing layer
4. ✅ Add async job polling logic
5. ✅ Add S3 file upload handling
6. ✅ Modify frontend for async processing
7. ✅ Add error handling for AWS failures

### Infrastructure Changes:
1. ✅ AWS account and credentials
2. ✅ S3 bucket setup
3. ✅ IAM roles and policies
4. ✅ Service quotas configuration
5. ✅ Cost monitoring setup

### Algorithm Changes:
- **Option A (Hybrid):** Minimal - just add AWS response processing
- **Option B (Full AWS):** Major - train and deploy SageMaker model

### Performance Impact:
- ⚠️ Slower: 10-60 seconds vs < 1 second
- ⚠️ More complex: Async job handling
- ⚠️ Higher costs: AWS service fees

### Recommendation:
**Use Hybrid Approach** - Keep our algorithms, add AWS Textract only for OCR (Phase 2C).

