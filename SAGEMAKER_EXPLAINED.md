# What is SageMaker Model For? (In Our Context)

## Quick Answer

**SageMaker** is AWS's machine learning platform. In our room detection project, we would use it to:

1. **Train a custom ML model** to extract wall lines from PDFs/images (if AWS pre-built services can't do it)
2. **Deploy the model** as an API endpoint for real-time inference
3. **Process documents/images** that Textract/Rekognition can't handle well

## The Problem: AWS Services Have Limitations

### What Textract Can Do:
- ✅ Extract text from PDFs/images
- ✅ Extract form fields (key-value pairs)
- ✅ Extract tables
- ❌ **Cannot extract line coordinates directly**
- ❌ Focuses on text, not geometry

### What Rekognition Can Do:
- ✅ Detect objects (furniture, doors, windows)
- ✅ Detect labels (general categories)
- ✅ OCR (text in images)
- ❌ **No built-in architectural line detection**
- ❌ Doesn't understand floorplan structure

### What We Need:
- ✅ Extract wall line segments (start/end coordinates)
- ✅ Identify architectural elements (walls vs annotations)
- ✅ Understand floorplan geometry

**Gap:** AWS pre-built services don't directly extract wall lines from blueprints.

## Solution: Custom SageMaker Model

### What SageMaker Would Do:

#### 1. **Train a Custom Model**
We would train a machine learning model to:
- **Input:** PDF or image of a floorplan
- **Output:** Wall line segments with coordinates
  ```json
  [
    {"type": "line", "start": [100, 100], "end": [500, 100]},
    {"type": "line", "start": [500, 100], "end": [500, 400]}
  ]
  ```

#### 2. **Model Training Process**
```
Training Data:
  ├─ 1000s of floorplan images/PDFs
  ├─ Manually labeled wall segments (ground truth)
  └─ Different architectural styles
     ↓
SageMaker Training:
  ├─ Use deep learning framework (TensorFlow, PyTorch)
  ├─ Train model to detect lines
  └─ Validate accuracy
     ↓
Deployed Model:
  └─ API endpoint for inference
```

#### 3. **How It Would Work in Our System**

**Current Flow (Without SageMaker):**
```
PDF → PyMuPDF → Extract vectors → Wall segments
```

**With SageMaker:**
```
PDF → S3 → SageMaker Endpoint → Wall segments
         ↓
    (Custom trained model)
```

## Specific Use Cases in Our Project

### Use Case 1: PDF Vector Extraction (Phase 2A)

**Problem:** Textract extracts text, but not wall line coordinates.

**SageMaker Solution:**
- Train model to detect wall lines in PDF vector graphics
- Input: PDF page
- Output: List of wall line segments with coordinates

**Example:**
```python
# Call SageMaker endpoint
response = sagemaker_client.invoke_endpoint(
    EndpointName='wall-line-extraction-model',
    Body=pdf_bytes
)

# Response contains wall segments
wall_segments = json.loads(response['Body'].read())
# [
#   {"start": [100, 100], "end": [500, 100]},
#   {"start": [500, 100], "end": [500, 400]}
# ]
```

### Use Case 2: Raster Image Line Detection (Phase 2B)

**Problem:** Rekognition doesn't detect architectural lines.

**SageMaker Solution:**
- Train model to detect wall lines in scanned images
- Input: Image (PNG/JPG)
- Output: List of detected wall lines

**Example:**
```python
# Call SageMaker endpoint
response = sagemaker_client.invoke_endpoint(
    EndpointName='image-line-detection-model',
    Body=image_bytes
)

# Response contains detected lines
detected_lines = json.loads(response['Body'].read())
```

### Use Case 3: Direct Room Detection (Alternative)

**Problem:** What if we want to skip line extraction and detect rooms directly?

**SageMaker Solution:**
- Train model to detect rooms directly from images
- Input: Floorplan image
- Output: Room bounding boxes

**Example:**
```python
# Call SageMaker endpoint
response = sagemaker_client.invoke_endpoint(
    EndpointName='room-detection-model',
    Body=image_bytes
)

# Response contains rooms directly
rooms = json.loads(response['Body'].read())
# [
#   {"id": "room_001", "bounding_box": [50, 50, 200, 300]},
#   {"id": "room_002", "bounding_box": [250, 50, 700, 500]}
# ]
```

## Do We Actually Need SageMaker?

### Option A: Use SageMaker (Compliant with AWS Requirement)

**Pros:**
- ✅ Complies with "AWS AI/ML Services" requirement
- ✅ Can be highly accurate if well-trained
- ✅ Handles edge cases with custom logic

**Cons:**
- ❌ Requires training data (1000s of labeled floorplans)
- ❌ Model development time (weeks/months)
- ❌ Ongoing maintenance and retraining
- ❌ Cost: ~$0.10-1.00 per inference
- ❌ Complex deployment

### Option B: Hybrid Approach (Recommended)

**Use AWS Services + Our Algorithm:**

```
PDF/Image → S3
  ↓
Textract → Extract text, forms (for room labels)
  ↓
Our Algorithm (PyMuPDF/OpenCV) → Extract wall lines
  ↓
Our Algorithm (NetworkX + Shapely) → Detect rooms
```

**Pros:**
- ✅ Uses AWS services (Textract for OCR)
- ✅ Uses our proven algorithms (fast, accurate)
- ✅ No model training needed
- ✅ Lower cost
- ✅ Faster development

**Cons:**
- ⚠️ Might not fully satisfy "must use AWS AI/ML Services" requirement
- ⚠️ Need clarification on requirement scope

### Option C: Minimal SageMaker (Compliance)

**Use SageMaker only where necessary:**

```
PDF/Image → S3
  ↓
Textract → Extract text (room labels)
  ↓
SageMaker → Extract wall lines (if Textract insufficient)
  ↓
Our Algorithm (NetworkX + Shapely) → Detect rooms
```

**Pros:**
- ✅ Complies with AWS requirement
- ✅ Uses SageMaker where needed
- ✅ Keeps our proven room detection algorithm

**Cons:**
- ❌ Still requires model training for line extraction
- ❌ More complex than Option B

## What Would SageMaker Model Actually Do?

### If We Train a Line Extraction Model:

**Input:**
- PDF page or image of floorplan

**Model Architecture (Example):**
- Convolutional Neural Network (CNN)
- Or Transformer-based model
- Trained to detect straight lines (walls)

**Output:**
- List of line segments:
  ```json
  [
    {"start": [x1, y1], "end": [x2, y2], "thickness": 2.5},
    {"start": [x2, y2], "end": [x3, y3], "thickness": 2.5}
  ]
  ```

**Training Data Needed:**
- 1000+ floorplan images
- Each manually labeled with wall line coordinates
- Various architectural styles
- Different image qualities

**Training Time:**
- Days to weeks depending on data size
- Requires GPU instances (costly)

**Deployment:**
- Deploy as SageMaker endpoint
- Can handle real-time inference
- Auto-scaling based on load

## Cost Breakdown

### SageMaker Costs:

| Component | Cost |
|-----------|------|
| **Training** | $1-5/hour (GPU instances) |
| **Endpoint** | $0.10-1.00 per 1000 inferences |
| **Storage** | $0.023/GB (model artifacts) |
| **Data Processing** | $0.10-0.50 per hour |

**Example:**
- Training: 10 hours × $3/hour = $30 (one-time)
- Inference: 1000 requests × $0.50/1000 = $0.50
- **Total per 1000 requests: ~$0.50-1.00**

## Recommendation

### For Our Use Case:

**We probably DON'T need SageMaker if:**
- ✅ We can use Textract for OCR (room labels)
- ✅ We can use PyMuPDF/OpenCV for line extraction
- ✅ Our algorithm works well (proven 100% accuracy)

**We DO need SageMaker if:**
- ❌ Requirement explicitly mandates it
- ❌ Textract/Rekognition can't extract lines
- ❌ We want to detect rooms directly (skip line extraction)

### Best Approach:

**Hybrid with Minimal SageMaker:**
1. Use **Textract** for OCR (room labels) - Phase 2C
2. Use **PyMuPDF/OpenCV** for line extraction - Phase 2A/2B
3. Use **SageMaker** only if required for compliance
4. Use **Our Algorithm** for room detection (proven, fast)

**This gives us:**
- ✅ AWS service usage (compliance)
- ✅ Proven algorithms (performance)
- ✅ Minimal complexity (development speed)

## Summary

**SageMaker Model Purpose:**
- Train custom ML model to extract wall lines from PDFs/images
- Deploy as API endpoint for real-time inference
- Handle cases where pre-built AWS services (Textract/Rekognition) can't

**Do We Need It?**
- **Probably not** if we can use PyMuPDF/OpenCV + Textract
- **Yes** if requirement mandates AWS AI/ML services for all processing
- **Maybe** for edge cases or future enhancements

**Recommendation:**
- Start with Textract + our algorithms
- Add SageMaker only if required or if pre-built services fail

